import Link from "next/link";
import CamelotWheel from "@/components/CamelotWheel";

const FEATURES = [
  {
    title: "Harmonic keys",
    body: "Every track gets a musical key and Camelot code, so blends stay in tune instead of clashing.",
    icon: <path d="M3 4h18v16H3zM8 4v10M16 4v10M12 4v7" />,
  },
  {
    title: "Groove match",
    body: "A rhythm fingerprint and onset density line up tracks that actually feel alike, not just share a key.",
    icon: <path d="M3 12v.01M7 8v8M11 5v14M15 9v6M21 12v.01M19 10v4" />,
  },
  {
    title: "Energy flow",
    body: "Order the set as a build-up or a plateau, and reshape it live — no re-analysis.",
    icon: (
      <>
        <path d="M3 17c3-1 4-6 7-6s4 4 7 3 4-6 4-6" />
        <circle cx="3" cy="17" r="1.2" />
      </>
    ),
  },
  {
    title: "Live control",
    body: "Weight what matters for your mix and reorder by hand; the set updates the moment you change it.",
    icon: (
      <>
        <path d="M4 8h16M4 16h16" />
        <circle cx="9" cy="8" r="2.2" />
        <circle cx="15" cy="16" r="2.2" />
      </>
    ),
  },
];

const STATS: [string, string][] = [
  ["24", "Camelot keys"],
  ["5", "Mix signals"],
  ["0", "Uploads needed"],
  ["∞", "Library size"],
];

const STEPS: [string, string, string][] = [
  ["01", "Point at a folder", "Choose any folder of songs — mp3, wav, flac, m4a, aac, ogg. Subfolders optional."],
  ["02", "Analyze", "Each track is read for BPM, key, groove, and energy. Results are cached, so it only runs once."],
  ["03", "Shape & export", "Reorder live, then export CSV, M3U, or your DJ software's own format."],
];

const PLANS = [
  {
    name: "Free",
    price: "$0",
    per: "forever",
    desc: "Try the full engine on a small crate.",
    feats: ["Up to 50 tracks", "Harmonic ordering", "CSV + M3U export", "Live reordering"],
    featured: false,
    cta: "Start free",
  },
  {
    name: "Pro",
    price: "$12",
    per: "/ month",
    desc: "For working DJs with a real library.",
    feats: [
      "Unlimited tracks",
      "rekordbox · Serato · Traktor export",
      "Key + BPM written to tags",
      "Energy-curve set builder",
      "Similar-track discovery",
    ],
    featured: true,
    cta: "Go Pro",
  },
  {
    name: "Lifetime",
    price: "$149",
    per: "once",
    desc: "Pay once, own it. Limited early-bird.",
    feats: ["Everything in Pro", "All future updates", "Founder's badge", "Priority feature requests"],
    featured: false,
    cta: "Get lifetime",
  },
];

function Kicker({ children }: { children: React.ReactNode }) {
  return <div className="font-mono text-[0.72rem] uppercase tracking-[0.28em] text-mint">{children}</div>;
}

