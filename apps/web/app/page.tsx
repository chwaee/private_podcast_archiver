"use client";

import React, { useState } from "react";

// Fixed demo episode from M3 seed (for upload + viewer testing)
const DEMO_EPISODE_ID = "33333333-3333-3333-3333-333333333333";
const API_BASE = "http://localhost:8000/api";

interface Segment {
  id?: string;
  segment_index: number;
  speaker: string | null;
  start_seconds: number | null;
  end_seconds: number | null;
  text: string;
}

export default function DashboardPage() {
  const [segments, setSegments] = useState<Segment[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [episodeInfo, setEpisodeInfo] = useState<any>(null);

  const filteredSegments = segments.filter((seg) => {
    const q = search.toLowerCase();
    return (
      seg.text.toLowerCase().includes(q) ||
      (seg.speaker || "").toLowerCase().includes(q)
    );
  });

  const formatTime = (sec: number | null) => {
    if (sec == null) return "--:--";
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  async function loadEpisodeInfo() {
    try {
      const res = await fetch(`${API_BASE}/episodes/${DEMO_EPISODE_ID}`);
      if (res.ok) {
        setEpisodeInfo(await res.json());
      }
    } catch (e) {
      // ignore for demo
    }
  }

  async function handleUpload(file: File | null) {
    if (!file) return;
    setIsUploading(true);
    setUploadStatus(null);
    setWarnings([]);
    setSegments([]);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(
        `${API_BASE}/episodes/${DEMO_EPISODE_ID}/transcript-files`,
        { method: "POST", body: formData }
      );
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Upload failed");
      }

      setUploadStatus(`Uploaded: ${data.original_filename} → ${data.status}`);
      setWarnings(data.warnings || []);

      // auto load segments
      await loadSegments();
      await loadEpisodeInfo();
    } catch (err: any) {
      setUploadStatus(`Error: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  }

  async function loadSegments() {
    try {
      const res = await fetch(
        `${API_BASE}/episodes/${DEMO_EPISODE_ID}/segments?limit=200`
      );
      if (res.ok) {
        const data = await res.json();
        setSegments(data.segments || []);
      }
    } catch (e) {
      // demo only
    }
  }

  // Quick action now functional for M3
  const handleQuickAction = (action: string) => {
    if (action === "Upload Transcript") {
      // trigger file input
      const input = document.getElementById("m3-file-input") as HTMLInputElement;
      input?.click();
    } else {
      alert(`${action} — will be available in a future milestone.\n\nSee PRODUCT_SPEC.md`);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Banner - updated for M3 */}
      <div className="rounded-lg border border-emerald-900/50 bg-emerald-950/30 px-4 py-2 text-sm text-emerald-300">
        <strong>Milestone 3 — Transcript Upload &amp; Parsing.</strong> Upload supported formats (JSON/CSV/TXT/VTT/SRT). 
        Segments are normalized, stored, and displayed with citations-ready timestamps. Demo episode pre-seeded.
      </div>

      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-zinc-400 mt-1">
          Overview for <span className="text-zinc-300">Demo Workspace</span> (M3 enabled).
        </p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Shows", value: "1", hint: "demo" },
          { label: "Episodes", value: "1", hint: "demo" },
          { label: "Indexed", value: "0", hint: "M4+" },
          { label: "Transcript Hours", value: "0.0", hint: "M3" },
        ].map((stat) => (
          <div key={stat.label} className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
            <div className="text-xs uppercase tracking-widest text-zinc-500">{stat.label}</div>
            <div className="mt-2 text-4xl font-semibold tabular-nums text-white">{stat.value}</div>
            <div className="text-[10px] text-zinc-500 mt-1">{stat.hint}</div>
          </div>
        ))}
      </div>

      {/* Quick actions - Upload now works */}
      <div>
        <div className="text-sm font-medium text-zinc-400 mb-2">Quick actions</div>
        <div className="flex flex-wrap gap-3">
          {[
            { label: "Add Show", ms: "M2" },
            { label: "Add Episode", ms: "M2" },
            { label: "Upload Transcript", ms: "M3" },
            { label: "Ask Archive", ms: "M6" },
          ].map((qa) => (
            <button
              key={qa.label}
              onClick={() => handleQuickAction(qa.label)}
              className="rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm hover:bg-zinc-800 active:bg-zinc-950 transition disabled:opacity-50"
              disabled={isUploading && qa.label.includes("Upload")}
            >
              {qa.label}
            </button>
          ))}
        </div>
        <p className="text-[11px] text-zinc-500 mt-2">
          "Upload Transcript" opens the M3 demo below. Use the sample JSON from <code>data/sample/</code>.
        </p>
      </div>

      {/* M3: Transcript Upload + Viewer (main deliverable) */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-lg font-semibold">M3 Demo: Transcript Upload &amp; Viewer</div>
            <div className="text-xs text-zinc-500">Episode: The Biggest Financial Mistake I Ever Made (fixed demo ID)</div>
          </div>
          <button
            onClick={loadSegments}
            className="text-xs px-3 py-1 rounded border border-zinc-700 hover:bg-zinc-800"
          >
            Reload Segments
          </button>
        </div>

        {/* Upload controls */}
        <div className="flex items-center gap-3">
          <input
            id="m3-file-input"
            type="file"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleUpload(f);
              e.target.value = ""; // allow re-select same file
            }}
            accept=".json,.csv,.txt,.vtt,.srt"
          />
          <button
            onClick={() => (document.getElementById("m3-file-input") as HTMLInputElement)?.click()}
            disabled={isUploading}
            className="rounded bg-emerald-600 hover:bg-emerald-700 px-4 py-2 text-sm font-medium disabled:opacity-60"
          >
            {isUploading ? "Uploading & Parsing..." : "Choose & Upload Transcript File"}
          </button>
          <span className="text-xs text-zinc-500">JSON / CSV / TXT / VTT / SRT supported</span>
        </div>

        {uploadStatus && (
          <div className="text-sm text-emerald-400">{uploadStatus}</div>
        )}
        {warnings.length > 0 && (
          <div className="text-xs bg-amber-950/40 border border-amber-900 p-2 rounded text-amber-300">
            Warnings: {warnings.join(" | ")}
          </div>
        )}

        {/* Search + Viewer */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search transcript (text or speaker)..."
              className="flex-1 bg-zinc-950 border border-zinc-700 rounded px-3 py-1 text-sm focus:outline-none focus:border-zinc-500"
            />
            <span className="text-xs text-zinc-500">{filteredSegments.length} / {segments.length} segments</span>
          </div>

          {segments.length === 0 ? (
            <div className="border border-dashed border-zinc-700 rounded p-8 text-center text-sm text-zinc-400">
              No segments loaded yet. Upload a transcript file above (try the sample JSON).
            </div>
          ) : (
            <div className="border border-zinc-800 rounded overflow-hidden max-h-[420px] overflow-y-auto text-sm">
              <table className="w-full">
                <thead className="bg-zinc-950 sticky top-0">
                  <tr className="text-left text-xs text-zinc-400">
                    <th className="px-3 py-2 w-12">#</th>
                    <th className="px-3 py-2 w-28">Time</th>
                    <th className="px-3 py-2 w-32">Speaker</th>
                    <th className="px-3 py-2">Text</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800">
                  {filteredSegments.map((seg, idx) => (
                    <tr key={idx} className="hover:bg-zinc-950/60">
                      <td className="px-3 py-2 text-zinc-500 tabular-nums">{seg.segment_index}</td>
                      <td className="px-3 py-2 font-mono text-xs text-zinc-400">
                        {formatTime(seg.start_seconds)}–{formatTime(seg.end_seconds)}
                      </td>
                      <td className="px-3 py-2 text-xs text-emerald-300">{seg.speaker || "—"}</td>
                      <td className="px-3 py-2 text-zinc-200">{seg.text}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <p className="mt-2 text-[10px] text-zinc-500">
            Segments are stored with timestamps and linked to the episode. Ready for citation in chat/exports (M5+).
          </p>
        </div>
      </div>

      {/* Recent / placeholders updated for M3 */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm font-medium">Recent ingestion jobs</div>
            <span className="text-[10px] px-1.5 py-px bg-zinc-800 rounded">M3+</span>
          </div>
          <div className="text-sm text-zinc-400 border border-dashed border-zinc-800 rounded p-6 text-center">
            Upload complete → status updated on episode. Full job tracking in M4.
          </div>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm font-medium">Transcript Viewer (M3)</div>
          </div>
          <div className="text-sm text-zinc-400">
            Searchable, timestamped segments from uploaded files. Click timestamps in future versions will seek audio.
          </div>
        </div>
      </div>

      <div className="text-xs text-zinc-500 pt-2">
        API base: <code className="bg-zinc-900 px-1 py-px rounded">http://localhost:8000/api</code> • 
        Demo episode ID: <code>{DEMO_EPISODE_ID}</code> • Run seed after migrations for data.
      </div>
    </div>
  );
}
