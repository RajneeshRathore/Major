import { useState, useEffect } from "react";
import {
    ChevronRight,
    ChevronDown,
    Folder,
    FileCode2,
    MessageSquare,
    Terminal,
    Settings,
    Play,
    Loader2,
    Clock
} from "lucide-react";
import Editor from "@monaco-editor/react";
import Chat from "../chat/Chat";
import { fetchProjectFiles, fetchFileContent, fetchProjects, retryProject, type ProjectInfo } from "../../api";

// -------------------------------------------------------------
// TYPES
// -------------------------------------------------------------

type TreeNode = {
    name: string;
    path: string;
    isDirectory: boolean;
    children: Record<string, TreeNode>;
};

function buildFileTree(files: string[]): TreeNode {
    const root: TreeNode = { name: "root", path: "", isDirectory: true, children: {} };
    for (const file of files) {
        const parts = file.split(/[/\\]/);
        let current = root;
        for (let i = 0; i < parts.length; i++) {
            const part = parts[i];
            if (!current.children[part]) {
                const isDir = i < parts.length - 1;
                current.children[part] = {
                    name: part,
                    path: parts.slice(0, i + 1).join("/"),
                    isDirectory: isDir,
                    children: {}
                };
            }
            current = current.children[part];
        }
    }
    return root;
}

const FileTreeNode = ({ node, level, onOpenFile, activeFile }: { node: TreeNode, level: number, onOpenFile: (path: string) => void, activeFile: string | null }) => {
    const [isOpen, setIsOpen] = useState(true);
    
    const children = Object.values(node.children).sort((a, b) => {
        if (a.isDirectory === b.isDirectory) return a.name.localeCompare(b.name);
        return a.isDirectory ? -1 : 1;
    });

    return (
        <div className="w-full">
            {node.name !== "root" && (
                <button
                    onClick={() => node.isDirectory ? setIsOpen(!isOpen) : onOpenFile(node.path)}
                    style={{ paddingLeft: `${level * 12 + 8}px` }}
                    className={`flex w-full items-center gap-1.5 py-1 text-left text-[13px] transition ${
                        !node.isDirectory && activeFile === node.path 
                            ? 'bg-violet-500/10 text-violet-300' 
                            : 'text-zinc-400 hover:bg-white/[0.04] hover:text-zinc-200'
                    }`}
                >
                    {node.isDirectory ? (
                        <>
                            {isOpen ? <ChevronDown className="h-3.5 w-3.5 shrink-0" /> : <ChevronRight className="h-3.5 w-3.5 shrink-0" />}
                            <Folder className="h-3.5 w-3.5 shrink-0 text-zinc-500" />
                        </>
                    ) : (
                        <>
                            <div className="w-3.5 shrink-0" />
                            <FileCode2 className="h-3.5 w-3.5 shrink-0 text-zinc-500" />
                        </>
                    )}
                    <span className="truncate">{node.name}</span>
                </button>
            )}
            {isOpen && children.map(child => (
                <FileTreeNode 
                    key={child.path} 
                    node={child} 
                    level={node.name === "root" ? 0 : level + 1} 
                    onOpenFile={onOpenFile} 
                    activeFile={activeFile} 
                />
            ))}
        </div>
    );
};

interface IDEProps {
    projectId?: string; // If provided, load this project
}

// -------------------------------------------------------------
// COMPONENTS
// -------------------------------------------------------------

