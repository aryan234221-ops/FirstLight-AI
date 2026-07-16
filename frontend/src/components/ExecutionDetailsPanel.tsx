import { ExecutionMode } from "@/components/studio-types";

type ExecutionDetailsPanelProps = {
  mode: ExecutionMode;
  selectedAgentLabel: string;
  currentStep: string;
  status: "idle" | "running" | "completed" | "failed";
  elapsedMs: number;
};

const statusStyles = {
  idle: "text-zinc-400",
  running: "text-amber-300",
  completed: "text-emerald-300",
  failed: "text-red-300",
};

function formatElapsed(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
}

export function ExecutionDetailsPanel({
  mode,
  selectedAgentLabel,
  currentStep,
  status,
  elapsedMs,
}: ExecutionDetailsPanelProps) {
  return (
    <aside className="rounded-2xl border border-zinc-800 bg-zinc-900/80 p-4 xl:w-[320px]">
      <h2 className="mb-4 text-xs font-semibold uppercase tracking-[0.2em] text-zinc-400">Execution Details</h2>
      <dl className="space-y-4 text-sm">
        <div>
          <dt className="text-zinc-500">Current Workflow</dt>
          <dd className="mt-1 font-medium text-zinc-100">
            {mode === "agent" ? `Single Agent (${selectedAgentLabel})` : "CEO -> Architect"}
          </dd>
        </div>
        <div>
          <dt className="text-zinc-500">Execution Steps</dt>
          <dd className="mt-1 text-zinc-100">{mode === "agent" ? "1" : "2"}</dd>
        </div>
        <div>
          <dt className="text-zinc-500">Elapsed Time</dt>
          <dd className="mt-1 font-mono text-zinc-100">{formatElapsed(elapsedMs)}</dd>
        </div>
        <div>
          <dt className="text-zinc-500">Current AI Employee</dt>
          <dd className="mt-1 text-zinc-100">{currentStep || "None"}</dd>
        </div>
        <div>
          <dt className="text-zinc-500">Status</dt>
          <dd className={`mt-1 font-semibold capitalize ${statusStyles[status]}`}>{status}</dd>
        </div>
      </dl>

      <div className="mt-6 rounded-xl border border-dashed border-zinc-700 p-3">
        <p className="text-xs uppercase tracking-wide text-zinc-500">Future Telemetry</p>
        <ul className="mt-2 space-y-1 text-sm text-zinc-400">
          <li>Token usage: --</li>
          <li>Cost: --</li>
          <li>Latency: --</li>
        </ul>
      </div>
    </aside>
  );
}
