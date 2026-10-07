import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Editor from "@monaco-editor/react";
import {
    ArrowUp,
    Bot,
    FileCode2,
    FolderOpen,
    Loader2,
    Paperclip,
    Sparkles,
    Terminal,
    WandSparkles,
    CheckCircle2,
    XCircle,
    ChevronDown,
    ChevronRight,
    Copy,
    Check,
    User,
    CheckCircle
} from "lucide-react";
import {
    generateProject,
    fetchProjectFiles,
    fetchFileContent,
    approveProjectPlan,
    type GenerateResponse,
} from "../../api";

// ... existing code ... (types, prompts, bg, header, etc)
// I will just replace from line 1 to 26 and then the main component and AgentThinking.
// Wait, I can't use replace_file_content like this without breaking the middle. I should be specific.

/* =========================================================
   TYPES
========================================================= */

interface Message {
    id: string;
    role: "user" | "agent";
    content: string;
    timestamp: Date;
    data?: GenerateResponse;
}

/* =========================================================
   SUGGESTED PROMPTS
========================================================= */

const suggestedPrompts = [
    {
        icon: WandSparkles,
        title: "Build a feature",
        description: "Create a complete feature from a description",
        prompt:
            "Build a REST API for a student management system using Flask and SQLite. It should support creating, reading, updating and deleting students.",
    },
    {
        icon: FileCode2,
        title: "Build a CLI tool",
        description: "Create a command-line utility with Python",
        prompt:
            "Build a Python CLI tool that converts CSV files to JSON format. It should accept input and output file paths as arguments.",
    },
    {
        icon: Terminal,
        title: "Build a calculator",
        description: "Create a simple calculator application",
        prompt:
            "Build a Python calculator application that supports add, subtract, multiply, and divide operations with a clean interface.",
    },
    {
        icon: FolderOpen,
        title: "Build a web scraper",
        description: "Create a web scraper with Python",
        prompt:
            "Build a Python web scraper that extracts article titles and links from a news website and saves them to a JSON file.",
    },
];

/* =========================================================
   BACKGROUND
========================================================= */

function ChatBackground() {
    return (
        <div className="pointer-events-none fixed inset-0 overflow-hidden">
            <div className="absolute left-1/2 top-[-300px] h-[600px] w-[900px] -translate-x-1/2 rounded-full bg-violet-600/10 blur-[150px]" />
            <div className="absolute left-[-250px] top-[45%] h-[450px] w-[450px] rounded-full bg-blue-600/5 blur-[130px]" />
            <div className="absolute bottom-[-250px] right-[-150px] h-[500px] w-[500px] rounded-full bg-purple-600/5 blur-[130px]" />
            <div
                className="absolute inset-0 opacity-[0.025]"
                style={{
                    backgroundImage:
                        "linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)",
                    backgroundSize: "40px 40px",
                }}
            />
        </div>
    );
}

/* =========================================================
   HEADER
========================================================= */

function ChatHeader() {
    return (
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-white/[0.06] px-6">
            <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/10 bg-white/[0.05]">
                    <Sparkles className="h-4 w-4 text-violet-300" />
                </div>
                <div>
                    <h1 className="text-sm font-semibold text-zinc-200">
                        DevAgent
                    </h1>
                    <p className="text-[10px] text-zinc-600">
                        Multi-Agent AI IDE
                    </p>
                </div>
            </div>

            <div className="flex items-center gap-2 rounded-lg border border-white/[0.07] bg-white/[0.03] px-3 py-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                <span className="text-[11px] text-zinc-400">
                    Ollama · qwen2.5:3b
                </span>
            </div>
        </header>
    );
}

/* =========================================================
   WELCOME
========================================================= */

function ChatWelcome() {
    return (
        <section className="mx-auto flex max-w-3xl flex-col items-center px-6 pt-20 text-center">
            <div className="relative mb-7">
                <div className="absolute inset-0 rounded-2xl bg-violet-500/20 blur-2xl" />
                <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl border border-violet-400/20 bg-white/[0.05] shadow-2xl shadow-violet-500/10">
                    <Bot className="h-7 w-7 text-violet-300" />
                </div>
            </div>

            <h2 className="text-3xl font-semibold tracking-[-0.03em] text-white sm:text-4xl">
                What are you building?
            </h2>

            <p className="mt-4 max-w-xl text-sm leading-7 text-zinc-500">
                Describe what you want to build. DevAgent will plan, code,
                set up the environment, run tests, and review — all
                automatically through its multi-agent pipeline.
            </p>
        </section>
    );
}

