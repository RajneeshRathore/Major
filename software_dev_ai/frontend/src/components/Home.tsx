import {
    ArrowRight,
    Bot,
    Code2,
    FolderGit2,
    GitBranch,
    Plus,
    Sparkles,
    Terminal,
    Clock3,
    MoreHorizontal,
} from "lucide-react";

const recentProjects = [
    {
        name: "devagent-website",
        path: "~/Projects/devagent-website",
        language: "TypeScript",
        lastOpened: "2 hours ago",
        branch: "main",
    },
    {
        name: "ai-dashboard",
        path: "~/Projects/ai-dashboard",
        language: "React",
        lastOpened: "Yesterday",
        branch: "develop",
    },
    {
        name: "api-server",
        path: "~/Projects/api-server",
        language: "Python",
        lastOpened: "3 days ago",
        branch: "main",
    },
];

const features = [
    {
        icon: Bot,
        title: "AI Coding Agent",
        description:
            "Plan, write, debug and refactor your code with an autonomous AI agent.",
    },
    {
        icon: Code2,
        title: "Powerful Editor",
        description:
            "A VS Code-like editor powered by Monaco with tabs, syntax highlighting and more.",
    },
    {
        icon: Terminal,
        title: "Built-in Terminal",
        description:
            "Run commands, install dependencies and execute your project without leaving the IDE.",
    },
    {
        icon: GitBranch,
        title: "Git Ready",
        description:
            "Work with branches, diffs and commits directly inside your development environment.",
    },
];

