"use client";

export default function DashboardPage() {
  const handleQuickAction = (action: string, milestone: string) => {
    alert(`${action} — available in ${milestone}.\n\n(M0 foundations only. See PRODUCT_SPEC.md)`);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Banner */}
      <div className="rounded-lg border border-amber-900/50 bg-amber-950/30 px-4 py-2 text-sm text-amber-300">
        <strong>Milestone 0 — Foundations only.</strong> Docker Compose, API health, and this UI shell are live.
        No data model, auth, ingestion or RAG yet. Follow the milestone plan in PRODUCT_SPEC.md.
      </div>

      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-zinc-400 mt-1">
          Overview for <span className="text-zinc-300">Demo Workspace</span>. All numbers are placeholders.
        </p>
      </div>

      {/* Stats row — per §8.3 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Shows", value: "0", hint: "M2+" },
          { label: "Episodes", value: "0", hint: "M2+" },
          { label: "Indexed", value: "0", hint: "M4+" },
          { label: "Transcript Hours", value: "0.0", hint: "M3+" },
        ].map((stat) => (
          <div key={stat.label} className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
            <div className="text-xs uppercase tracking-widest text-zinc-500">{stat.label}</div>
            <div className="mt-2 text-4xl font-semibold tabular-nums text-white">{stat.value}</div>
            <div className="text-[10px] text-zinc-500 mt-1">{stat.hint}</div>
          </div>
        ))}
      </div>

      {/* Quick actions — per §8.3 */}
      <div>
        <div className="text-sm font-medium text-zinc-400 mb-2">Quick actions</div>
        <div className="flex flex-wrap gap-3">
          {[
            { label: "Add Show", ms: "Milestone 2" },
            { label: "Add Episode", ms: "Milestone 2" },
            { label: "Upload Transcript", ms: "Milestone 3" },
            { label: "Ask Archive", ms: "Milestone 6" },
          ].map((qa) => (
            <button
              key={qa.label}
              onClick={() => handleQuickAction(qa.label, qa.ms)}
              className="rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm hover:bg-zinc-800 active:bg-zinc-950 transition"
            >
              {qa.label}
            </button>
          ))}
        </div>
        <p className="text-[11px] text-zinc-500 mt-2">These will open real forms and flows in later milestones.</p>
      </div>

      {/* Recent activity placeholders */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm font-medium">Recent ingestion jobs</div>
            <span className="text-[10px] px-1.5 py-px bg-zinc-800 rounded">M3+</span>
          </div>
          <div className="text-sm text-zinc-400 border border-dashed border-zinc-800 rounded p-6 text-center">
            No jobs yet.<br />Upload a transcript and run ingestion to see activity here.
          </div>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm font-medium">Recent chats</div>
            <span className="text-[10px] px-1.5 py-px bg-zinc-800 rounded">M6+</span>
          </div>
          <div className="text-sm text-zinc-400 border border-dashed border-zinc-800 rounded p-6 text-center">
            No conversations yet.<br />Archive chat with citations will appear after M6.
          </div>
        </div>
      </div>

      {/* Helpful note */}
      <div className="text-xs text-zinc-500 pt-2">
        API: <code className="bg-zinc-900 px-1 py-px rounded">http://localhost:8000/api/health</code> • 
        Check <code>docker compose logs</code> for backend. • Follow AGENTS.md and incremental milestones.
      </div>
    </div>
  );
}
