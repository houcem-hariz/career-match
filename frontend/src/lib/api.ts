export interface GapPayload {
  kind: string;
  skill_id: string | null;
  requirement: string | null;
  have: string | null;
  need: string | null;
  detail: string;
}

export interface SimulationPayload {
  course_id: string;
  title: string;
  skill_id: string;
  score_before: number;
  score_after: number;
  delta: number;
  bucket_before: string;
  bucket_after: string;
}

export interface CardPayload {
  rank: number;
  bucket: "eligible" | "reachable" | "out_of_reach";
  score: number;
  similarity: number;
  source_id: string;
  title: string;
  company: string | null;
  family: string;
  seniority: string;
  work_model: string;
  dimensions: Record<string, number>;
  mandatory_gap_count: number;
  gaps: GapPayload[];
  simulations: SimulationPayload[];
}

export interface MatchResponse {
  candidate_count: number;
  query_from_cache: boolean;
  cards: CardPayload[];
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function extractErrorMessage(res: Response): Promise<string> {
  try {
    const text = await res.text();
    try {
      const data = JSON.parse(text);
      if (data.detail) return data.detail;
      if (data.message) return data.message;
    } catch {
      // not JSON
    }
    if (res.status === 500) {
      return "Backend internal error. Please ensure GROQ_API_KEY and OPENAI_API_KEY are provided in your .env file, or check backend logs.";
    }
    return text || res.statusText || `Request failed with status ${res.status}`;
  } catch {
    return `Request failed with status ${res.status}`;
  }
}

export async function matchExample(example: string, k = 10): Promise<MatchResponse> {
  const res = await fetch(`/api/match?k=${k}`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ example }),
  });
  if (!res.ok) {
    const msg = await extractErrorMessage(res);
    throw new ApiError(res.status, msg);
  }
  return res.json();
}

export async function matchText(text: string, k = 10): Promise<MatchResponse> {
  const res = await fetch(`/api/match?k=${k}`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, k }),
  });
  if (!res.ok) {
    const msg = await extractErrorMessage(res);
    throw new ApiError(res.status, msg);
  }
  return res.json();
}

export async function matchPdf(file: File, k = 10): Promise<MatchResponse> {
  const form = new FormData();
  form.append("cv", file);
  const res = await fetch(`/api/match?k=${k}`, {
    method: "POST",
    credentials: "include",
    body: form,
  });
  if (!res.ok) {
    const msg = await extractErrorMessage(res);
    throw new ApiError(res.status, msg);
  }
  return res.json();
}

export async function listOffers(): Promise<MatchResponse | null> {
  const res = await fetch(`/api/offers`, { credentials: "include" });
  if (res.status === 404) return null;
  if (!res.ok) {
    const msg = await extractErrorMessage(res);
    throw new ApiError(res.status, msg);
  }
  return res.json();
}

export async function getOffer(sourceId: string): Promise<CardPayload | null> {
  const res = await fetch(`/api/offers/${sourceId}`, {
    credentials: "include",
  });
  if (res.status === 404) return null;
  if (!res.ok) {
    const msg = await extractErrorMessage(res);
    throw new ApiError(res.status, msg);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Profile (week 6). Pydantic serialises the backend IntEnums as numbers:
// seniority 1-4 (JUNIOR..LEAD), skill level 1-4 (AWARENESS..EXPERT),
// education level 0-4 (NONE..DOCTORATE), language proficiency 1-6 (A1..C2).
// ---------------------------------------------------------------------------

export type JobFamily =
  | "backend"
  | "frontend"
  | "data"
  | "devops"
  | "cybersecurity"
  | "technical_product";

export type WorkModel = "onsite" | "hybrid" | "remote";

export type ContractType =
  | "permanent"
  | "fixed_term"
  | "internship"
  | "apprenticeship"
  | "freelance";

export interface NormalizedSkill {
  skill_id: string;
  level: number;
  years_experience: number | null;
  source: "cv_extraction" | "user_input" | "inferred";
}

export interface Experience {
  title: string;
  family: JobFamily | null;
  duration_months: number;
  skill_labels: string[];
}

export interface EducationRecord {
  level: number;
  field_of_study: string | null;
}

export interface LanguageSkill {
  language_code: string;
  proficiency: number;
}

export interface WorkPreferences {
  locations: string[];
  contract_types: ContractType[];
  work_models: WorkModel[];
  willing_to_relocate: boolean;
}

export interface Profile {
  profile_id: string;
  source_cv_hash: string | null;
  first_name: string | null;
  target_title: string | null;
  target_families: JobFamily[];
  total_years_experience: number;
  seniority: number;
  skills: NormalizedSkill[];
  experiences: Experience[];
  education: EducationRecord[];
  languages: LanguageSkill[];
  preferences: WorkPreferences;
  user_edited: boolean;
  correction_count: number;
}

export async function getProfile(): Promise<Profile | null> {
  const res = await fetch(`/api/profile`, { credentials: "include" });
  if (res.status === 404) return null;
  if (!res.ok) {
    const msg = await extractErrorMessage(res);
    throw new ApiError(res.status, msg);
  }
  return res.json();
}

/** Saves the correction only. Call rematch() afterwards to rescore. */
export async function putProfile(profile: Profile): Promise<Profile> {
  const res = await fetch(`/api/profile`, {
    method: "PUT",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
  if (!res.ok) {
    const msg = await extractErrorMessage(res);
    throw new ApiError(res.status, msg);
  }
  return res.json();
}

export async function rematch(k = 10): Promise<MatchResponse> {
  const res = await fetch(`/api/rematch?k=${k}`, {
    method: "POST",
    credentials: "include",
  });
  if (!res.ok) {
    const msg = await extractErrorMessage(res);
    throw new ApiError(res.status, msg);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Auth (week 6): try first, account only to keep the profile.
// ---------------------------------------------------------------------------

export interface MeResponse {
  authenticated: boolean;
  email: string | null;
}

async function postAuth(path: string, email: string, password: string): Promise<MeResponse> {
  const res = await fetch(`/api/auth/${path}`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const msg = await extractErrorMessage(res);
    throw new ApiError(res.status, msg);
  }
  return res.json();
}

export function register(email: string, password: string): Promise<MeResponse> {
  return postAuth("register", email, password);
}

export function login(email: string, password: string): Promise<MeResponse> {
  return postAuth("login", email, password);
}

export async function logout(): Promise<void> {
  const res = await fetch(`/api/auth/logout`, {
    method: "POST",
    credentials: "include",
  });
  if (!res.ok && res.status !== 204) {
    const msg = await extractErrorMessage(res);
    throw new ApiError(res.status, msg);
  }
}

export async function getMe(): Promise<MeResponse> {
  const res = await fetch(`/api/auth/me`, { credentials: "include" });
  if (!res.ok) return { authenticated: false, email: null };
  return res.json();
}