export default function IDE({ projectId: initialProjectId }: IDEProps) {
    const [activeTab, setActiveTab] = useState<"files" | "chat" | "projects" | "terminal">("projects");
    const [projectId, setProjectId] = useState<string | null>(initialProjectId || null);
    const [files, setFiles] = useState<string[]>([]);
    const [projects, setProjects] = useState<ProjectInfo[]>([]);
    const [loadingProjects, setLoadingProjects] = useState(false);
    
    // Editor state
    const [openFiles, setOpenFiles] = useState<{path: string, content: string}[]>([]);
    const [activeFile, setActiveFile] = useState<string | null>(null);
    const [liveStream, setLiveStream] = useState<string>("");
    const [projectStatus, setProjectStatus] = useState<string>("");

    // Fetch past projects on mount
    useEffect(() => {
        loadProjects();
    }, []);

    const loadProjects = async () => {
        setLoadingProjects(true);
        try {
            const data = await fetchProjects();
            setProjects(data);
        } catch (error) {
            console.error("Failed to fetch past projects:", error);
        } finally {
            setLoadingProjects(false);
        }
    };

    // Refresh files when projectId changes and poll for updates
    useEffect(() => {
        if (!projectId) return;

        let interval: any;

        const checkAndLoad = async () => {
            loadFiles();
            try {
                const res = await fetch(`/api/projects/${projectId}/status`);
                if (res.ok) {
                    const data = await res.json();
                    setProjectStatus(data.status);
                    if (data.status === "COMPLETED" || data.status === "FAILED") {
                        if (interval) clearInterval(interval);
                    }
                }
            } catch (e) {
                // ignore
            }
        };

        checkAndLoad();
        interval = setInterval(checkAndLoad, 3000);
        
        const es = new EventSource(`/api/projects/${projectId}/stream`);
        es.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.chunk) {
                    setLiveStream(prev => prev + data.chunk);
                }
            } catch (e) {}
        };
        es.onerror = () => {
            es.close();
        };

        return () => {
            if (interval) clearInterval(interval);
            es.close();
            setLiveStream("");
        };
    }, [projectId]);

    const loadFiles = async () => {
        if (!projectId) return;
        try {
            const projectFiles = await fetchProjectFiles(projectId);
            setFiles(projectFiles);
        } catch (error) {
            console.error("Failed to fetch project files:", error);
        }
    };

    const handleOpenFile = async (path: string) => {
        if (!projectId) return;

        // Check if already open
        if (!openFiles.find(f => f.path === path)) {
            try {
                const content = await fetchFileContent(projectId, path);
                setOpenFiles(prev => [...prev, { path, content }]);
            } catch (error) {
                console.error("Failed to read file:", error);
                return;
            }
        }
        setActiveFile(path);
    };

    const closeFile = (path: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setOpenFiles(prev => prev.filter(f => f.path !== path));
        if (activeFile === path) {
            const remaining = openFiles.filter(f => f.path !== path);
            setActiveFile(remaining.length > 0 ? remaining[remaining.length - 1].path : null);
        }
    };

    // Derived state
    const activeFileContent = openFiles.find(f => f.path === activeFile)?.content || "";

    const getLanguage = (filename: string) => {
        if (filename.endsWith('.py')) return 'python';
        if (filename.endsWith('.js')) return 'javascript';
        if (filename.endsWith('.ts') || filename.endsWith('.tsx')) return 'typescript';
        if (filename.endsWith('.json')) return 'json';
        if (filename.endsWith('.html')) return 'html';
        if (filename.endsWith('.css')) return 'css';
        if (filename.endsWith('.md')) return 'markdown';
        return 'plaintext';
    };

    return (
        <div className="flex h-screen w-full flex-col overflow-hidden bg-[#0d0f14] text-zinc-300 font-sans">
            
            {/* --- TOP BAR --- */}
            <div className="flex h-12 shrink-0 items-center justify-between border-b border-white/[0.05] bg-[#0a0c10] px-4">
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <div className="h-6 w-6 rounded bg-violet-600 flex items-center justify-center">
                            <span className="text-white font-bold text-xs">DA</span>
                        </div>
                        <span className="text-sm font-semibold text-zinc-200">DevAgent IDE</span>
                    </div>
                    {projectId && (
                        <div className="rounded-md bg-white/[0.03] px-2 py-1 text-[11px] text-zinc-400 border border-white/[0.05]">
                            Project: {projectId}
                        </div>
                    )}
                </div>

                <div className="flex items-center gap-2">
                    <button className="flex items-center gap-2 rounded-md bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-400 transition hover:bg-emerald-500/20">
                        <Play className="h-3 w-3" />
                        Run App
                    </button>
                </div>
            </div>

            {/* --- MAIN WORKSPACE --- */}
            <div className="flex flex-1 overflow-hidden">
                
                {/* ACTIVITY BAR (Far Left) */}
                <div className="flex w-12 shrink-0 flex-col items-center border-r border-white/[0.05] bg-[#0a0c10] py-4">
                    <button 
                        onClick={() => setActiveTab("projects")}
                        className={`mb-4 rounded-xl p-2.5 transition ${activeTab === 'projects' ? 'bg-violet-500/20 text-violet-400' : 'text-zinc-500 hover:bg-white/[0.05] hover:text-zinc-300'}`}
                    >
                        <Clock className="h-5 w-5" />
                    </button>
                    <button 
                        onClick={() => setActiveTab("chat")}
                        className={`mb-4 rounded-xl p-2.5 transition ${activeTab === 'chat' ? 'bg-violet-500/20 text-violet-400' : 'text-zinc-500 hover:bg-white/[0.05] hover:text-zinc-300'}`}
                    >
                        <MessageSquare className="h-5 w-5" />
                    </button>
                    <button 
                        onClick={() => setActiveTab("files")}
                        className={`mb-4 rounded-xl p-2.5 transition ${activeTab === 'files' ? 'bg-violet-500/20 text-violet-400' : 'text-zinc-500 hover:bg-white/[0.05] hover:text-zinc-300'}`}
                    >
                        <Folder className="h-5 w-5" />
                    </button>
                    <button 
                        onClick={() => setActiveTab("terminal")}
                        className={`mb-4 rounded-xl p-2.5 transition ${activeTab === 'terminal' ? 'bg-violet-500/20 text-violet-400' : 'text-zinc-500 hover:bg-white/[0.05] hover:text-zinc-300'}`}
                    >
                        <Terminal className="h-5 w-5" />
                    </button>

                    <div className="mt-auto">
                        <button className="rounded-xl p-2.5 text-zinc-500 transition hover:bg-white/[0.05] hover:text-zinc-300">
                            <Settings className="h-5 w-5" />
                        </button>
                    </div>
                </div>

                {/* SIDEBAR */}
                {(activeTab === "files" || activeTab === "chat" || activeTab === "projects") && (
                    <div className="flex w-[340px] shrink-0 flex-col border-r border-white/[0.05] bg-[#0a0c10]/50 backdrop-blur">
                        
                        {/* PROJECTS EXPLORER */}
                        <div className={`flex h-full flex-col ${activeTab === "projects" ? "flex" : "hidden"}`}>
                            <div className="flex h-10 items-center px-4 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
                                Recent Projects
                            </div>
                            <div className="flex-1 overflow-y-auto px-2 pb-4">
                                {loadingProjects ? (
                                    <div className="flex justify-center p-4">
                                        <Loader2 className="h-4 w-4 animate-spin text-violet-500" />
                                    </div>
                                ) : projects.length === 0 ? (
                                    <div className="p-4 text-center text-xs text-zinc-500">
                                        No past projects found.
                                    </div>
                                ) : (
                                    <div className="space-y-[2px]">
                                        {projects.map(project => (
                                            <button
                                                key={project.id}
                                                onClick={() => {
                                                    setProjectId(project.id);
                                                    setActiveTab("files");
                                                }}
                                                className={`flex w-full flex-col gap-1 rounded-md px-3 py-2 text-left transition ${projectId === project.id ? 'bg-violet-500/10' : 'hover:bg-white/[0.04]'}`}
                                            >
                                                <div className={`text-[13px] font-medium ${projectId === project.id ? 'text-violet-300' : 'text-zinc-200'}`}>
                                                    {project.name}
                                                </div>
                                                <div className="flex justify-between items-center w-full mt-1">
                                                    <span className="text-[10px] text-zinc-500">
                                                        {new Date(project.created_at).toLocaleDateString()}
                                                    </span>
                                                    <div className="flex items-center gap-2">
                                                        {project.status === 'FAILED' && (
                                                            <button 
                                                                onClick={async (e) => {
                                                                    e.stopPropagation();
                                                                    try {
                                                                        await retryProject(project.id);
                                                                        setProjectId(project.id); // set as active
                                                                        loadProjects(); // refresh projects list
                                                                    } catch (err) {
                                                                        console.error(err);
                                                                    }
                                                                }}
                                                                className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-violet-500/10 text-violet-400 hover:bg-violet-500/20"
                                                            >
                                                                Retry
                                                            </button>
                                                        )}
                                                        <span className={`text-[9px] uppercase px-1.5 py-0.5 rounded ${
                                                            project.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-400' : 
                                                            project.status === 'FAILED' ? 'bg-red-500/10 text-red-400' : 
                                                            'bg-zinc-500/10 text-zinc-400'
                                                        }`}>
                                                            {project.status}
                                                        </span>
                                                    </div>
                                                </div>
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* FILE EXPLORER */}
                        <div className={`flex h-full flex-col ${activeTab === "files" ? "flex" : "hidden"}`}>
                            <div className="flex h-10 items-center px-4 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
                                Explorer
                            </div>
                            <div className="flex-1 overflow-y-auto px-2 pb-4">
                                {!projectId ? (
                                    <div className="p-4 text-center text-xs text-zinc-500">
                                        No project active. Use the chat to generate one.
                                    </div>
                                ) : files.length === 0 ? (
                                    <div className="p-4 text-center text-xs text-zinc-500">
                                        No files generated yet.
                                    </div>
                                ) : (
                                    <div className="flex-1 overflow-y-auto pb-4">
                                        <FileTreeNode 
                                            node={buildFileTree(files)} 
                                            level={0} 
                                            onOpenFile={handleOpenFile} 
                                            activeFile={activeFile} 
                                        />
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* CHAT INTEGRATION */}
                        <div className={`flex h-full flex-col ${activeTab === "chat" ? "flex" : "hidden"}`}>
                            <div className="flex h-10 items-center px-4 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
                                AI Agent
                            </div>
                            <div className="flex-1 overflow-hidden relative">
                                {/* We pass a callback to the chat so the IDE knows when a project is generated */}
                                <Chat embedded onProjectCreated={(id) => {
                                    setProjectId(id);
                                    loadProjects(); // Refresh the list
                                    // Auto-switch to files tab to show what was generated
                                    setTimeout(() => setActiveTab("files"), 1500);
                                }} />
                            </div>
                        </div>
                    </div>
                )}

                {/* EDITOR AREA */}
                <div className="flex flex-1 flex-col bg-[#0d0f14]">
                    {(projectStatus === "CODING" || projectStatus === "STARTED") && liveStream ? (
                        <>
                            <div className="flex h-10 items-center px-4 border-b border-white/[0.05] bg-[#0a0c10] text-[13px] text-emerald-400">
                                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                AI Agent is currently writing code...
                            </div>
                            <div className="flex-1 relative">
                                <Editor
                                    height="100%"
                                    language="python"
                                    theme="vs-dark"
                                    value={liveStream}
                                    options={{
                                        readOnly: true,
                                        minimap: { enabled: false },
                                        fontSize: 14,
                                        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                                        padding: { top: 16 },
                                        scrollBeyondLastLine: false,
                                        wordWrap: "on",
                                        smoothScrolling: true
                                    }}
                                />
                            </div>
                        </>
                    ) : openFiles.length > 0 ? (
                        <>
                            {/* Editor Tabs */}
                            <div className="flex h-10 shrink-0 overflow-x-auto border-b border-white/[0.05] bg-[#0a0c10] custom-scrollbar">
                                {openFiles.map(file => (
                                    <button
                                        key={file.path}
                                        onClick={() => setActiveFile(file.path)}
                                        className={`group flex min-w-[120px] max-w-[200px] items-center gap-2 border-r border-white/[0.05] px-4 text-[13px] transition ${activeFile === file.path ? 'bg-[#0d0f14] text-violet-300' : 'text-zinc-500 hover:bg-white/[0.02] hover:text-zinc-300'}`}
                                    >
                                        <FileCode2 className="h-3.5 w-3.5 shrink-0" />
                                        <span className="truncate">{file.path.split('/').pop()}</span>
                                        <div 
                                            onClick={(e) => closeFile(file.path, e)}
                                            className="ml-auto flex h-5 w-5 items-center justify-center rounded-md opacity-0 transition group-hover:opacity-100 hover:bg-white/10"
                                        >
                                            ×
                                        </div>
                                    </button>
                                ))}
                            </div>
                            
                            {/* Monaco Editor */}
                            <div className="flex-1 relative">
                                {activeFile ? (
                                    <Editor
                                        height="100%"
                                        language={getLanguage(activeFile)}
                                        theme="vs-dark"
                                        value={activeFileContent}
                                        options={{
                                            minimap: { enabled: false },
                                            fontSize: 14,
                                            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                                            padding: { top: 16 },
                                            scrollBeyondLastLine: false,
                                            smoothScrolling: true,
                                            cursorBlinking: "smooth",
                                            cursorSmoothCaretAnimation: "on",
                                            formatOnPaste: true,
                                        }}
                                        loading={
                                            <div className="flex h-full items-center justify-center">
                                                <Loader2 className="h-6 w-6 animate-spin text-violet-500" />
                                            </div>
                                        }
                                    />
                                ) : (
                                    <div className="flex h-full items-center justify-center text-zinc-600">
                                        Select a file to view its code
                                    </div>
                                )}
                            </div>
                        </>
                    ) : (
                        <div className="flex h-full flex-col items-center justify-center text-zinc-500">
                            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl border border-white/[0.05] bg-white/[0.02]">
                                <FileCode2 className="h-8 w-8 text-zinc-600" />
                            </div>
                            <h3 className="text-sm font-medium text-zinc-300">No file is open</h3>
                            <p className="mt-1 text-xs">Generate a project with the AI or open a file from the explorer.</p>
                        </div>
                    )}
                </div>

            </div>
        </div>
    );
}
