// ─────────────────────────────────────────────
// API Client — talks to the Flask backend
// ─────────────────────────────────────────────

const BASE = "/api";

export interface GenerateRequest {
  requirement: string;
}

export interface GenerateResponse {
  project_id: string;
  status: string;
  plan: Record<string, unknown>;
  files: string[];
  test_result: Record<string, unknown>;
  review_result: string;
  errors: string[];
  iteration: number;
  error?: string;
}

export interface FileContentResponse {
  project_id: string;
  path: string;
  content: string;
}

export interface ProjectFilesResponse {
  project_id: string;
  files: string[];
}

// ─── Generate a project ──────────────────────
export async function generateProject(
  requirement: string,
  onStatusChange?: (status: string, plan?: any) => void,
  onProjectCreated?: (projectId: string) => void
): Promise<GenerateResponse> {
  onStatusChange?.("SENDING_REQUEST");

  const res = await fetch(`${BASE}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ requirement }),
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.error || "Unknown server error");
  }

  const projectId = data.project_id;
  if (onProjectCreated) {
    onProjectCreated(projectId);
  }

  // Poll until completion
  while (true) {
    await new Promise((resolve) => setTimeout(resolve, 2000));
    try {
      const statusRes = await fetch(`${BASE}/projects/${projectId}/status`);
      if (statusRes.ok) {
        const statusData = await statusRes.json();
        onStatusChange?.(statusData.status, statusData.plan);
        
        if (statusData.status === "COMPLETED" || statusData.status === "FAILED") {
          const files = await fetchProjectFiles(projectId).catch(() => []);
          return {
            project_id: projectId,
            status: statusData.status,
            plan: statusData.plan || {},
            files: files,
            test_result: {},
            review_result: "",
            errors: [],
            iteration: 0,
          };
        }
      }
    } catch (e) {
      console.error("Failed to poll status:", e);
    }
  }
}

// ─── Approve a plan ──────────────────────
export async function approveProjectPlan(projectId: string): Promise<void> {
  const res = await fetch(`${BASE}/projects/${projectId}/approve`, {
    method: "POST",
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.error || "Failed to approve plan");
  }
}

// ─── Retry a failed project ──────────────────────
export async function retryProject(projectId: string): Promise<void> {
  const res = await fetch(`${BASE}/projects/${projectId}/retry`, {
    method: "POST",
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.error || "Failed to retry project");
  }
}

// ─── List project files ──────────────────────
export async function fetchProjectFiles(
  projectId: string
): Promise<string[]> {
  const res = await fetch(`${BASE}/projects/${projectId}/files`);
  const data: ProjectFilesResponse = await res.json();
  return data.files;
}

// ─── Read a single file ──────────────────────
export async function fetchFileContent(
  projectId: string,
  filePath: string
): Promise<string> {
  const res = await fetch(
    `${BASE}/projects/${projectId}/files/${filePath}`
  );
  const data: FileContentResponse = await res.json();
  return data.content;
}

// ─── Health check ────────────────────────────
export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE}/health`);
    return res.ok;
  } catch {
    return false;
  }
}

export interface ProjectInfo {
  id: string;
  name: string;
  status: string;
  created_at: string;
}

// ─── List past projects ──────────────────────
export async function fetchProjects(): Promise<ProjectInfo[]> {
  const res = await fetch(`${BASE}/projects`);
  if (!res.ok) {
    throw new Error("Failed to fetch projects");
  }
  const data = await res.json();
  return data.projects || [];
}
