import Link from "next/link";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col justify-center px-5 py-10">
      <Link
        href="/"
        className="mb-8 flex items-center justify-center gap-2 font-display text-xl font-extrabold tracking-tight"
      >
        <span className="h-4 w-4 rounded-full bg-[conic-gradient(from_0deg,#5eead4,#a78bfa,#f2a6c9,#f5d98f,#5eead4)]" />
        Keyflow
      </Link>
      <div className="animate-rise rounded-2xl border border-line bg-surface p-8">{children}</div>
      <p className="mt-6 text-center font-mono text-xs text-[color:var(--faint)]">
        Sets that flow in key · keyflow.dj
      </p>
    </main>
  );
}
