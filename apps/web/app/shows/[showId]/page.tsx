"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

const API_BASE = "http://localhost:8000/api";

interface Show {
  id: string;
  name: string;
  slug: string;
  description?: string;
}

interface Episode {
  id: string;
  title: string;
  episode_number?: string;
  ingestion_status: string;
  created_at: string;
}

export default function ShowDetailPage() {
  const params = useParams<{ showId: string }>();
  const router = useRouter();
  const showId = params.showId;

  const [show, setShow] = useState<Show | null>(null);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newEp, setNewEp] = useState({ title: "", episode_number: "", description: "" });
  const [creating, setCreating] = useState(false);

  // For editing the show
  const [showEdit, setShowEdit] = useState(false);
  const [editShow, setEditShow] = useState({ name: "", slug: "", description: "" });
  const [updating, setUpdating] = useState(false);

  async function fetchData() {
    setLoading(true);
    setError(null);
    try {
      const [showRes, epsRes] = await Promise.all([
        fetch(`${API_BASE}/shows/${showId}`),
        fetch(`${API_BASE}/episodes/shows/${showId}/episodes`),
      ]);
      if (!showRes.ok) throw new Error("Show not found");
      if (!epsRes.ok) throw new Error("Failed to load episodes");

      const showData = await showRes.json();
      const epsData = await epsRes.json();
      setShow(showData);
      setEpisodes(epsData.episodes || []);
      // Prefill edit form when show loads
      if (showData) {
        setEditShow({
          name: showData.name,
          slug: showData.slug,
          description: showData.description || "",
        });
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function createEpisode(e: React.FormEvent) {
    e.preventDefault();
    if (!newEp.title) return;
    setCreating(true);
    try {
      const res = await fetch(`${API_BASE}/episodes/shows/${showId}/episodes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newEp),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Create failed");
      }
      setNewEp({ title: "", episode_number: "", description: "" });
      setShowCreate(false);
      await fetchData();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setCreating(false);
    }
  }

  async function updateShow(e: React.FormEvent) {
    e.preventDefault();
    if (!editShow.name || !editShow.slug) return;
    setUpdating(true);
    try {
      const res = await fetch(`${API_BASE}/shows/${showId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(editShow),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Update failed");
      }
      setShowEdit(false);
      await fetchData();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setUpdating(false);
    }
  }

  async function deleteShow() {
    if (!confirm("Delete this show? This will also delete all its episodes (and their data).")) return;
    try {
      const res = await fetch(`${API_BASE}/shows/${showId}`, { method: "DELETE" });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Delete failed");
      }
      router.push("/shows");
    } catch (e: any) {
      setError(e.message);
    }
  }

  useEffect(() => {
    if (showId) fetchData();
  }, [showId]);

  if (loading) return <div className="text-zinc-400">Loading show...</div>;
  if (error || !show) return <div className="text-red-400">{error || "Show not found"}</div>;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <Link href="/shows" className="text-xs text-zinc-400 hover:text-zinc-200">← Back to Shows</Link>
        <h1 className="text-2xl font-semibold tracking-tight mt-1">{show.name}</h1>
        <div className="text-xs text-zinc-500">/{show.slug}</div>
        {show.description && <p className="text-sm text-zinc-400 mt-1">{show.description}</p>}
      </div>

      {/* Show edit/delete controls */}
      <div className="flex gap-3">
        <button
          onClick={() => {
            setShowEdit(!showEdit);
            if (!showEdit && show) {
              setEditShow({ name: show.name, slug: show.slug, description: show.description || "" });
            }
          }}
          className="rounded border border-zinc-700 px-3 py-1 text-sm hover:bg-zinc-800"
        >
          {showEdit ? "Cancel Edit" : "Edit Show"}
        </button>
        <button
          onClick={deleteShow}
          className="rounded border border-red-700 px-3 py-1 text-sm text-red-400 hover:bg-zinc-800"
        >
          Delete Show
        </button>
      </div>

      {showEdit && (
        <form onSubmit={updateShow} className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 space-y-3">
          <div>
            <label className="block text-xs font-medium text-zinc-400 mb-1">Show Name</label>
            <input
              type="text"
              value={editShow.name}
              onChange={(e) => setEditShow({ ...editShow, name: e.target.value })}
              className="w-full bg-zinc-950 border border-zinc-700 rounded px-3 py-2 text-sm"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-zinc-400 mb-1">Slug</label>
            <input
              type="text"
              value={editShow.slug}
              onChange={(e) => setEditShow({ ...editShow, slug: e.target.value })}
              className="w-full bg-zinc-950 border border-zinc-700 rounded px-3 py-2 text-sm font-mono"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-zinc-400 mb-1">Description (optional)</label>
            <textarea
              value={editShow.description}
              onChange={(e) => setEditShow({ ...editShow, description: e.target.value })}
              className="w-full bg-zinc-950 border border-zinc-700 rounded px-3 py-2 text-sm h-20"
            />
          </div>
          <button
            type="submit"
            disabled={updating}
            className="rounded bg-white text-black px-4 py-1.5 text-sm font-medium disabled:opacity-50"
          >
            {updating ? "Saving..." : "Save Changes"}
          </button>
        </form>
      )}

      <div className="flex items-center justify-between">
        <div className="text-lg font-medium">Episodes</div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="rounded-lg bg-emerald-600 hover:bg-emerald-700 px-4 py-1.5 text-sm font-medium"
        >
          {showCreate ? "Cancel" : "+ New Episode"}
        </button>
      </div>

      {showCreate && (
        <form onSubmit={createEpisode} className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 space-y-3">
          <input
            type="text"
            placeholder="Episode Title"
            value={newEp.title}
            onChange={(e) => setNewEp({ ...newEp, title: e.target.value })}
            className="w-full bg-zinc-950 border border-zinc-700 rounded px-3 py-2 text-sm"
            required
          />
          <div className="grid grid-cols-2 gap-3">
            <input
              type="text"
              placeholder="Episode # (optional)"
              value={newEp.episode_number}
              onChange={(e) => setNewEp({ ...newEp, episode_number: e.target.value })}
              className="bg-zinc-950 border border-zinc-700 rounded px-3 py-2 text-sm"
            />
            <input
              type="text"
              placeholder="Description (optional)"
              value={newEp.description}
              onChange={(e) => setNewEp({ ...newEp, description: e.target.value })}
              className="bg-zinc-950 border border-zinc-700 rounded px-3 py-2 text-sm"
            />
          </div>
          <button
            type="submit"
            disabled={creating}
            className="rounded bg-white text-black px-4 py-1.5 text-sm font-medium disabled:opacity-50"
          >
            {creating ? "Creating..." : "Create Episode"}
          </button>
        </form>
      )}

      {episodes.length === 0 ? (
        <div className="border border-dashed border-zinc-700 rounded-xl p-8 text-center text-sm text-zinc-400">
          No episodes yet for this show. Create one above.
        </div>
      ) : (
        <div className="space-y-2">
          {episodes.map((ep) => (
            <Link
              key={ep.id}
              href={`/episodes/${ep.id}`}
              className="flex items-center justify-between rounded-xl border border-zinc-800 bg-zinc-900 p-4 hover:border-zinc-700 transition"
            >
              <div>
                <div className="font-medium">{ep.title}</div>
                {ep.episode_number && <div className="text-xs text-zinc-500">#{ep.episode_number}</div>}
              </div>
              <div className="text-right">
                <div className="text-xs px-2 py-0.5 rounded bg-zinc-800 inline-block">{ep.ingestion_status}</div>
                <div className="text-[10px] text-zinc-500 mt-1">{new Date(ep.created_at).toLocaleDateString()}</div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
