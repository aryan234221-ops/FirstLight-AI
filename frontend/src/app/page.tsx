"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { EnterprisePanel } from "@/components/EnterprisePanel";
import { ExecutionDetailsPanel } from "@/components/ExecutionDetailsPanel";
import { ExecutionHistoryPanel } from "@/components/ExecutionHistoryPanel";
import { KnowledgeLibraryPanel } from "@/components/KnowledgeLibraryPanel";
import { PlanResultCards } from "@/components/PlanResultCards";
import { ProjectSidebar } from "@/components/ProjectSidebar";
import { StudioTopBar } from "@/components/StudioTopBar";
import {
  EmployeeId,
  ExecutionMode,
  ExecutionRecord,
  AuthSession,
  KnowledgeDocumentMetadata,
  KnowledgeUploadInput,
  Project,
  WorkflowResult,
} from "@/components/studio-types";
import { Plan } from "@/components/studio-types";

const BACKEND_BASE_URL = "http://127.0.0.1:8000";
const PROJECTS_STORAGE_KEY = "fl.projects";
const EXECUTIONS_STORAGE_KEY = "fl.executions";
const SELECTED_PROJECT_STORAGE_KEY = "fl.selectedProjectId";
const KNOWLEDGE_STORAGE_KEY = "fl.knowledgeDocuments";
const AUTH_STORAGE_KEY = "fl.authSession";

type InitialWorkspaceState = {
  projects: Project[];
  executions: ExecutionRecord[];
  knowledgeDocuments: KnowledgeDocumentMetadata[];
  selectedProjectId: string | null;
};

type WorkspaceTab = "workspace" | "knowledge" | "enterprise";
const DEFAULT_PROJECT_ID = "firstlight-core";
const DEFAULT_PROJECT_CREATED_AT = "2026-01-01T00:00:00.000Z";

function parseStoredArray<T>(raw: string | null): T[] {
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as T[]) : [];
  } catch {
    return [];
  }
}

function createDefaultProject(): Project {
  return {
    id: DEFAULT_PROJECT_ID,
    name: "FirstLight Core",
    description: "Primary AI workforce initiative",
    createdDate: DEFAULT_PROJECT_CREATED_AT,
    lastRun: null,
    workflowType: "workflow",
    preferredProvider: "Gemini 3.5 Flash",
    selectedAgent: "ceo",
    goalDraft: "Launch a production-ready AI planning workspace.",
  };
}

function loadInitialWorkspaceState(): InitialWorkspaceState {
  const fallback = createDefaultProject();
  return { projects: [fallback], executions: [], knowledgeDocuments: [], selectedProjectId: fallback.id };
}

function loadWorkspaceStateFromStorage(): InitialWorkspaceState {
  const fallback = createDefaultProject();
  try {
    const storedProjects = localStorage.getItem(PROJECTS_STORAGE_KEY);
    const storedExecutions = localStorage.getItem(EXECUTIONS_STORAGE_KEY);
    const storedKnowledgeDocuments = localStorage.getItem(KNOWLEDGE_STORAGE_KEY);
    const storedSelectedProjectId = localStorage.getItem(SELECTED_PROJECT_STORAGE_KEY);

    const parsedProjects = parseStoredArray<Project>(storedProjects).filter(
      (project) =>
        typeof project?.id === "string" &&
        typeof project?.name === "string" &&
        typeof project?.description === "string" &&
        typeof project?.createdDate === "string",
    );
    const projects = parsedProjects.length > 0 ? parsedProjects : [createDefaultProject()];
    const executions = parseStoredArray<ExecutionRecord>(storedExecutions);
    const knowledgeDocuments = parseStoredArray<KnowledgeDocumentMetadata>(storedKnowledgeDocuments);
    const selectedProjectId =
      storedSelectedProjectId && projects.some((project) => project.id === storedSelectedProjectId)
        ? storedSelectedProjectId
        : projects[0]?.id ?? null;

    return { projects, executions, knowledgeDocuments, selectedProjectId };
  } catch {
    return { projects: [fallback], executions: [], knowledgeDocuments: [], selectedProjectId: fallback.id };
  }
}

function buildKnowledgeUploadRequest(projectId: string, upload: KnowledgeUploadInput): KnowledgeDocumentMetadata {
  return {
    ...upload.metadata,
    projectId,
  };
}

