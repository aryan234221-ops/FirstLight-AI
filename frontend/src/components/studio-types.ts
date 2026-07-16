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
