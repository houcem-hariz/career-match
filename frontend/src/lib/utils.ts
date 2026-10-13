import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function bucketLabel(bucket: string): string {
  switch (bucket) {
    case "eligible":
      return "Eligible";
    case "reachable":
      return "Reachable";
    case "out_of_reach":
      return "Out of Reach";
    default:
      return bucket;
  }
}

export function bucketDescription(bucket: string): string {
  switch (bucket) {
    case "eligible":
      return "Ready to apply immediately. All mandatory skills and seniority requirements are fully satisfied.";
    case "reachable":
      return "Attainable with targeted upskilling. At most 2 mandatory skill gaps and suitable seniority baseline.";
    case "out_of_reach":
      return "Requires significant experience or fundamental stack transition. Key mandatory qualifications are missing.";
    default:
      return "";
  }
}

export function bucketStyles(bucket: string) {
  switch (bucket) {
    case "eligible":
      return {
        badge: "bg-emerald-50 text-emerald-700 border-emerald-200 ring-emerald-500/20",
        pill: "bg-emerald-500 text-white",
        bg: "bg-emerald-50/50",
        border: "border-emerald-200",
        text: "text-emerald-700",
        dot: "bg-emerald-500",
      };
    case "reachable":
      return {
        badge: "bg-amber-50 text-amber-700 border-amber-200 ring-amber-500/20",
        pill: "bg-amber-500 text-white",
        bg: "bg-amber-50/50",
        border: "border-amber-200",
        text: "text-amber-700",
        dot: "bg-amber-500",
      };
    case "out_of_reach":
      return {
        badge: "bg-rose-50 text-rose-700 border-rose-200 ring-rose-500/20",
        pill: "bg-rose-500 text-white",
        bg: "bg-rose-50/50",
        border: "border-rose-200",
        text: "text-rose-700",
        dot: "bg-rose-500",
      };
    default:
      return {
        badge: "bg-slate-100 text-slate-700 border-slate-200 ring-slate-500/20",
        pill: "bg-slate-700 text-white",
        bg: "bg-slate-50",
        border: "border-slate-200",
        text: "text-slate-700",
        dot: "bg-slate-400",
      };
  }
}

export interface DimensionMeta {
  label: string;
  weight: number;
  description: string;
}

export const DIMENSIONS_INFO: Record<string, DimensionMeta> = {
  mandatory_skills: {
    label: "Mandatory Skills",
    weight: 35,
    description: "Coverage and proficiency in core essential requirements",
  },
  preferred_skills: {
    label: "Preferred Skills",
    weight: 15,
    description: "Bonus qualifications and secondary technical proficiencies",
  },
  seniority: {
    label: "Seniority Match",
    weight: 15,
    description: "Years of experience and leadership trajectory alignment",
  },
  education: {
    label: "Education Alignment",
    weight: 10,
    description: "Academic degree and discipline compatibility",
  },
  languages: {
    label: "Languages & Communication",
    weight: 5,
    description: "Language requirements for international collaboration",
  },
  semantic: {
    label: "Semantic & Role Fit",
    weight: 20,
    description: "pgvector cosine similarity between profile & job description",
  },
};

export function dimensionLabel(key: string): string {
  return DIMENSIONS_INFO[key]?.label ?? key;
}

export function formatWorkModel(model: string): string {
  switch (model?.toLowerCase()) {
    case "remote":
      return "Remote";
    case "hybrid":
      return "Hybrid";
    case "onsite":
      return "On-site";
    default:
      return model || "Unspecified";
  }
}

export const SENIORITY_LABELS: Record<number, string> = {
  1: "Junior",
  2: "Mid",
  3: "Senior",
  4: "Lead",
};

export const SKILL_LEVEL_LABELS: Record<number, string> = {
  1: "Awareness",
  2: "Working",
  3: "Proficient",
  4: "Expert",
};

export const EDUCATION_LABELS: Record<number, string> = {
  0: "None",
  1: "High school",
  2: "Bachelor",
  3: "Master",
  4: "Doctorate",
};

export const CEFR_LABELS: Record<number, string> = {
  1: "A1",
  2: "A2",
  3: "B1",
  4: "B2",
  5: "C1",
  6: "C2",
};

export function formatFamily(family: string): string {
  return family
    ?.split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ") || family;
}
