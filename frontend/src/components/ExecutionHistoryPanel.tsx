import { ExecutionRecord } from "@/components/studio-types";

type ExecutionHistoryPanelProps = {
  records: ExecutionRecord[];
};

function formatDuration(durationMs: number): string {
  const seconds = (durationMs / 1000).toFixed(1);
  return `${seconds}s`;
}

export function ExecutionHistoryPanel({ records }: ExecutionHistoryPanelProps) {
  return (
    <section className="rounded-2xl border border-zinc-800 bg-zinc-900/80 p-4">
      <h3 className="text-sm font-semibold text-zinc-200">Execution History</h3>
      <div className="mt-3 max-h-[340px] space-y-3 overflow-auto pr-1">
        {records.length === 0 ? (
          <p className="text-sm text-zinc-500">No executions yet for this project.</p>
        ) : (
          records.map((record) => (
            <details className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3" key={record.id}>
              <summary className="cursor-pointer list-none">
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                  <span className="font-semibold text-zinc-100">{record.date}</span>
                  <span className="rounded-md border border-zinc-700 px-2 py-0.5 text-zinc-300">{record.workflow}</span>
                  <span
                    className={`rounded-md px-2 py-0.5 font-semibold ${
                      record.status === "completed" ? "bg-emerald-500/15 text-emerald-300" : "bg-red-500/15 text-red-300"
                    }`}
                  >
                    {record.status}
                  </span>
                  <span className="text-zinc-400">{formatDuration(record.durationMs)}</span>
                </div>
              </summary>

              {record.errorMessage ? (
                <p className="mt-2 text-sm text-red-300">{record.errorMessage}</p>
              ) : (
                <pre className="mt-2 overflow-auto rounded-lg bg-zinc-950 p-2 text-xs text-zinc-300">
                  {JSON.stringify(record.result, null, 2)}
                </pre>
              )}
            </details>
          ))
        )}
      </div>
    </section>
  );
}