function safePrompt(message: string, defaultValue = ""): string | null {
  try {
    return window.prompt(message, defaultValue);
  } catch {
    return defaultValue;
  }
}

function safeConfirm(message: string): boolean {
  try {
    return window.confirm(message);
  } catch {
    return true;
  }
}

export default function Home() {
  const initialState = loadInitialWorkspaceState();
  const [projects, setProjects] = useState<Project[]>(initialState.projects);
  const [executions, setExecutions] = useState<ExecutionRecord[]>(initialState.executions);
  const [knowledgeDocuments, setKnowledgeDocuments] = useState<KnowledgeDocumentMetadata[]>(initialState.knowledgeDocuments);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(initialState.selectedProjectId);
  const [hasHydratedStorage, setHasHydratedStorage] = useState(false);
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("workspace");
  const [authSession, setAuthSession] = useState<AuthSession | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "running" | "completed" | "failed">("idle");
  const [currentStep, setCurrentStep] = useState("None");
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [connectionStatus, setConnectionStatus] = useState<"Connected" | "Disconnected">("Connected");
  const [darkMode, setDarkMode] = useState(true);
  const knowledgeFileCacheRef = useRef<Record<string, File>>({});

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
  }, [darkMode]);

  useEffect(() => {
    const storedState = loadWorkspaceStateFromStorage();
    const storedAuth = localStorage.getItem(AUTH_STORAGE_KEY);

    const hydrateState = () => {
      setProjects(storedState.projects);
      setExecutions(storedState.executions);
      setKnowledgeDocuments(storedState.knowledgeDocuments);
      setSelectedProjectId(storedState.selectedProjectId);
      if (storedAuth) {
        try {
          setAuthSession(JSON.parse(storedAuth) as AuthSession);
        } catch {
          setAuthSession(null);
        }
      }
      setHasHydratedStorage(true);
    };

    const timeoutId = window.setTimeout(hydrateState, 0);
    return () => window.clearTimeout(timeoutId);
  }, []);

  useEffect(() => {
    if (!hasHydratedStorage) {
      return;
    }
    if (projects.length === 0) {
      return;
    }
    localStorage.setItem(PROJECTS_STORAGE_KEY, JSON.stringify(projects));
  }, [projects, hasHydratedStorage]);

  useEffect(() => {
    if (!hasHydratedStorage) {
      return;
    }
    localStorage.setItem(EXECUTIONS_STORAGE_KEY, JSON.stringify(executions));
  }, [executions, hasHydratedStorage]);

  useEffect(() => {
    if (!hasHydratedStorage) {
      return;
    }
    localStorage.setItem(KNOWLEDGE_STORAGE_KEY, JSON.stringify(knowledgeDocuments));
  }, [knowledgeDocuments, hasHydratedStorage]);

  useEffect(() => {
    if (!hasHydratedStorage) {
      return;
    }
    if (!selectedProjectId) {
      return;
    }
    localStorage.setItem(SELECTED_PROJECT_STORAGE_KEY, selectedProjectId);
  }, [selectedProjectId, hasHydratedStorage]);

  useEffect(() => {
    if (!hasHydratedStorage) {
      return;
    }
    if (!authSession) {
      localStorage.removeItem(AUTH_STORAGE_KEY);
      return;
    }
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(authSession));
  }, [authSession, hasHydratedStorage]);

  useEffect(() => {
    if (!loading || startedAt === null) {
      return;
    }

    const timer = setInterval(() => {
      setElapsedMs(Date.now() - startedAt);
    }, 300);

    return () => clearInterval(timer);
  }, [loading, startedAt]);

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === selectedProjectId) ?? null,
    [projects, selectedProjectId],
  );

  const projectExecutions = useMemo(() => {
    if (!selectedProjectId) {
      return [];
    }
    return executions.filter((record) => record.projectId === selectedProjectId).reverse();
  }, [executions, selectedProjectId]);

  const latestResult = useMemo(() => {
    const latest = projectExecutions.find((record) => record.result !== null);
    return latest?.result ?? null;
  }, [projectExecutions]);

  const selectedProjectKnowledge = useMemo(() => {
    if (!selectedProjectId) {
      return [];
    }
    return knowledgeDocuments
      .filter((document) => document.projectId === selectedProjectId)
      .sort((a, b) => b.uploadedDate.localeCompare(a.uploadedDate));
  }, [knowledgeDocuments, selectedProjectId]);

  const updateSelectedProject = (updater: (project: Project) => Project) => {
    if (!selectedProjectId) {
      return;
    }
    setProjects((previous) => previous.map((project) => (project.id === selectedProjectId ? updater(project) : project)));
  };

  const handleCreateProject = () => {
    const name = safePrompt("Project name", "New Project")?.trim();
    if (!name) {
      return;
    }

    const description = safePrompt("Project description", "")?.trim() ?? "";
    const newProject: Project = {
      id: crypto.randomUUID(),
      name,
      description,
      createdDate: new Date().toISOString(),
      lastRun: null,
      workflowType: "workflow",
      preferredProvider: "Gemini 3.5 Flash",
      selectedAgent: "ceo",
      goalDraft: "",
    };

    setProjects((previous) => [...previous, newProject]);
    setSelectedProjectId(newProject.id);
  };

  const handleRenameProject = (projectId: string) => {
    const current = projects.find((project) => project.id === projectId);
    if (!current) {
      return;
    }

    const nextName = safePrompt("Rename project", `${current.name} Renamed`)?.trim();
    if (!nextName) {
      return;
    }

    setProjects((previous) =>
      previous.map((project) => (project.id === projectId ? { ...project, name: nextName } : project)),
    );
  };

  const handleDeleteProject = (projectId: string) => {
    const current = projects.find((project) => project.id === projectId);
    if (!current) {
      return;
    }

    const confirmed = safeConfirm(`Delete project "${current.name}"?`);
    if (!confirmed) {
      return;
    }

    const remaining = projects.filter((project) => project.id !== projectId);
    setProjects(remaining);
    setExecutions((previous) => previous.filter((record) => record.projectId !== projectId));
    setKnowledgeDocuments((previous) => previous.filter((document) => document.projectId !== projectId));
    for (const key of Object.keys(knowledgeFileCacheRef.current)) {
      if (key.startsWith(`${projectId}:`)) {
        delete knowledgeFileCacheRef.current[key];
      }
    }
    setSelectedProjectId(remaining[0]?.id ?? null);
  };

  const handleKnowledgeUpload = (upload: KnowledgeUploadInput) => {
    if (!selectedProjectId) {
      return;
    }

    const metadata = buildKnowledgeUploadRequest(selectedProjectId, upload);
    setKnowledgeDocuments((previous) => [metadata, ...previous]);
    knowledgeFileCacheRef.current[`${selectedProjectId}:${metadata.id}`] = upload.file;
  };

  const handleKnowledgeRemove = (documentId: string) => {
    if (!selectedProjectId) {
      return;
    }

    setKnowledgeDocuments((previous) => previous.filter((document) => document.id !== documentId));
    delete knowledgeFileCacheRef.current[`${selectedProjectId}:${documentId}`];
  };

  const runAI = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!selectedProject) {
      setError("Please create and select a project first.");
      return;
    }

    const normalizedGoal = selectedProject.goalDraft.trim();
    if (!normalizedGoal) {
      setError("Please enter a goal for this project.");
      return;
    }

    setError(null);

    setLoading(true);
    setStatus("running");
    setStartedAt(Date.now());
    setElapsedMs(0);
    setCurrentStep(
      selectedProject.workflowType === "agent"
        ? `Agent: ${selectedProject.selectedAgent}`
        : "Workflow: CEO -> Architect",
    );

    const started = Date.now();

    try {
      const endpoint =
        selectedProject.workflowType === "agent"
          ? `${BACKEND_BASE_URL}/api/v1/agents/${selectedProject.selectedAgent}/plan`
          : `${BACKEND_BASE_URL}/api/v1/workflows/plan`;

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ goal: normalizedGoal }),
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(payload?.detail ?? "Request failed while running AI workforce.");
      }

      const payload = (await response.json()) as Plan | WorkflowResult;
      const completedAt = new Date().toISOString();
      const duration = Date.now() - started;

      setExecutions((previous) => [
        ...previous,
        {
          id: crypto.randomUUID(),
          projectId: selectedProject.id,
          date: completedAt,
          workflow: selectedProject.workflowType,
          status: "completed",
          durationMs: duration,
          result: payload,
          errorMessage: null,
        },
      ]);

      setProjects((previous) =>
        previous.map((project) =>
          project.id === selectedProject.id
            ? {
                ...project,
                lastRun: completedAt,
              }
            : project,
        ),
      );

      setConnectionStatus("Connected");
      setStatus("completed");
      setCurrentStep("Completed");
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : "Execution failed unexpectedly.";
      const completedAt = new Date().toISOString();
      const duration = Date.now() - started;

      setExecutions((previous) => [
        ...previous,
        {
          id: crypto.randomUUID(),
          projectId: selectedProject.id,
          date: completedAt,
          workflow: selectedProject.workflowType,
          status: "failed",
          durationMs: duration,
          result: null,
          errorMessage: message,
        },
      ]);

      setError(message);
      setStatus("failed");
      setConnectionStatus("Disconnected");
      setCurrentStep("Failed");
    } finally {
      setLoading(false);
    }
  };

  if (!hasHydratedStorage) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100">
        <main className="mx-auto flex w-full max-w-[1600px] flex-col gap-4 px-3 py-4 sm:px-4 lg:px-6">
          <section className="rounded-2xl border border-zinc-800 bg-zinc-900/80 p-6 text-sm text-zinc-400">
            Loading workspace...
          </section>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <main className="mx-auto flex w-full max-w-[1600px] flex-col gap-4 px-3 py-4 sm:px-4 lg:px-6">
        <StudioTopBar
          provider={selectedProject?.preferredProvider ?? "Gemini 3.5 Flash"}
          connectionStatus={connectionStatus}
          darkMode={darkMode}
          onToggleTheme={() => setDarkMode((current) => !current)}
        />

        <div className="grid gap-4 xl:grid-cols-[280px_minmax(0,1fr)_320px]">
          <ProjectSidebar
            projects={projects}
            selectedProjectId={selectedProjectId}
            onSelectProject={setSelectedProjectId}
            onCreateProject={handleCreateProject}
            onRenameProject={handleRenameProject}
            onDeleteProject={handleDeleteProject}
          />

          <section className="space-y-4 rounded-2xl border border-zinc-800 bg-zinc-900/80 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-400">Project Workspace</h2>
              <div className="inline-flex rounded-lg border border-zinc-700 bg-zinc-900 p-1">
                <button
                  className={`rounded-md px-3 py-1 text-xs font-semibold transition ${
                    activeTab === "workspace"
                      ? "bg-zinc-700 text-zinc-100"
                      : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
                  }`}
                  onClick={() => setActiveTab("workspace")}
                  type="button"
                >
                  Workspace
                </button>
                <button
                  className={`rounded-md px-3 py-1 text-xs font-semibold transition ${
                    activeTab === "knowledge"
                      ? "bg-zinc-700 text-zinc-100"
                      : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
                  }`}
                  onClick={() => setActiveTab("knowledge")}
                  type="button"
                >
                  Knowledge
                </button>
                <button
                  className={`rounded-md px-3 py-1 text-xs font-semibold transition ${
                    activeTab === "enterprise"
                      ? "bg-zinc-700 text-zinc-100"
                      : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
                  }`}
                  onClick={() => setActiveTab("enterprise")}
                  type="button"
                >
                  Enterprise
                </button>
              </div>
            </div>

            {!selectedProject ? (
              <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-4 text-sm text-zinc-400">
                Create or select a project to begin.
              </div>
            ) : (
              <>
                <section className="rounded-xl border border-zinc-800 bg-zinc-950/70 p-4">
                  <h3 className="text-sm font-semibold text-zinc-200">Project Information</h3>
                  <div className="mt-3 grid gap-3 sm:grid-cols-2">
                    <label className="text-xs text-zinc-400">
                      Name
                      <input
                        className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-900 px-2 py-1.5 text-sm text-zinc-100"
                        onChange={(event) =>
                          updateSelectedProject((project) => ({ ...project, name: event.target.value }))
                        }
                        value={selectedProject.name}
                      />
                    </label>
                    <label className="text-xs text-zinc-400">
                      Preferred AI Provider
                      <input
                        className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-900 px-2 py-1.5 text-sm text-zinc-100"
                        onChange={(event) =>
                          updateSelectedProject((project) => ({ ...project, preferredProvider: event.target.value }))
                        }
                        value={selectedProject.preferredProvider}
                      />
                    </label>
                    <label className="text-xs text-zinc-400 sm:col-span-2">
                      Description
                      <textarea
                        className="mt-1 min-h-20 w-full rounded-lg border border-zinc-700 bg-zinc-900 px-2 py-1.5 text-sm text-zinc-100"
                        onChange={(event) =>
                          updateSelectedProject((project) => ({ ...project, description: event.target.value }))
                        }
                        value={selectedProject.description}
                      />
                    </label>
                  </div>
                </section>

                {activeTab === "workspace" ? (
                  <>
                    <form className="space-y-4" onSubmit={runAI}>
                      <section className="rounded-xl border border-zinc-800 bg-zinc-950/70 p-4">
                        <h3 className="text-sm font-semibold text-zinc-200">Goal Editor</h3>
                        <textarea
                          className="mt-3 min-h-36 w-full resize-y rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none ring-emerald-500/70 focus:ring"
                          onChange={(event) =>
                            updateSelectedProject((project) => ({ ...project, goalDraft: event.target.value }))
                          }
                          placeholder="Describe the objective for this project..."
                          value={selectedProject.goalDraft}
                        />

                        <div className="mt-3 grid gap-3 sm:grid-cols-2">
                          <label className="text-xs text-zinc-400">
                            Workflow Selector
                            <select
                              className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-900 px-2 py-1.5 text-sm text-zinc-100"
                              onChange={(event) =>
                                updateSelectedProject((project) => ({
                                  ...project,
                                  workflowType: event.target.value as ExecutionMode,
                                }))
                              }
                              value={selectedProject.workflowType}
                            >
                              <option value="agent">Single Agent</option>
                              <option value="workflow">CEO -&gt; Architect Workflow</option>
                            </select>
                          </label>

                          <label className="text-xs text-zinc-400">
                            Agent
                            <select
                              className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-900 px-2 py-1.5 text-sm text-zinc-100"
                              disabled={selectedProject.workflowType === "workflow"}
                              onChange={(event) =>
                                updateSelectedProject((project) => ({
                                  ...project,
                                  selectedAgent: event.target.value as EmployeeId,
                                }))
                              }
                              value={selectedProject.selectedAgent}
                            >
                              <option value="ceo">CEO</option>
                              <option value="architect">Architect</option>
                            </select>
                          </label>
                        </div>

                        <button
                          className="mt-4 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:bg-emerald-900"
                          disabled={loading}
                          type="submit"
                        >
                          {loading ? "Running AI..." : "Run AI"}
                        </button>
                      </section>
                    </form>

                    {error && (
                      <section className="rounded-xl border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-200">
                        {error}
                      </section>
                    )}

                    <ExecutionHistoryPanel records={projectExecutions} />

                    {latestResult && (
                      <section className="space-y-3 rounded-xl border border-zinc-800 bg-zinc-950/70 p-4">
                        <h3 className="text-sm font-semibold text-zinc-200">Latest AI Output</h3>
                        <PlanResultCards result={latestResult} />
                        <details className="rounded-lg border border-zinc-800 bg-zinc-950 p-2">
                          <summary className="cursor-pointer text-xs font-semibold text-zinc-400">Raw JSON</summary>
                          <pre className="mt-2 overflow-auto text-xs text-zinc-300">
                            {JSON.stringify(latestResult, null, 2)}
                          </pre>
                        </details>
                      </section>
                    )}
                  </>
                ) : activeTab === "knowledge" ? (
                  <KnowledgeLibraryPanel
                    records={selectedProjectKnowledge}
                    onUpload={handleKnowledgeUpload}
                    onRemove={handleKnowledgeRemove}
                  />
                ) : (
                  <EnterprisePanel
                    backendBaseUrl={BACKEND_BASE_URL}
                    projectId={selectedProject.id}
                    projectName={selectedProject.name}
                    projectGoal={selectedProject.goalDraft}
                    auth={authSession}
                    onAuthChange={setAuthSession}
                  />
                )}
              </>
            )}
          </section>

          <ExecutionDetailsPanel
            mode={selectedProject?.workflowType ?? "agent"}
            selectedAgentLabel={selectedProject ? selectedProject.selectedAgent : "None"}
            currentStep={currentStep}
            status={status}
            elapsedMs={elapsedMs}
          />
        </div>
      </main>
    </div>
  );
}
