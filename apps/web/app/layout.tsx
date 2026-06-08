import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Private Podcast Archive Copilot",
  description: "Ask your podcast archive anything. Private, cited, grounded in your transcripts.",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}
    >
      <body className="min-h-full flex bg-zinc-950 text-zinc-200">
        {/* M0 static sidebar shell (per PRODUCT_SPEC §8.2) */}
        <aside className="w-64 border-r border-zinc-800 bg-zinc-900 flex flex-col">
          <div className="px-4 py-5 border-b border-zinc-800">
            <div className="font-semibold tracking-tight text-lg">PPA Copilot</div>
            <div className="text-[10px] text-zinc-500 -mt-0.5">PRIVATE ARCHIVE</div>
          </div>

          <div className="px-3 pt-3">
            <div className="text-xs uppercase tracking-widest text-zinc-500 px-2 mb-1">Workspace</div>
            <div className="mx-2 mb-3 rounded bg-zinc-950 px-3 py-1.5 text-sm border border-zinc-800">
              Demo Workspace <span className="text-[10px] text-amber-400">(M2)</span>
            </div>
          </div>

          <nav className="px-2 text-sm flex-1">
            {[
              { label: "Dashboard", href: "/" },
              { label: "Shows", href: "/shows" },
              { label: "Search", href: "#" },
              { label: "Chat", href: "#" },
              { label: "Exports", href: "#" },
              { label: "Jobs", href: "#" },
              { label: "Settings", href: "#" },
            ].map((item) => (
              <Link
                key={item.label}
                href={item.href}
                className="block rounded px-3 py-2 mb-0.5 text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200"
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="p-3 text-[10px] text-zinc-500 border-t border-zinc-800">
            Milestone 2 • Show &amp; Episode UI<br />
            <span className="text-emerald-400">API health:</span> connected
          </div>
        </aside>

        <div className="flex-1 flex flex-col min-w-0">
          {/* Top bar */}
          <header className="h-12 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur flex items-center px-5 text-sm justify-between">
            <div className="font-medium text-zinc-400">Private Podcast Archive Copilot</div>
            <div className="flex items-center gap-3 text-xs">
              <div className="px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800">v0.1.0 (M2)</div>
              <div className="text-emerald-400">● Local</div>
            </div>
          </header>

          {/* Page content */}
          <main className="flex-1 overflow-auto p-6">
            {children}
          </main>

          <footer className="px-6 py-3 text-[10px] text-zinc-500 border-t border-zinc-800">
            Private Podcast Archive Copilot • All data scoped to workspace • See PRODUCT_SPEC.md
          </footer>
        </div>
      </body>
    </html>
  );
}
