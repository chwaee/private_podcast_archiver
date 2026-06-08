"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

const API_BASE = "http://localhost:8000/api";

interface Episode {
  id: string;
  title: string;
  episode_number?: string;
  description?: string;
  ingestion_status: string;
  show_id: string;
  workspace_id: string;
}

interface Segment {
  segment_index: number;
  speaker: string | null;
  start_seconds: number | null;
  end_seconds: number | null;
  text: string;
}

interface Chunk {
  id: string;
  chunk_index: number;
  start_seconds: number | null;
  end_seconds: number | null;
  speaker_summary: string | null;
  text: string;
  token_count: number;
}

export default function EpisodeDetailPage() {
  const params = useParams<{ episodeId: string }>();
  const episodeId = params.episodeId;

  const [episode, setEpisode] = useState<Episode | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "transcript" | "chunks" | "exports" | "metadata">("overview");

  // Transcript state (from M3)
  const [segments, setSegments] = useState<Segment[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  // Chunks state (M4)
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestStatus, setIngestStatus] = useState<string | null>(null);

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

  async function fetchEpisode() {
    try {
      const res = await fetch(`${API_BASE}/episodes/${episodeId}`);
      if (res.ok) setEpisode(await res.json());
    } catch {}
  }

  async function loadSegments() {
    try {
      const res = await fetch(`${API_BASE}/episodes/${episodeId}/segments?limit=200`);
      if (res.ok) {
        const data = await res.json();
        setSegments(data.segments || []);
      }
    } catch {}
  }

  async function loadChunks() {
    try {
      const res = await fetch(`${API_BASE}/episodes/${episodeId}/chunks`);
      if (res.ok) {
        const data = await res.json();
        setChunks(data.chunks || []);
      }
    } catch {}
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
      const res = await fetch(`${API_BASE}/episodes/${episodeId}/transcript-files`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");

      setUploadStatus(`Uploaded: ${data.original_filename} → ${data.status}`);
      setWarnings(data.warnings || []);
      await loadSegments();
      await fetchEpisode();
    } catch (err: any) {
      setUploadStatus(`Error: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  }

  async function runIngestion() {
    setIsIngesting(true);
    setIngestStatus(null);
    try {
      const res = await fetch(`${API_BASE}/episodes/${episodeId}/ingest`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Ingestion failed");
      setIngestStatus(`Success: ${data.status} (${data.chunks_created || 0} chunks)`);
      await fetchEpisode();
      await loadChunks();
    } catch (err: any) {
      setIngestStatus(`Error: ${err.message}`);
    } finally {
      setIsIngesting(false);
    }
  }

  useEffect(() => {
    if (episodeId) {
      fetchEpisode();
      loadSegments();
      loadChunks();
    }
  }, [episodeId]);

  if (!episode) return <div className="text-zinc-400">Loading episode...</div>;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <Link href={`/shows/${episode.show_id}`} className="text-xs text-zinc-400 hover:text-zinc-200">← Back to Show</Link>
        <h1 className="text-2xl font-semibold tracking-tight mt-1">{episode.title}</h1>
        {episode.episode_number && <div className="text-sm text-zinc-400">Episode #{episode.episode_number}</div>}
        <div className="mt-1">
          Status: <span className="px-2 py-0.5 text-xs rounded bg-zinc-800">{episode.ingestion_status}</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-zinc-800 flex gap-4 text-sm">
        {(["overview", "transcript", "chunks", "exports", "metadata"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-2 capitalize ${activeTab === tab ? "border-b-2 border-white font-medium" : "text-zinc-400 hover:text-zinc-200"}`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === "overview" && (
        <div className="space-y-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
            <div className="font-medium mb-2">Quick Actions</div>
            <div className="flex gap-3">
              <button
                onClick={runIngestion}
                disabled={isIngesting}
                className="rounded bg-emerald-600 hover:bg-emerald-700 px-4 py-2 text-sm disabled:opacity-50"
              >
                {isIngesting ? "Ingesting..." : "Run Ingestion (M4)"}
              </button>
              <button
                onClick={() => setActiveTab("transcript")}
                className="rounded border border-zinc-700 px-4 py-2 text-sm hover:bg-zinc-800"
              >
                Upload Transcript (M3)
              </button>
            </div>
            {ingestStatus && <div className="mt-2 text-sm text-emerald-400">{ingestStatus}</div>}
          </div>
          <div className="text-sm text-zinc-400">Description: {episode.description || "—"}</div>
        </div>
      )}

      {activeTab === "transcript" && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="font-semibold">Transcript (M3)</div>
            <button
              onClick={() => (document.getElementById("ep-file-input") as HTMLInputElement)?.click()}
              disabled={isUploading}
              className="rounded bg-emerald-600 hover:bg-emerald-700 px-3 py-1 text-sm"
            >
              {isUploading ? "Uploading..." : "Upload File"}
            </button>
            <input
              id="ep-file-input"
              type="file"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleUpload(f);
                e.target.value = "";
              }}
              accept=".json,.csv,.txt,.vtt,.srt"
            />
          </div>

          {uploadStatus && <div className="text-sm text-emerald-400">{uploadStatus}</div>}
          {warnings.length > 0 && <div className="text-xs text-amber-300">Warnings: {warnings.join(" | ")}</div>}

          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search segments..."
            className="w-full bg-zinc-950 border border-zinc-700 rounded px-3 py-1 text-sm"
          />

          {segments.length === 0 ? (
            <div className="text-sm text-zinc-400 border border-dashed p-6 rounded text-center">No segments. Upload a transcript file.</div>
          ) : (
            <div className="border border-zinc-800 rounded max-h-[400px] overflow-auto text-sm">
              <table className="w-full">
                <thead className="bg-zinc-950 sticky top-0">
                  <tr className="text-xs text-zinc-400">
                    <th className="px-3 py-1.5 w-10">#</th>
                    <th className="px-3 py-1.5 w-24">Time</th>
                    <th className="px-3 py-1.5 w-28">Speaker</th>
                    <th className="px-3 py-1.5">Text</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800">
                  {filteredSegments.map((seg, i) => (
                    <tr key={i} className="hover:bg-zinc-950/50">
                      <td className="px-3 py-1.5 text-zinc-500">{seg.segment_index}</td>
                      <td className="px-3 py-1.5 font-mono text-xs">{formatTime(seg.start_seconds)}–{formatTime(seg.end_seconds)}</td>
                      <td className="px-3 py-1.5 text-xs text-emerald-300">{seg.speaker || "—"}</td>
                      <td className="px-3 py-1.5 text-zinc-200">{seg.text}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === "chunks" && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
          <div className="font-semibold mb-3">Chunks (M4)</div>
          {chunks.length === 0 ? (
            <div className="text-sm text-zinc-400">No chunks yet. Run ingestion from Overview.</div>
          ) : (
            <div className="space-y-2 text-sm">
              {chunks.map((c) => (
                <div key={c.id} className="border border-zinc-800 rounded p-3">
                  <div className="text-xs text-zinc-400">#{c.chunk_index} • {formatTime(c.start_seconds)}–{formatTime(c.end_seconds)} • {c.speaker_summary || "—"} • {c.token_count} tokens</div>
                  <div className="mt-1 text-zinc-200">{c.text}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === "exports" && (
        <div className="text-sm text-zinc-400">Exports (M7) — placeholder. Use the API once implemented.</div>
      )}

      {activeTab === "metadata" && (
        <div className="bg-zinc-900 border border-zinc-800 rounded p-4 text-sm space-y-1">
          <div>ID: {episode.id}</div>
          <div>Show ID: {episode.show_id}</div>
          <div>Workspace: {episode.workspace_id}</div>
          <div>Status: {episode.ingestion_status}</div>
        </div>
      )}
    </div>
  );
}
