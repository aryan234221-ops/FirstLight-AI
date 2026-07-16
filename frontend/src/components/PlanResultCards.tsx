import { Plan, WorkflowResult } from "@/components/studio-types";

type PlanResultCardsProps = {
  result: Plan | WorkflowResult;
};

function isWorkflowResult(result: Plan | WorkflowResult): result is WorkflowResult {
  return "ceo" in result && "architect" in result;
}

function PlanCard({ label, plan }: { label: string; plan: Plan }) {
  return (
    <details className="group rounded-2xl border border-zinc-700 bg-zinc-900/70 p-4 transition-all open:bg-zinc-900" open>
      <summary className="cursor-pointer list-none text-base font-semibold text-zinc-100">{label}</summary>
      <p className="mt-2 text-sm text-zinc-400">Goal: {plan.goal}</p>
      <div className="mt-3 space-y-3">
        {plan.tasks.map((task, index) => (
          <details
            className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3 transition-all duration-200 open:border-emerald-500/50"
            key={`${label}-${task.title}-${index}`}
          >
            <summary className="cursor-pointer list-none text-sm font-semibold text-zinc-100">{task.title}</summary>
            <p className="mt-2 text-sm text-zinc-300">{task.description}</p>
          </details>
        ))}
      </div>
    </details>
  );
}

export function PlanResultCards({ result }: PlanResultCardsProps) {
  if (isWorkflowResult(result)) {
    return (
      <div className="space-y-4">
        <PlanCard label="CEO Plan" plan={result.ceo} />
        <PlanCard label="Architect Plan" plan={result.architect} />
      </div>
    );
  }

  return <PlanCard label="Agent Plan" plan={result} />;
}
