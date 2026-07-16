type StudioTopBarProps = {
  provider: string;
  connectionStatus: "Connected" | "Disconnected";
  darkMode: boolean;
  onToggleTheme: () => void;
};

export function StudioTopBar({
  provider,
  connectionStatus,
  darkMode,
  onToggleTheme,
}: StudioTopBarProps) {
  const connectionClass =
    connectionStatus === "Connected"
      ? "bg-emerald-500/20 text-emerald-300"
      : "bg-red-500/20 text-red-300";

  return (
    <header className="sticky top-0 z-10 rounded-2xl border border-zinc-800/80 bg-zinc-900/90 px-4 py-3 backdrop-blur sm:px-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-xl bg-emerald-500/20 text-emerald-300">FL</div>
          <div>
            <p className="text-sm text-zinc-400">Workspace</p>
            <h1 className="text-lg font-semibold text-zinc-100 sm:text-xl">FirstLight AI Studio</h1>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="rounded-lg border border-zinc-700 px-3 py-1.5 text-xs text-zinc-200">
            Provider: <span className="font-semibold">{provider}</span>
          </div>
          <div className={`rounded-lg px-3 py-1.5 text-xs ${connectionClass}`}>{connectionStatus}</div>
          <button
            className="rounded-lg border border-zinc-700 px-3 py-1.5 text-xs text-zinc-200 transition hover:border-zinc-500"
            onClick={onToggleTheme}
            type="button"
          >
            {darkMode ? "Light" : "Dark"} Theme
          </button>
        </div>
      </div>
    </header>
  );
}
