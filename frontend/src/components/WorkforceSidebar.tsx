import { Employee, EmployeeId } from "@/components/studio-types";

type WorkforceSidebarProps = {
  employees: Employee[];
  selectedEmployee: EmployeeId;
  onSelectEmployee: (employee: EmployeeId) => void;
};

const statusClassMap = {
  online: "bg-emerald-400",
  busy: "bg-amber-400",
  idle: "bg-zinc-500",
};

export function WorkforceSidebar({
  employees,
  selectedEmployee,
  onSelectEmployee,
}: WorkforceSidebarProps) {
  return (
    <aside className="rounded-2xl border border-zinc-800 bg-zinc-900/80 p-4 xl:w-70">
      <h2 className="mb-4 text-xs font-semibold uppercase tracking-[0.2em] text-zinc-400">AI Workforce</h2>
      <ul className="space-y-2">
        {employees.map((employee) => {
          const active = selectedEmployee === employee.id;
          return (
            <li key={employee.id}>
              <button
                className={`flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left transition ${
                  active
                    ? "bg-emerald-500/20 text-zinc-100 ring-1 ring-emerald-500/40"
                    : "bg-zinc-900 text-zinc-300 hover:bg-zinc-800"
                }`}
                onClick={() => onSelectEmployee(employee.id)}
                type="button"
              >
                <span className="flex items-center gap-2">
                  <span aria-hidden>{employee.icon}</span>
                  <span className="text-sm font-medium">{employee.name}</span>
                </span>
                <span className={`h-2.5 w-2.5 rounded-full ${statusClassMap[employee.status]}`} />
              </button>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
