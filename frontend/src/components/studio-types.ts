export type ExecutionMode = "agent" | "workflow";

export type EmployeeStatus = "online" | "busy" | "idle";

export type EmployeeId =
  | "ceo"
  | "architect"
  | "backend"
  | "frontend"
  | "qa"
  | "devops"
  | "documentation"
  | "database"
  | "security";

export type Employee = {
  id: EmployeeId;
  name: string;
  icon: string;
  status: EmployeeStatus;
};

export type Task = {
  title: string;
  description: string;
};

export type Plan = {
  goal: string;
  tasks: Task[];
};

export type WorkflowResult = {
  ceo: Plan;
  architect: Plan;
};

export type TimelineStatus = "started" | "completed" | "failed";

export type TimelineEvent = {
  id: string;
  step: string;
  agentName: string;
  status: TimelineStatus;
  at: string;
};

export type Project = {
  id: string;
  name: string;
  description: string;
  createdDate: string;
  lastRun: string | null;
  workflowType: ExecutionMode;
  preferredProvider: string;
  selectedAgent: EmployeeId;
  goalDraft: string;
};

export type ExecutionStatus = "completed" | "failed";

export type ExecutionRecord = {
  id: string;
  projectId: string;
  date: string;
  workflow: ExecutionMode;
  status: ExecutionStatus;
  durationMs: number;
  result: Plan | WorkflowResult | null;
  errorMessage: string | null;
};

export type KnowledgeDocumentMetadata = {
  id: string;
  projectId: string;
  name: string;
  size: number;
  type: string;
  uploadedDate: string;
  description: string;
};

export type KnowledgeUploadInput = {
  file: File;
  metadata: Omit<KnowledgeDocumentMetadata, "projectId">;
};

export type AuthSession = {
  accessToken: string;
  refreshToken: string;
  username: string;
  roles: string[];
};

export type DashboardOverview = {
  recent_projects: Array<{ id: string; name: string; description: string; updated_at: string }>;
  running_workflows: number;
  completed_workflows: number;
  agent_utilization: Array<{ agent: string; runs: number }>;
  knowledge_statistics: { document_count: number; project_count: number };
  execution_success_rate: number;
  recent_activity: Array<{ event_type: string; message: string; status: string; created_at: string; project_id: string | null }>;
  system_health: { status: string; database: string };
};

export type WorkflowRunSummary = {
  run_id: string;
  project_id: string;
  goal: string;
  status: string;
  approval_state: string;
  current_agent: string | null;
  estimated_ms: number;
  started_at: string;
  completed_at: string | null;
  duration_ms: number;
  error_message: string | null;
};

export type WorkflowEvent = {
  id: string;
  event_type: string;
  status: string;
  message: string;
  agent_name: string | null;
  progress: number;
  payload: Record<string, unknown>;
  created_at: string;
};

export type ChatMessage = {
  id: string;
  project_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
};

export const WORKFORCE: Employee[] = [
  { id: "ceo", name: "CEO", icon: "🧠", status: "online" },
  { id: "architect", name: "Architect", icon: "🏗", status: "online" },
  { id: "backend", name: "Backend", icon: "⚙", status: "idle" },
  { id: "frontend", name: "Frontend", icon: "🎨", status: "idle" },
  { id: "qa", name: "QA", icon: "🧪", status: "idle" },
  { id: "devops", name: "DevOps", icon: "🚀", status: "idle" },
  { id: "documentation", name: "Documentation", icon: "📚", status: "idle" },
  { id: "database", name: "Database", icon: "🗄", status: "idle" },
  { id: "security", name: "Security", icon: "🔒", status: "busy" },
];
