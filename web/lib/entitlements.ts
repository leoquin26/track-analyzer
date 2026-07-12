// Plan entitlements — mirror of authcore.ENTITLEMENTS (Python). Keep in sync:
// the API enforces these server-side; the web only uses them for UI gating.
export type Role = "free" | "pro" | "lifetime";

export const ROLE_LABELS: Record<Role, string> = {
  free: "Free",
  pro: "Pro",
  lifetime: "Lifetime",
};

export const ENTITLEMENTS: Record<
  Role,
  { maxTracks: number | null; energyCurve: boolean; discover: boolean; djExport: boolean }
> = {
  free: { maxTracks: 50, energyCurve: false, discover: false, djExport: false },
  pro: { maxTracks: null, energyCurve: true, discover: true, djExport: true },
  lifetime: { maxTracks: null, energyCurve: true, discover: true, djExport: true },
};

export function asRole(value: unknown): Role {
  return value === "pro" || value === "lifetime" ? value : "free";
}