function HomeBackground() {
    return (
        <div className="pointer-events-none fixed inset-0 overflow-hidden">
            {/* Main purple glow */}
            <div className="absolute left-1/2 top-[-280px] h-[600px] w-[900px] -translate-x-1/2 rounded-full bg-violet-600/10 blur-[140px]" />

            {/* Blue glow */}
            <div className="absolute left-[-200px] top-[40%] h-[400px] w-[400px] rounded-full bg-blue-600/5 blur-[120px]" />

            {/* Purple bottom glow */}
            <div className="absolute bottom-[-200px] right-[-100px] h-[450px] w-[450px] rounded-full bg-purple-600/5 blur-[120px]" />

            {/* Grid */}
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

function HomeHeader() {
    return (
        <header className="mb-20 flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 bg-white/[0.06] shadow-lg shadow-violet-500/10">
                    <Sparkles className="h-4 w-4 text-violet-300" />
                </div>

                <div>
                    <h1 className="text-sm font-semibold tracking-tight">
                        DevAgent
                    </h1>

                    <p className="text-[11px] text-zinc-500">
                        AI Development IDE
                    </p>
                </div>
            </div>

            {/* Settings */}
            <button
                type="button"
                className="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-xs text-zinc-400 transition hover:border-white/20 hover:bg-white/[0.07] hover:text-white"
            >
                Settings
            </button>
        </header>
    );
}

function HomeHero() {
    return (
        <section className="mx-auto max-w-4xl text-center">
            {/* Badge */}
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-violet-400/20 bg-violet-400/[0.06] px-3 py-1.5 text-xs text-violet-300">
                <Sparkles className="h-3.5 w-3.5" />

                AI-powered development environment
            </div>

            {/* Heading */}
            <h2 className="text-4xl font-semibold tracking-[-0.04em] text-white sm:text-5xl lg:text-6xl">
                Build software with

                <span className="block bg-gradient-to-r from-violet-300 via-purple-300 to-blue-300 bg-clip-text text-transparent">
                    an AI that actually codes.
                </span>
            </h2>

            {/* Description */}
            <p className="mx-auto mt-6 max-w-2xl text-sm leading-7 text-zinc-400 sm:text-base">
                A local-first development environment where your AI agent can
                understand your project, write code, run commands, debug errors,
                and help you ship faster.
            </p>

            {/* Buttons */}
            <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
                {/* New Project */}
                <button
                    type="button"
                    className="group flex items-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-black shadow-xl shadow-white/10 transition hover:-translate-y-0.5 hover:bg-zinc-100"
                >
                    <Plus className="h-4 w-4" />

                    Create new project

                    <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </button>

                {/* Recent Project */}
                <button
                    type="button"
                    className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-5 py-3 text-sm font-medium text-zinc-300 transition hover:border-white/20 hover:bg-white/[0.06] hover:text-white"
                >
                    <FolderGit2 className="h-4 w-4" />

                    Open recent project
                </button>
            </div>
        </section>
    );
}

function HomeFeatures() {
    return (
        <section className="mt-28">
            {/* Section heading */}
            <div className="mb-7">
                <p className="text-xs font-medium uppercase tracking-[0.2em] text-violet-400">
                    Everything you need
                </p>

                <h3 className="mt-2 text-xl font-semibold tracking-tight">
                    Your development workspace
                </h3>
            </div>

            {/* Feature cards */}
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {features.map((feature) => {
                    const Icon = feature.icon;

                    return (
                        <div
                            key={feature.title}
                            className="group relative overflow-hidden rounded-2xl border border-white/[0.08] bg-white/[0.025] p-5 transition duration-300 hover:-translate-y-1 hover:border-white/[0.15] hover:bg-white/[0.045]"
                        >
                            {/* Glow */}
                            <div className="absolute right-0 top-0 h-24 w-24 translate-x-8 -translate-y-8 rounded-full bg-violet-500/10 blur-2xl transition group-hover:bg-violet-500/20" />

                            <div className="relative">
                                {/* Icon */}
                                <div className="mb-5 flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/[0.05]">
                                    <Icon className="h-5 w-5 text-violet-300" />
                                </div>

                                {/* Title */}
                                <h4 className="text-sm font-semibold text-white">
                                    {feature.title}
                                </h4>

                                {/* Description */}
                                <p className="mt-2 text-xs leading-6 text-zinc-500">
                                    {feature.description}
                                </p>
                            </div>
                        </div>
                    );
                })}
            </div>
        </section>
    );
}

function RecentProjects() {
    return (
        <section className="mt-24 pb-16">
            {/* Heading */}
            <div className="mb-6 flex items-center justify-between">
                <div>
                    <p className="text-xs font-medium uppercase tracking-[0.2em] text-zinc-500">
                        Workspace
                    </p>

                    <h3 className="mt-2 text-xl font-semibold tracking-tight">
                        Recent projects
                    </h3>
                </div>

                {/* New project button */}
                <button
                    type="button"
                    className="hidden items-center gap-2 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-zinc-300 transition hover:bg-white/[0.07] hover:text-white sm:flex"
                >
                    <Plus className="h-3.5 w-3.5" />

                    New project
                </button>
            </div>

            {/* Project list */}
            <div className="overflow-hidden rounded-2xl border border-white/[0.08] bg-white/[0.02]">
                {recentProjects.map((project, index) => (
                    <div
                        key={project.name}
                        className={`group flex w-full items-center gap-4 px-5 py-4 transition hover:bg-white/[0.045] ${index !== recentProjects.length - 1
                                ? "border-b border-white/[0.06]"
                                : ""
                            }`}
                    >
                        {/* Project icon */}
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/[0.04]">
                            <FolderGit2 className="h-5 w-5 text-zinc-400 transition group-hover:text-violet-300" />
                        </div>

                        {/* Project info */}
                        <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2">
                                <h4 className="truncate text-sm font-medium text-zinc-200 group-hover:text-white">
                                    {project.name}
                                </h4>

                                {/* Language */}
                                <span className="hidden rounded-md border border-white/10 bg-white/[0.04] px-1.5 py-0.5 text-[10px] text-zinc-500 sm:block">
                                    {project.language}
                                </span>
                            </div>

                            <p className="mt-1 truncate text-xs text-zinc-600">
                                {project.path}
                            </p>
                        </div>

                        {/* Branch */}
                        <div className="hidden items-center gap-1.5 text-xs text-zinc-600 md:flex">
                            <GitBranch className="h-3.5 w-3.5" />

                            {project.branch}
                        </div>

                        {/* Last opened */}
                        <div className="hidden items-center gap-1.5 text-xs text-zinc-600 lg:flex">
                            <Clock3 className="h-3.5 w-3.5" />

                            {project.lastOpened}
                        </div>

                        {/* More */}
                        <MoreHorizontal className="h-4 w-4 shrink-0 text-zinc-700 transition group-hover:text-zinc-400" />
                    </div>
                ))}
            </div>
        </section>
    );
}

function HomeFooter() {
    return (
        <footer className="border-t border-white/[0.06] py-6">
            <div className="flex flex-col items-center justify-between gap-3 text-[11px] text-zinc-600 sm:flex-row">
                <span>DevAgent IDE</span>

                <div className="flex items-center gap-4">
                    {/* Status */}
                    <span className="flex items-center gap-1.5">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />

                        Local environment
                    </span>

                    <span>v0.1.0</span>
                </div>
            </div>
        </footer>
    );
}

export default function Home() {
    return (
        <div className="min-h-screen overflow-hidden bg-[#08090d] text-white">
            {/* Background */}
            <HomeBackground />
            {/* Page content */}
            <div className="relative mx-auto max-w-7xl px-6 py-8 lg:px-10">
                <HomeHeader />
                <HomeHero />
                <HomeFeatures />
                <RecentProjects />
                <HomeFooter />
            </div>
        </div>
    );
}


