"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";

const API_BASE = "http://localhost:8000/api";
const DEMO_WORKSPACE_ID = "11111111-1111-1111-1111-111111111111";

interface Show {
  id: string;
  name: string;
  slug: string;
  description?: string;
  created_at: string;
}

export default function ShowsPage() {
  const [shows, setShows] = useState<Show[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newShow, setNewShow] = useState({ name: "", slug: "", description: "" });
  const [creating, setCreating] = useState(false);

  async function fetchShows() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/shows/workspaces/${DEMO_WORKSPACE_ID}/shows`);
      if (!res.ok) throw new Error("Failed to load shows");
      const data = await res.json();
      setShows(data.shows || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function createShow(e: React.FormEvent) {
    e.preventDefault();
    if (!newShow.name || !newShow.slug) return;
    setCreating(true);
    try {
      const res = await fetch(`${API_BASE}/shows/workspaces/${DEMO_WORKSPACE_ID}/shows`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newShow),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Create failed");
      }
      setNewShow({ name: "", slug: "", description: "" });
      setShowCreateForm(false);
      await fetchShows();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setCreating(false);
    }
  }

  useEffect(() => {
    fetchShows();
  }, []);

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Shows</h1>
          <p className="text-zinc-400">Manage your podcast shows (M2)</p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="rounded-lg bg-emerald-600 hover:bg-emerald-700 px-4 py-2 text-sm font-medium"
        >
          {showCreateForm ? "Cancel" : "+ New Show"}
        </button>
      </div>

      {error && (
        <div className="bg-red-950/40 border border-red-900 text-red-300 p-3 rounded text-sm">{error}</div>
      )}

      {showCreateForm && (
        <form onSubmit={createShow} className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <input
              type="text"
              placeholder="Show Name"
              value={newShow.name}
              onChange={(e) => setNewShow({ ...newShow, name: e.target.value })}
              className="bg-zinc-950 border border-zinc-700 rounded px-3 py-2 text-sm"
              required
            />
            <input
              type="text"
              placeholder="Slug (e.g. my-podcast)"
              value={newShow.slug}
              onChange={(e) => setNewShow({ ...newShow, slug: e.target.value })}
              className="bg-zinc-950 border border-zinc-700 rounded px-3 py-2 text-sm"
              required
            />
          </div>
          <textarea
            placeholder="Description (optional)"
            value={newShow.description}
            onChange={(e) => setNewShow({ ...newShow, description: e.target.value })}
            className="w-full bg-zinc-950 border border-zinc-700 rounded px-3 py-2 text-sm h-20"
          />
          <button
            type="submit"
            disabled={creating}
            className="rounded bg-white text-black px-4 py-1.5 text-sm font-medium disabled:opacity-50"
          >
            {creating ? "Creating..." : "Create Show"}
          </button>
        </form>
      )}

      {loading ? (
        <div className="text-zinc-400">Loading shows...</div>
      ) : shows.length === 0 ? (
        <div className="border border-dashed border-zinc-700 rounded-xl p-8 text-center text-sm text-zinc-400">
          No shows yet. Create one above or run the seed script.
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {shows.map((show) => (
            <Link
              key={show.id}
              href={`/shows/${show.id}`}
              className="block rounded-xl border border-zinc-800 bg-zinc-900 p-4 hover:border-zinc-700 transition"
            >
              <div className="font-semibold text-lg">{show.name}</div>
              <div className="text-xs text-zinc-500 mt-0.5">/{show.slug}</div>
              {show.description && (
                <div className="text-sm text-zinc-400 mt-2 line-clamp-2">{show.description}</div>
              )}
              <div className="text-[10px] text-zinc-500 mt-3">Created {new Date(show.created_at).toLocaleDateString()}</div>
            </Link>
          ))}
        </div>
      )}

      <div className="text-xs text-zinc-500 pt-4">
        Demo workspace: {DEMO_WORKSPACE_ID} • Seed data available after running seed_sample_data.py
      </div>
    </div>
  );
}