/* =========================================================
   SUGGESTIONS
========================================================= */

function ChatSuggestions({
    onSelect,
}: {
    onSelect: (prompt: string) => void;
}) {
    return (
        <section className="mx-auto mt-12 grid max-w-3xl gap-3 px-6 sm:grid-cols-2">
            {suggestedPrompts.map((prompt) => {
                const Icon = prompt.icon;
                return (
                    <button
                        key={prompt.title}
                        type="button"
                        onClick={() => onSelect(prompt.prompt)}
                        className="group relative overflow-hidden rounded-2xl border border-white/[0.08] bg-white/[0.025] p-4 text-left transition duration-300 hover:-translate-y-0.5 hover:border-white/[0.14] hover:bg-white/[0.045]"
                    >
                        <div className="absolute right-0 top-0 h-20 w-20 translate-x-8 -translate-y-8 rounded-full bg-violet-500/10 blur-2xl transition group-hover:bg-violet-500/20" />
                        <div className="relative flex gap-3">
                            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-white/10 bg-white/[0.04]">
                                <Icon className="h-4 w-4 text-violet-300" />
                            </div>
                            <div>
                                <h3 className="text-xs font-medium text-zinc-200">
                                    {prompt.title}
                                </h3>
                                <p className="mt-1 text-[11px] leading-5 text-zinc-600">
                                    {prompt.description}
                                </p>
                            </div>
                        </div>
                    </button>
                );
            })}
        </section>
    );
}

/* =========================================================
   CODE BLOCK WITH COPY
========================================================= */

function CodeBlock({ code, filename }: { code: string; filename: string }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(code);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="mt-3 overflow-hidden rounded-xl border border-white/[0.08] bg-[#0a0c10] transition-all hover:border-violet-500/30">
            <div className="flex items-center justify-between border-b border-white/[0.06] bg-[#0d0f14] px-4 py-2">
                <span className="text-[11px] font-medium text-zinc-400">
                    {filename}
                </span>
                <button
                    type="button"
                    onClick={handleCopy}
                    className="flex items-center gap-1.5 text-[11px] text-zinc-500 transition hover:text-zinc-200"
                >
                    {copied ? (
                        <Check className="h-3 w-3 text-emerald-400" />
                    ) : (
                        <Copy className="h-3 w-3" />
                    )}
                    {copied ? "Copied" : "Copy"}
                </button>
            </div>
            <div className="h-[300px] w-full pt-2 bg-[#0a0c10]">
                <Editor
                    height="100%"
                    language={filename.split('.').pop() === 'py' ? 'python' : filename.split('.').pop() === 'ts' || filename.split('.').pop() === 'tsx' ? 'typescript' : 'javascript'}
                    theme="vs-dark"
                    value={code}
                    options={{
                        readOnly: true,
                        minimap: { enabled: false },
                        scrollBeyondLastLine: false,
                        fontSize: 12,
                        lineHeight: 20,
                        padding: { top: 8, bottom: 8 },
                        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                    }}
                />
            </div>
        </div>
    );
}

/* =========================================================
   AGENT RESPONSE CARD
========================================================= */

