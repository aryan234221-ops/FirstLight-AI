import { Project } from "@/components/studio-types";

type ProjectSidebarProps = {
  projects: Project[];
  selectedProjectId: string | null;
  onSelectProject: (projectId: string) => void;
  onCreateProject: () => void;
  onRenameProject: (projectId: string) => void;
  onDeleteProject: (projectId: string) => void;
};

export function ProjectSidebar({
  projects,
  selectedProjectId,
  onSelectProject,
  onCreateProject,
  onRenameProject,
  onDeleteProject,
}: ProjectSidebarProps) {
  return (
    <aside className="rounded-2xl border border-zinc-800 bg-zinc-900/80 p-4 xl:w-70">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-400">Projects</h2>
        <button
          className="rounded-lg bg-emerald-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-emerald-500"
          onClick={onCreateProject}
          type="button"
        >
          + Create
        </button>
      </div>

      <ul className="space-y-2">
        {projects.map((project) => {
          const active = project.id === selectedProjectId;
          return (
            <li key={project.id}>
              <div
                className={`rounded-xl border p-3 transition ${
                  active
                    ? "border-emerald-500/60 bg-emerald-500/10"
                    : "border-zinc-800 bg-zinc-950/50 hover:border-zinc-700"
                }`}
              >
                <button className="w-full text-left" onClick={() => onSelectProject(project.id)} type="button">
                  <p className="truncate text-sm font-semibold text-zinc-100">{project.name}</p>
                  <p className="mt-1 line-clamp-2 text-xs text-zinc-400">{project.description || "No description"}</p>
                </button>
                <div className="mt-3 flex gap-2">
                  <button
                    className="rounded-md border border-zinc-700 px-2 py-1 text-[11px] text-zinc-300 hover:border-zinc-500"
                    onClick={() => onRenameProject(project.id)}
                    type="button"
                  >
                    Rename
                  </button>
                  <button
                    className="rounded-md border border-red-700/60 px-2 py-1 text-[11px] text-red-300 hover:border-red-500"
                    onClick={() => onDeleteProject(project.id)}
                    type="button"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
