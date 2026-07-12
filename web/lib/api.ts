// Typed browser client for the Keyflow FastAPI. The web app calls it directly
// (CORS allows the web origin) using the Supabase access token as the Bearer
// credential — `api/supabase_auth.py` verifies it offline and maps the user's
// plan from public.profiles.

export const AUDIO_EXTENSIONS = [".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"];

export type JobStatus = {
  job_id: string;
  status: "queued" | "running" | "done" | "error";
  progress: number;
  total: number;
  cached_hits: number;
  error: string | null;
};

/** One row of the ordered set, as serialized by build_playlist_dataframe.
 *  Score columns are null on the opening track (NaN → null in JSON). */
export type PlaylistRow = {
  order: number;
  title: string;
  file: string;
  bpm: number;
  key: string;
  camelot: string;
  energy: number;
  onset_rate: number;
  transition_score_from_previous: number | null;
  harmonic_score: number | null;
  bpm_score: number | null;
  rhythm_score: number | null;
  onset_score: number | null;
  energy_score: number | null;
};

export function apiUrl(): string {
  return (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "");
}

export function isAudioFile(name: string): boolean {
  const dot = name.lastIndexOf(".");
  return dot >= 0 && AUDIO_EXTENSIONS.includes(name.slice(dot).toLowerCase());
}

/** FastAPI puts the human-readable message in `detail`. */
export async function apiDetail(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
  } catch {
    /* not JSON */
  }
  return `The engine answered ${res.status} ${res.statusText}.`;
}

export function formatBytes(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}