export default function Home() {
  return (
    <main className="mx-auto max-w-[1120px] px-5 pb-24 pt-6">
      {/* Navbar */}
      <nav className="animate-rise flex items-center justify-between rounded-full border border-line bg-[rgba(24,20,30,0.72)] py-2 pl-5 pr-2 backdrop-blur-md">
        <div className="flex items-center gap-2 font-display text-lg font-extrabold tracking-tight">
          <span className="h-3.5 w-3.5 rounded-full bg-[conic-gradient(from_0deg,#5eead4,#a78bfa,#f2a6c9,#f5d98f,#5eead4)]" />
          Keyflow
        </div>
        <div className="hidden items-center gap-8 font-mono text-[0.8rem] text-[color:var(--muted)] sm:flex">
          <a href="#capabilities" className="transition-colors hover:text-mint">Capabilities</a>
          <a href="#how" className="transition-colors hover:text-mint">How it works</a>
          <a href="#pricing" className="transition-colors hover:text-mint">Pricing</a>
        </div>
        <Link href="/app" className="rounded-full bg-ink px-4 py-2 text-sm font-semibold text-bg transition-transform hover:-translate-y-0.5">
          Open Keyflow →
        </Link>
      </nav>

      {/* Hero */}
      <section className="mt-14 grid items-center gap-10 md:grid-cols-[1.05fr_0.95fr]">
        <div className="animate-rise">
          <span className="inline-block rounded-full border border-line bg-surface px-3 py-1 font-mono text-[0.72rem] uppercase tracking-[0.28em] text-[color:var(--muted)]">
            Keyflow · harmonic mixing engine · <b className="text-mint">local &amp; private</b>
          </span>
          <h1 className="mt-6 font-display text-[clamp(2.9rem,5.6vw,4.6rem)] font-extrabold leading-[0.98] tracking-tight">
            Sets that flow
            <br />
            <span className="bg-gradient-to-r from-mint via-lavender to-[#f2a6c9] bg-clip-text text-transparent">in key.</span>
          </h1>
          <p className="mt-5 max-w-lg text-lg text-[color:var(--muted)]">
            Keyflow turns any folder of songs into a DJ set that flows — ordered by key, tempo, groove, and energy for transitions that just land.
          </p>
          <Link href="/app" className="mt-6 inline-block rounded-xl bg-ink px-6 py-3 font-semibold text-bg transition-transform hover:-translate-y-0.5">
            Open Keyflow →
          </Link>
          <p className="mt-6 font-mono text-[0.78rem] text-[color:var(--faint)]">No upload · your tracks never leave your machine.</p>
        </div>
        <div className="relative mx-auto w-full max-w-[440px] animate-rise">
          <div className="wheel-halo absolute inset-[-6%] rounded-full opacity-30 blur-[40px] [animation:spin_26s_linear_infinite] [background:conic-gradient(from_0deg,#5eead4,#a78bfa,#f2a6c9,#f5d98f,#5eead4)]" />
          <CamelotWheel />
        </div>
      </section>

      {/* Stats */}
      <section className="mt-20 grid grid-cols-2 gap-6 border-y border-line py-8 sm:grid-cols-4">
        {STATS.map(([n, l]) => (
          <div key={l} className="text-center">
            <div className="font-display text-4xl font-extrabold">{n}</div>
            <div className="mt-1 font-mono text-[0.72rem] uppercase tracking-[0.18em] text-[color:var(--faint)]">{l}</div>
          </div>
        ))}
      </section>

      {/* Capabilities */}
      <section id="capabilities" className="mt-24">
        <Kicker>What it does</Kicker>
        <h2 className="mt-1 font-display text-[clamp(1.7rem,3vw,2.4rem)] font-bold tracking-tight">Four signals, one seamless set</h2>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((f) => (
            <div key={f.title} className="rounded-2xl border border-line bg-surface p-6 transition-all hover:-translate-y-1 hover:border-mint/40">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" className="h-6 w-6 text-mint">
                {f.icon}
              </svg>
              <h3 className="mt-4 font-semibold">{f.title}</h3>
              <p className="mt-1 text-sm text-[color:var(--muted)]">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="mt-24">
        <Kicker>How it works</Kicker>
        <h2 className="mt-1 font-display text-[clamp(1.7rem,3vw,2.4rem)] font-bold tracking-tight">From folder to flawless set</h2>
        <div className="mt-8 grid gap-8 md:grid-cols-3">
          {STEPS.map(([num, title, body]) => (
            <div key={num} className="border-t border-line pt-4">
              <div className="font-display text-3xl font-extrabold text-mint">{num}</div>
              <h4 className="mt-1 font-semibold">{title}</h4>
              <p className="mt-1 text-sm text-[color:var(--muted)]">{body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="mt-24">
        <div className="text-center">
          <Kicker>Pricing</Kicker>
          <h2 className="mt-1 font-display text-[clamp(1.7rem,3vw,2.4rem)] font-bold tracking-tight">Start free. Upgrade when it earns you gigs.</h2>
          <p className="mx-auto mt-2 max-w-xl text-[color:var(--muted)]">Analysis runs locally, so your library stays private on every plan.</p>
        </div>
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {PLANS.map((p) => (
            <div key={p.name} className={`flex flex-col rounded-2xl border p-6 ${p.featured ? "border-mint/45 bg-mint/[0.05]" : "border-line bg-surface"}`}>
              {p.featured && (
                <span className="mb-3 self-start rounded-full border border-mint/30 px-2 py-0.5 font-mono text-[0.62rem] uppercase tracking-widest text-mint">
                  Most popular
                </span>
              )}
              <div className="font-display text-xl font-bold">{p.name}</div>
              <div className="mt-2">
                <span className="font-display text-4xl font-extrabold">{p.price}</span>{" "}
                <span className="font-mono text-sm text-[color:var(--faint)]">{p.per}</span>
              </div>
              <p className="mt-2 min-h-[2.5rem] text-sm text-[color:var(--muted)]">{p.desc}</p>
              <ul className="mb-6 mt-2 space-y-2 text-sm text-[color:var(--muted)]">
                {p.feats.map((feat) => (
                  <li key={feat} className="relative pl-5 before:absolute before:left-0 before:font-bold before:text-mint before:content-['+']">
                    {feat}
                  </li>
                ))}
              </ul>
              <Link
                href="/app"
                className={`mt-auto rounded-xl px-4 py-2.5 text-center text-sm font-semibold transition-transform hover:-translate-y-0.5 ${
                  p.featured ? "bg-ink text-bg" : "border border-line bg-surface-2 text-ink hover:border-mint/45"
                }`}
              >
                {p.cta} →
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-24 rounded-3xl border border-line bg-[radial-gradient(ellipse_60%_120%_at_50%_0%,rgba(167,139,250,0.15),transparent_60%)] px-6 py-12 text-center">
        <h3 className="font-display text-[clamp(1.6rem,3vw,2.3rem)] font-bold">Ready to build your set?</h3>
        <p className="mt-2 text-[color:var(--muted)]">Point it at your library and let the wheel do the sequencing.</p>
        <Link href="/app" className="mt-6 inline-block rounded-xl bg-ink px-6 py-3 font-semibold text-bg transition-transform hover:-translate-y-0.5">
          Open Keyflow →
        </Link>
        <p className="mt-8 font-mono text-xs text-[color:var(--faint)]">Keyflow · sets that flow in key · keyflow.dj</p>
      </footer>
    </main>
  );
}
