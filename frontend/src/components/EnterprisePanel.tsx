import { FormEvent, useMemo, useState } from "react";

import {
  AuthSession,
  ChatMessage,
  DashboardOverview,
  WorkflowEvent,
  WorkflowRunSummary,
} from "@/components/studio-types";

type EnterprisePanelProps = {
  backendBaseUrl: string;
  projectId: string;
  projectName: string;
  projectGoal: string;
  auth: AuthSession | null;
  onAuthChange: (session: AuthSession | null) => void;
};

function authHeaders(auth: AuthSession | null): HeadersInit {
  if (!auth) {
    return { "Content-Type": "application/json" };
  }
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${auth.accessToken}`,
  };
}

export function EnterprisePanel({
  backendBaseUrl,
  projectId,
  projectName,
  projectGoal,
  auth,
  onAuthChange,
}: EnterprisePanelProps) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("ChangeMeNow123!");
  const [enterpriseError, setEnterpriseError] = useState<string | null>(null);

  const [dashboard, setDashboard] = useState<DashboardOverview | null>(null);
  const [activeRun, setActiveRun] = useState<WorkflowRunSummary | null>(null);
  const [workflowEvents, setWorkflowEvents] = useState<WorkflowEvent[]>([]);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [streamingResponse, setStreamingResponse] = useState("");

  const healthTone = dashboard?.system_health.status === "healthy" ? "text-emerald-300" : "text-amber-300";

  const runProgress = useMemo(() => {
    const latest = workflowEvents.at(-1);
    return latest?.progress ?? 0;
  }, [workflowEvents]);

  const login = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setEnterpriseError(null);
    try {
      const response = await fetch(`${backendBaseUrl}/api/v2/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!response.ok) {
        throw new Error("Login failed");
      }
      const payload = (await response.json()) as {
        access_token: string;
        refresh_token: string;
        user: { username: string; roles: string[] };
      };
      onAuthChange({
        accessToken: payload.access_token,
        refreshToken: payload.refresh_token,
        username: payload.user.username,
        roles: payload.user.roles,
      });
    } catch (error) {
      setEnterpriseError(error instanceof Error ? error.message : "Login failed");
    }
  };

  const loadDashboard = async () => {
    setEnterpriseError(null);
    try {
      const response = await fetch(`${backendBaseUrl}/api/v2/dashboard/overview`, {
        headers: authHeaders(auth),
      });
      if (!response.ok) {
        throw new Error("Unable to load dashboard");
      }
      const payload = (await response.json()) as DashboardOverview;
      setDashboard(payload);
    } catch (error) {
      setEnterpriseError(error instanceof Error ? error.message : "Failed to load dashboard");
    }
  };

  const createWorkflowRun = async () => {
    setEnterpriseError(null);
    try {
      const response = await fetch(`${backendBaseUrl}/api/v2/workflows/runs`, {
        method: "POST",
        headers: authHeaders(auth),
        body: JSON.stringify({ project_id: projectId, goal: projectGoal || `Build roadmap for ${projectName}` }),
      });
      if (!response.ok) {
        throw new Error("Failed to create workflow run");
      }
      const payload = (await response.json()) as { run: WorkflowRunSummary };
      setActiveRun(payload.run);
      setWorkflowEvents([]);
    } catch (error) {
      setEnterpriseError(error instanceof Error ? error.message : "Workflow creation failed");
    }
  };

  const runApprovalAction = async (action: "approve" | "reject" | "edit" | "resume") => {
    if (!activeRun) {
      return;
    }
    setEnterpriseError(null);
    try {
      const response = await fetch(`${backendBaseUrl}/api/v2/workflows/runs/${activeRun.run_id}/approval`, {
        method: "POST",
        headers: authHeaders(auth),
        body: JSON.stringify({ action, comment: `${action} via UI` }),
      });
      if (!response.ok) {
        throw new Error(`Approval action failed: ${action}`);
      }
      const payload = (await response.json()) as WorkflowRunSummary;
      setActiveRun(payload);
    } catch (error) {
      setEnterpriseError(error instanceof Error ? error.message : "Approval action failed");
    }
  };

  const watchRun = async () => {
    if (!activeRun) {
      return;
    }
    setEnterpriseError(null);

    try {
      const response = await fetch(`${backendBaseUrl}/api/v2/workflows/runs/${activeRun.run_id}/stream`, {
        headers: authHeaders(auth),
      });
      if (!response.ok || !response.body) {
        throw new Error("Unable to stream workflow events");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }
        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split("\n\n");
        buffer = chunks.pop() ?? "";

        for (const chunk of chunks) {
          const line = chunk.split("\n").find((entry) => entry.startsWith("data:"));
          if (!line) {
            continue;
          }
          const payloadText = line.replace("data:", "").trim();
          if (payloadText === "[DONE]") {
            continue;
          }
          try {
            const event = JSON.parse(payloadText) as WorkflowEvent;
            setWorkflowEvents((previous) => [...previous, event]);
          } catch {
            // Ignore malformed chunks from interrupted streams.
          }
        }
      }
    } catch (error) {
      setEnterpriseError(error instanceof Error ? error.message : "Stream failed");
    }
  };

  const loadChatMessages = async () => {
    try {
      const response = await fetch(`${backendBaseUrl}/api/v2/projects/${projectId}/chat/messages`, {
        headers: authHeaders(auth),
      });
      if (!response.ok) {
        throw new Error("Unable to load chat messages");
      }
      const payload = (await response.json()) as ChatMessage[];
      setChatMessages(payload);
    } catch (error) {
      setEnterpriseError(error instanceof Error ? error.message : "Chat history failed");
    }
  };

  const sendChat = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!chatInput.trim()) {
      return;
    }

    setStreamingResponse("");
    try {
      const response = await fetch(`${backendBaseUrl}/api/v2/projects/${projectId}/chat/messages`, {
        method: "POST",
        headers: authHeaders(auth),
        body: JSON.stringify({ message: chatInput, goal: projectGoal, stream: true }),
      });
      if (!response.ok || !response.body) {
        throw new Error("Unable to stream chat response");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assembled = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        const text = decoder.decode(value, { stream: true });
        for (const line of text.split("\n")) {
          if (!line.startsWith("data:")) {
            continue;
          }
          const token = line.replace("data:", "").trim();
          if (!token || token === "[DONE]") {
            continue;
          }
          assembled += `${token} `;
          setStreamingResponse(assembled);
        }
      }

      setChatInput("");
      await loadChatMessages();
    } catch (error) {
      setEnterpriseError(error instanceof Error ? error.message : "Chat send failed");
    }
  };

  return (
    <section className="space-y-4 rounded-2xl border border-zinc-800 bg-zinc-900/80 p-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-zinc-100">Enterprise Platform</h3>
          <p className="text-xs text-zinc-400">Dashboard, approvals, live timeline, analytics, and project chat workspace.</p>
        </div>
        {auth ? (
          <div className="rounded-lg border border-zinc-700 px-3 py-1.5 text-xs text-zinc-300">
            User: <span className="font-semibold text-zinc-100">{auth.username}</span>
          </div>
        ) : null}
      </header>

      {!auth ? (
        <form className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]" onSubmit={login}>
          <input
            className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100"
            onChange={(event) => setUsername(event.target.value)}
            placeholder="username"
            value={username}
          />
          <input
            className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100"
            onChange={(event) => setPassword(event.target.value)}
            placeholder="password"
            type="password"
            value={password}
          />
          <button className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white" type="submit">
            Login
          </button>
        </form>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <button className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-200" onClick={loadDashboard} type="button">
            Load Dashboard
          </button>
          <button className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-200" onClick={createWorkflowRun} type="button">
            Start Workflow (Approval Gate)
          </button>
          <button className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-200" onClick={watchRun} type="button">
            Watch Live Timeline
          </button>
          <button className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-200" onClick={loadChatMessages} type="button">
            Refresh Chat
          </button>
        </div>
      )}

      {enterpriseError ? (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs text-red-200">{enterpriseError}</div>
      ) : null}

      {dashboard ? (
        <section className="space-y-3 rounded-xl border border-zinc-800 bg-zinc-950/70 p-4">
          <h4 className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-400">Dashboard</h4>
          <div className="grid gap-3 md:grid-cols-4">
            <article className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
              <p className="text-xs text-zinc-400">Running Workflows</p>
              <p className="mt-2 text-xl font-semibold text-zinc-100">{dashboard.running_workflows}</p>
            </article>
            <article className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
              <p className="text-xs text-zinc-400">Completed Workflows</p>
              <p className="mt-2 text-xl font-semibold text-zinc-100">{dashboard.completed_workflows}</p>
            </article>
            <article className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
              <p className="text-xs text-zinc-400">Knowledge Documents</p>
              <p className="mt-2 text-xl font-semibold text-zinc-100">{dashboard.knowledge_statistics.document_count}</p>
            </article>
            <article className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
              <p className="text-xs text-zinc-400">Success Rate</p>
              <p className="mt-2 text-xl font-semibold text-zinc-100">{dashboard.execution_success_rate}%</p>
            </article>
          </div>
          <p className={`text-xs ${healthTone}`}>System Health: {dashboard.system_health.status} / DB: {dashboard.system_health.database}</p>
        </section>
      ) : null}

      {activeRun ? (
        <section className="space-y-3 rounded-xl border border-zinc-800 bg-zinc-950/70 p-4">
          <header className="flex flex-wrap items-center justify-between gap-2">
            <h4 className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-400">Approval Panel</h4>
            <div className="text-xs text-zinc-300">
              Run: <span className="font-mono">{activeRun.run_id}</span>
            </div>
          </header>

          <div className="grid gap-2 sm:grid-cols-4">
            <button className="rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-xs text-zinc-200" onClick={() => runApprovalAction("approve")} type="button">
              Approve
            </button>
            <button className="rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-xs text-zinc-200" onClick={() => runApprovalAction("reject")} type="button">
              Reject
            </button>
            <button className="rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-xs text-zinc-200" onClick={() => runApprovalAction("edit")} type="button">
              Edit
            </button>
            <button className="rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-xs text-zinc-200" onClick={() => runApprovalAction("resume")} type="button">
              Resume
            </button>
          </div>

          <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3 text-xs text-zinc-300">
            <p>Status: {activeRun.status}</p>
            <p>Approval State: {activeRun.approval_state}</p>
            <p>Current Agent: {activeRun.current_agent || "none"}</p>
            <p>Progress: {runProgress}%</p>
          </div>
        </section>
      ) : null}

      <section className="space-y-3 rounded-xl border border-zinc-800 bg-zinc-950/70 p-4">
        <h4 className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-400">Workflow Timeline & Execution Logs</h4>
        <div className="max-h-52 space-y-2 overflow-auto rounded-lg border border-zinc-800 bg-zinc-900/50 p-2 text-xs text-zinc-300">
          {workflowEvents.length === 0 ? (
            <p className="text-zinc-500">No live events yet.</p>
          ) : (
            workflowEvents.map((event) => (
              <article className="rounded-md border border-zinc-800 bg-zinc-950/80 p-2" key={event.id}>
                <p className="font-semibold text-zinc-100">{event.event_type}</p>
                <p>{event.message}</p>
                <p className="text-zinc-500">{new Date(event.created_at).toLocaleString()}</p>
              </article>
            ))
          )}
        </div>
      </section>

      <section className="grid gap-3 lg:grid-cols-2">
        <div className="space-y-3 rounded-xl border border-zinc-800 bg-zinc-950/70 p-4">
          <h4 className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-400">Project Settings</h4>
          <p className="text-sm text-zinc-300">Project: {projectName}</p>
          <p className="text-xs text-zinc-400">Use Project Settings in the sidebar above for provider and goal updates.</p>
        </div>
        <div className="space-y-3 rounded-xl border border-zinc-800 bg-zinc-950/70 p-4">
          <h4 className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-400">User Profile</h4>
          <p className="text-sm text-zinc-300">Username: {auth?.username ?? "Not signed in"}</p>
          <p className="text-xs text-zinc-400">Roles: {auth?.roles.join(", ") ?? "none"}</p>
        </div>
      </section>

      <section className="space-y-3 rounded-xl border border-zinc-800 bg-zinc-950/70 p-4">
        <h4 className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-400">AI Chat Workspace</h4>
        <form className="flex flex-col gap-2 sm:flex-row" onSubmit={sendChat}>
          <input
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100"
            onChange={(event) => setChatInput(event.target.value)}
            placeholder="Ask about this project, knowledge, workflow history, or next steps"
            value={chatInput}
          />
          <button className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white" type="submit">
            Send
          </button>
        </form>

        {streamingResponse ? (
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3 text-sm text-zinc-200">{streamingResponse}</div>
        ) : null}

        <div className="max-h-48 space-y-2 overflow-auto rounded-lg border border-zinc-800 bg-zinc-900/50 p-2 text-xs">
          {chatMessages.length === 0 ? (
            <p className="text-zinc-500">No chat history yet.</p>
          ) : (
            chatMessages.map((message) => (
              <article className="rounded-md border border-zinc-800 bg-zinc-950/70 p-2" key={message.id}>
                <p className="font-semibold text-zinc-200">{message.role}</p>
                <p className="mt-1 text-zinc-300">{message.content}</p>
              </article>
            ))
          )}
        </div>
      </section>
    </section>
  );
}
