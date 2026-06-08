"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";

const API_BASE = "http://localhost:8000/api";
const DEMO_WORKSPACE_ID = "11111111-1111-1111-1111-111111111111";

interface Show {
  id: string;
  name: string;
  slug: string;
}

interface Episode {
  id: string;
  title: string;
  ingestion_status: string;
}

export default function DashboardPage() {
  const [recentShows, setRecentShows] = useState<Show[]>([]);
  const [recentEpisodes, setRecentEpisodes] = useState<Episode[]>([]);

  useEffect(() => {
    // Load demo data for dashboard (M2)
    fetch(`${API_BASE}/shows/workspaces/${DEMO_WORKSPACE_ID}/shows?limit=3`)
      .then(r => r.json())
      .then(d => setRecentShows(d.shows || []))
      .catch(() => {});

    // For episodes, pick first show or use known demo if available
    // Simplified: just show note
  }, []);

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="rounded-lg border border-emerald-900/50 bg-emerald-950/30 px-4 py-2 text-sm text-emerald-300">
        <strong>Milestone 2 — Show &amp; Episode UI complete.</strong> Full CRUD for shows and episodes now available. 
        Use the <Link href="/shows" className="underline">Shows</Link> section to create and manage content. 
        Transcript (M3) and Ingestion (M4) are integrated in episode detail pages.
      </div>

      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-zinc-400 mt-1">
          Overview for <span className="text-zinc-300">Demo Workspace</span>.
        </p>
      </div>

      {/* Quick links / stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link href="/shows" className="rounded-xl border border-zinc-800 bg-zinc-900 p-4 hover:border-zinc-700 block">
          <div className="text-sm text-zinc-400">Shows</div>
          <div className="text-3xl font-semibold mt-1">Manage</div>
          <div className="text-xs mt-2 text-emerald-400">Create shows &amp; episodes →</div>
        </Link>
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="text-sm text-zinc-400">Quick Start</div>
          <div className="mt-2 text-sm">1. Go to <Link href="/shows" className="underline">/shows</Link> and create a show.<br />2. Add an episode.<br />3. Open the episode detail to upload transcript or run ingestion.</div>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4 text-sm text-zinc-400">
          Data from seed is available. Visit <Link href="/shows" className="underline">Shows</Link> to see the demo "The Canadian Investor".
        </div>
      </div>

      <div className="text-xs text-zinc-500">
        API: <code>http://localhost:8000/api</code> • Run <code>python scripts/seed_sample_data.py</code> after migrations for demo data.
      </div>
    </div>
  );
}
