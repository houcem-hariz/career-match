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