function AgentResponseCard({ data }: { data: GenerateResponse }) {
    const [expandedFiles, setExpandedFiles] = useState<Set<string>>(
        new Set()
    );
    const [fileContents, setFileContents] = useState<Record<string, string>>(
        {}
    );
    const [loadingFile, setLoadingFile] = useState<string | null>(null);

    const isSuccess = data.status === "COMPLETED";
    const plan = data.plan as {
        project_type?: string;
        technologies?: string[];
        components?: string[];
        tasks?: { id: number; description: string }[];
        testing_requirements?: string[];
    };

    const toggleFile = async (file: string) => {
        if (expandedFiles.has(file)) {
            const next = new Set(expandedFiles);
            next.delete(file);
            setExpandedFiles(next);
            return;
        }

        if (!fileContents[file]) {
            setLoadingFile(file);
            try {
                const content = await fetchFileContent(data.project_id, file);
                setFileContents((prev) => ({ ...prev, [file]: content }));
            } catch {
                setFileContents((prev) => ({
                    ...prev,
                    [file]: "// Error loading file content",
                }));
            }
            setLoadingFile(null);
        }

        setExpandedFiles(new Set(expandedFiles).add(file));
    };

    return (
        <div className="mt-4 space-y-4">
            {/* Status badge */}
            <div className="flex items-center gap-2">
                {isSuccess ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                ) : (
                    <XCircle className="h-4 w-4 text-red-400" />
                )}
                <span
                    className={`text-xs font-medium ${isSuccess ? "text-emerald-400" : "text-red-400"}`}
                >
                    {data.status}
                </span>
                <span className="text-[10px] text-zinc-600">
                    · {data.iteration} iteration(s)
                </span>
                <span className="text-[10px] text-zinc-600">
                    · Project: {data.project_id}
                </span>
            </div>

            {/* Plan */}
            {plan && plan.project_type && (
                <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
                    <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider text-violet-400">
                        Development Plan
                    </h4>
                    <div className="space-y-2 text-[12px] text-zinc-400">
                        <p>
                            <span className="text-zinc-300">Type:</span>{" "}
                            {plan.project_type}
                        </p>
                        {plan.technologies && (
                            <p>
                                <span className="text-zinc-300">Tech:</span>{" "}
                                {plan.technologies.join(", ")}
                            </p>
                        )}
                        {plan.components && (
                            <p>
                                <span className="text-zinc-300">
                                    Components:
                                </span>{" "}
                                {plan.components.join(", ")}
                            </p>
                        )}
                        {plan.tasks && (
                            <div className="mt-2">
                                <span className="text-zinc-300">Tasks:</span>
                                <ul className="mt-1 list-inside list-decimal space-y-1 text-zinc-500">
                                    {plan.tasks.map((t) => (
                                        <li key={t.id}>{t.description}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Files */}
            {data.files && data.files.length > 0 && (
                <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
                    <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider text-violet-400">
                        Generated Files ({data.files.length})
                    </h4>
                    <div className="space-y-1">
                        {data.files.map((file) => (
                            <div key={file}>
                                <button
                                    type="button"
                                    onClick={() => toggleFile(file)}
                                    className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-[12px] text-zinc-400 transition hover:bg-white/[0.04] hover:text-zinc-200"
                                >
                                    {expandedFiles.has(file) ? (
                                        <ChevronDown className="h-3 w-3 text-violet-400" />
                                    ) : (
                                        <ChevronRight className="h-3 w-3" />
                                    )}
                                    <FileCode2 className="h-3.5 w-3.5" />
                                    {file}
                                    {loadingFile === file && (
                                        <Loader2 className="ml-auto h-3 w-3 animate-spin text-violet-400" />
                                    )}
                                </button>
                                {expandedFiles.has(file) &&
                                    fileContents[file] && (
                                        <CodeBlock
                                            code={fileContents[file]}
                                            filename={file}
                                        />
                                    )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Test results */}
            {data.test_result && Object.keys(data.test_result).length > 0 && (
                <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
                    <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-violet-400">
                        Test Results
                    </h4>
                    <p className="text-[12px] text-zinc-400">
                        Status:{" "}
                        <span
                            className={
                                (data.test_result as Record<string, string>)
                                    .status === "PASSED"
                                    ? "text-emerald-400"
                                    : "text-red-400"
                            }
                        >
                            {
                                (data.test_result as Record<string, string>)
                                    .status
                            }
                        </span>
                    </p>
                </div>
            )}

            {/* Errors */}
            {data.errors && data.errors.length > 0 && (
                <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4">
                    <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-red-400">
                        Errors
                    </h4>
                    <ul className="space-y-1 text-[12px] text-red-300/70">
                        {data.errors.map((err, i) => (
                            <li key={i}>• {err}</li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}

/* =========================================================
   MESSAGE BUBBLE
========================================================= */

function MessageBubble({ msg }: { msg: Message }) {
    const isUser = msg.role === "user";

    return (
        <motion.div 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}
        >
            {!isUser && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-violet-400/20 bg-violet-500/10 shadow-lg shadow-violet-500/10">
                    <Bot className="h-4 w-4 text-violet-300" />
                </div>
            )}

            <div
                className={`max-w-[85%] ${
                    isUser
                        ? "rounded-2xl rounded-br-md border border-white/10 bg-white/[0.06] px-4 py-3"
                        : "flex-1"
                }`}
            >
                {isUser ? (
                    <p className="text-sm leading-6 text-zinc-200">
                        {msg.content}
                    </p>
                ) : (
                    <>
                        <p className="text-sm leading-6 text-zinc-300">
                            {msg.content}
                        </p>
                        {msg.data && <AgentResponseCard data={msg.data} />}
                    </>
                )}
                <p className="mt-1 text-[10px] text-zinc-700">
                    {msg.timestamp.toLocaleTimeString()}
                </p>
            </div>

            {isUser && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-white/10 bg-white/[0.06] shadow-xl">
                    <User className="h-4 w-4 text-zinc-300" />
                </div>
            )}
        </motion.div>
    );
}

/* =========================================================
   LOADING INDICATOR
========================================================= */

function AgentThinking({ 
    status, 
    plan, 
    projectId,
    streamText
}: { 
    status: string; 
    plan: any; 
    projectId: string | null;
    streamText?: string;
}) {
    const isWaiting = status === "WAITING_FOR_APPROVAL";

    const handleApprove = async () => {
        if (!projectId) return;
        try {
            await approveProjectPlan(projectId);
            // The polling loop will automatically pick up the new status
        } catch (e) {
            console.error("Failed to approve plan:", e);
        }
    };
    
    // Auto-scroll the streaming text container
    const streamRef = useRef<HTMLPreElement>(null);
    useEffect(() => {
        if (streamRef.current) {
            streamRef.current.scrollTop = streamRef.current.scrollHeight;
        }
    }, [streamText]);

    return (
        <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="flex gap-3"
        >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-violet-400/20 bg-violet-500/10 shadow-lg shadow-violet-500/20">
                <Bot className="h-4 w-4 text-violet-300" />
            </div>
            <div className="flex flex-col gap-3 rounded-2xl border border-violet-500/20 bg-[#0d0f14]/80 backdrop-blur-md px-4 py-3 w-[85%] shadow-xl shadow-violet-900/10 transition-all">
                <div className="flex items-center gap-3">
                    {isWaiting ? (
                        <CheckCircle className="h-4 w-4 text-violet-400" />
                    ) : (
                        <Loader2 className="h-4 w-4 animate-spin text-violet-400" />
                    )}
                    <div>
                        <p className="text-sm text-zinc-300">
                            {isWaiting ? "Plan is ready for your review!" : `Agents are working... (${status})`}
                        </p>
                        <p className="text-[11px] text-zinc-600">
                            Planning → Coding → Environment → Testing → Reviewing
                        </p>
                    </div>
                </div>

                {/* Show Plan if waiting */}
                {isWaiting && plan && plan.project_type && (
                    <div className="mt-2 rounded-xl border border-white/[0.08] bg-black/20 p-4">
                        <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider text-violet-400">
                            Proposed Development Plan
                        </h4>
                        <div className="space-y-2 text-[12px] text-zinc-400">
                            <p>
                                <span className="text-zinc-300">Type:</span>{" "}
                                {plan.project_type}
                            </p>
                            {plan.technologies && (
                                <p>
                                    <span className="text-zinc-300">Tech:</span>{" "}
                                    {plan.technologies.join(", ")}
                                </p>
                            )}
                            {plan.components && (
                                <p>
                                    <span className="text-zinc-300">
                                        Components:
                                    </span>{" "}
                                    {plan.components.join(", ")}
                                </p>
                            )}
                            {plan.tasks && (
                                <div className="mt-2">
                                    <span className="text-zinc-300">Tasks:</span>
                                    <ul className="mt-1 list-inside list-decimal space-y-1 text-zinc-500">
                                        {plan.tasks.map((t: any) => (
                                            <li key={t.id}>{t.description}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>

                        <div className="mt-4 flex justify-end">
                            <button
                                onClick={handleApprove}
                                className="flex items-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-xs font-medium text-white transition hover:bg-violet-700"
                            >
                                <Check className="h-4 w-4" />
                                Approve & Continue
                            </button>
                        </div>
                    </div>
                )}

                {/* Stream terminal when coding */}
                {status === "CODING" && streamText && (
                    <div className="mt-2 rounded-xl bg-black/40 border border-white/[0.05] p-3 overflow-hidden shadow-inner">
                        <div className="flex items-center justify-between mb-2 pb-2 border-b border-white/[0.05]">
                            <span className="text-[10px] uppercase tracking-wider text-zinc-500 font-mono flex items-center gap-2">
                                <Terminal className="h-3 w-3" />
                                Live Generation
                            </span>
                            <span className="flex h-2 w-2 rounded-full bg-violet-500 animate-pulse"></span>
                        </div>
                        <pre ref={streamRef} className="text-[11px] text-zinc-400 font-mono overflow-y-auto max-h-[150px] whitespace-pre-wrap break-all">
                            {streamText}
                        </pre>
                    </div>
                )}
            </div>
        </motion.div>
    );
}

/* =========================================================
   PROMPT COMPOSER
========================================================= */

function PromptComposer({
    onSend,
    loading,
}: {
    onSend: (text: string) => void;
    loading: boolean;
}) {
    const [value, setValue] = useState("");
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const handleSend = () => {
        const trimmed = value.trim();
        if (!trimmed || loading) return;
        onSend(trimmed);
        setValue("");
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    // Auto-resize
    const handleInput = () => {
        const el = textareaRef.current;
        if (el) {
            el.style.height = "auto";
            el.style.height = Math.min(el.scrollHeight, 200) + "px";
        }
    };

    return (
        <div className="mx-auto w-full max-w-3xl px-6">
            <div className="rounded-2xl border border-white/[0.1] bg-[#0d0f14]/90 shadow-2xl shadow-black/30 backdrop-blur-xl transition focus-within:border-violet-400/30 focus-within:shadow-violet-500/5">
                <textarea
                    ref={textareaRef}
                    placeholder="Ask DevAgent to build something..."
                    rows={3}
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    onInput={handleInput}
                    onKeyDown={handleKeyDown}
                    disabled={loading}
                    className="w-full resize-none bg-transparent px-5 pt-4 text-sm leading-6 text-zinc-200 outline-none placeholder:text-zinc-600 disabled:opacity-50"
                />

                <div className="flex items-center justify-between px-3 pb-3">
                    <div className="flex items-center gap-1">
                        <button
                            type="button"
                            className="flex h-8 w-8 items-center justify-center rounded-lg text-zinc-600 transition hover:bg-white/[0.06] hover:text-zinc-300"
                        >
                            <Paperclip className="h-4 w-4" />
                        </button>
                        <span className="hidden text-[10px] text-zinc-700 sm:block">
                            Attach files
                        </span>
                    </div>

                    <button
                        type="button"
                        onClick={handleSend}
                        disabled={!value.trim() || loading}
                        className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-black shadow-lg shadow-white/5 transition hover:bg-zinc-200 disabled:opacity-30"
                    >
                        {loading ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            <ArrowUp className="h-4 w-4" />
                        )}
                    </button>
                </div>
            </div>

            <p className="mt-3 text-center text-[10px] text-zinc-700">
                DevAgent can make mistakes. Review generated code before running
                it.
            </p>
        </div>
    );
}

/* =========================================================
   MAIN CHAT COMPONENT
========================================================= */

interface ChatProps {
    embedded?: boolean;
    onProjectCreated?: (projectId: string) => void;
}

export default function Chat({ embedded = false, onProjectCreated }: ChatProps) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [loading, setLoading] = useState(false);
    
    // New states for tracking background generation
    const [currentStatus, setCurrentStatus] = useState<string>("STARTED");
    const [currentPlan, setCurrentPlan] = useState<any>(null);
    const [currentProjectId, setCurrentProjectId] = useState<string | null>(null);
    const [streamText, setStreamText] = useState<string>("");
    
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, loading, currentStatus, streamText]);

    // Stream SSE when coding
    useEffect(() => {
        if (currentStatus === "CODING" && currentProjectId) {
            const eventSource = new EventSource(`/api/projects/${currentProjectId}/stream`);
            eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.chunk) {
                        setStreamText((prev) => {
                            const newText = prev + data.chunk;
                            // Keep only last 1000 chars to avoid memory issues and lagging UI
                            return newText.length > 1000 ? newText.slice(-1000) : newText;
                        });
                    }
                } catch (e) {
                    console.error("SSE Parse Error", e);
                }
            };
            eventSource.onerror = () => {
                eventSource.close();
            };
            return () => eventSource.close();
        } else {
            setStreamText("");
        }
    }, [currentStatus, currentProjectId]);

    const handleSend = async (text: string) => {
        // Add user message
        const userMsg: Message = {
            id: crypto.randomUUID(),
            role: "user",
            content: text,
            timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMsg]);
        setLoading(true);
        setCurrentStatus("STARTED");
        setCurrentPlan(null);

        try {
            const result = await generateProject(
                text,
                (status, plan) => {
                    setCurrentStatus(status);
                    if (plan) setCurrentPlan(plan);
                },
                (projectId) => {
                    setCurrentProjectId(projectId);
                    if (onProjectCreated) onProjectCreated(projectId);
                }
            );

            const agentMsg: Message = {
                id: crypto.randomUUID(),
                role: "agent",
                content:
                    result.status === "COMPLETED"
                        ? `Project **${result.project_id}** has been built successfully! The pipeline completed in ${result.iteration} iteration(s). Here's what was generated:`
                        : `Project **${result.project_id}** finished with status: **${result.status}**. There may be issues to review:`,
                timestamp: new Date(),
                data: result,
            };

            setMessages((prev) => [...prev, agentMsg]);
        } catch (err: unknown) {
            const errorMsg = err instanceof Error ? err.message : String(err);

            const agentMsg: Message = {
                id: crypto.randomUUID(),
                role: "agent",
                content: `Something went wrong while running the pipeline: ${errorMsg}`,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, agentMsg]);
        } finally {
            setLoading(false);
            setCurrentProjectId(null);
            setCurrentPlan(null);
        }
    };

    const hasMessages = messages.length > 0;

    return (
        <div className={`relative flex flex-col overflow-hidden text-white ${embedded ? 'h-full bg-transparent' : 'h-screen bg-[#08090d]'}`}>
            {!embedded && <ChatBackground />}

            <div className="relative flex flex-1 flex-col h-full">
                {!embedded && <ChatHeader />}

                <main className={`flex-1 overflow-y-auto ${embedded ? 'pb-32' : 'pb-56'}`}>
                    {!hasMessages && (
                        <>
                            {!embedded && <ChatWelcome />}
                            <div className={embedded ? "px-4 pt-4" : ""}>
                                <ChatSuggestions onSelect={handleSend} />
                            </div>
                        </>
                    )}

                    {hasMessages && (
                        <div className={`mx-auto space-y-6 ${embedded ? 'px-4 py-4 w-full' : 'max-w-3xl px-6 py-8'}`}>
                            <AnimatePresence mode="popLayout">
                                {messages.map((msg) => (
                                    <MessageBubble key={msg.id} msg={msg} />
                                ))}
                                {loading && <AgentThinking status={currentStatus} plan={currentPlan} projectId={currentProjectId} streamText={streamText} />}
                            </AnimatePresence>
                            <div ref={messagesEndRef} />
                        </div>
                    )}
                </main>

                <div className={`pointer-events-none absolute bottom-0 left-0 right-0 bg-gradient-to-t from-[#08090d] via-[#08090d] to-transparent ${embedded ? 'pb-4 pt-10 px-2' : 'pb-6 pt-20'}`}>
                    <div className="pointer-events-auto">
                        <PromptComposer onSend={handleSend} loading={loading} />
                    </div>
                </div>
            </div>
        </div>
    );
}
