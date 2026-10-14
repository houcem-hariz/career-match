"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/navbar";
import { useAuth } from "@/context/auth-context";
import {
  ApiError,
  getProfile,
  putProfile,
  rematch,
  type JobFamily,
  type Profile,
  type WorkModel,
} from "@/lib/api";
import {
  CEFR_LABELS,
  EDUCATION_LABELS,
  SENIORITY_LABELS,
  SKILL_LEVEL_LABELS,
  formatFamily,
  formatWorkModel,
} from "@/lib/utils";
// Copy of data/processed/referentiel.json (id + label). Regenerate if the referential changes.
import skillReferential from "@/lib/skill-referential.json";
import { Loader2, Plus, RotateCcw, Save, X, PencilLine } from "lucide-react";

const FAMILIES: JobFamily[] = [
  "backend",
  "frontend",
  "data",
  "devops",
  "cybersecurity",
  "technical_product",
];
const WORK_MODELS: WorkModel[] = ["remote", "hybrid", "onsite"];

const SKILL_LABELS = new Map(
  (skillReferential as { id: string; label: string }[]).map((s) => [s.id, s.label])
);

function toggle<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((v) => v !== value) : [...list, value];
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-xs font-black uppercase tracking-wider text-slate-400 mb-3">{children}</h2>
  );
}

function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full border px-3 py-1 text-xs font-semibold transition-all ${
        active
          ? "border-purple-600 bg-purple-600 text-white"
          : "border-slate-200 bg-white text-slate-600 hover:border-purple-300"
      }`}
    >
      {children}
    </button>
  );
}

const inputClass =
  "w-full rounded-xl border border-slate-200 bg-[#fbfbfa] px-3 py-2 text-sm text-slate-900 focus:bg-white focus:border-purple-500 focus:outline-none focus:ring-4 focus:ring-purple-500/10";

/**
 * Wireframe 04: correct the extracted Profile, then "Recalculate" →
 * PUT /api/profile (save, no rescoring) + POST /api/rematch → /offers.
 */
export default function ProfilePage() {
  const router = useRouter();
  const { sessionVersion } = useAuth();
  const [original, setOriginal] = useState<Profile | null>(null);
  const [draft, setDraft] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmNew, setConfirmNew] = useState(false);
  const [newSkill, setNewSkill] = useState("");
  const [newSkillLevel, setNewSkillLevel] = useState(2);

  useEffect(() => {
    getProfile()
      .then((profile) => {
        if (!profile) {
          router.replace("/");
          return;
        }
        setOriginal(profile);
        setDraft(profile);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Could not reach the backend.");
        setLoading(false);
      });
  }, [router, sessionVersion]);

  const dirty = useMemo(
    () => JSON.stringify(original) !== JSON.stringify(draft),
    [original, draft]
  );

  function update(patch: Partial<Profile>) {
    setDraft((prev) => (prev ? { ...prev, ...patch } : prev));
  }

  function addSkill() {
    if (!draft) return;
    const id = newSkill.trim().toLowerCase();
    if (!SKILL_LABELS.has(id)) {
      setError(`"${newSkill}" is not in the skill referential. Pick one from the list.`);
      return;
    }
    if (draft.skills.some((s) => s.skill_id === id)) {
      setError(`${SKILL_LABELS.get(id)} is already in your profile.`);
      return;
    }
    update({
      skills: [
        ...draft.skills,
        { skill_id: id, level: newSkillLevel, years_experience: null, source: "user_input" },
      ],
    });
    setNewSkill("");
    setError(null);
  }

  async function handleRecalculate() {
    if (!draft) return;
    setSaving(true);
    setError(null);
    try {
      if (dirty) await putProfile(draft);
      await rematch();
      router.push("/offers");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach the backend.");
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#fafaf8]">
        <Navbar />
        <main className="mx-auto max-w-5xl px-6 py-28 flex flex-col items-center text-center">
          <Loader2 className="h-6 w-6 animate-spin text-purple-600" />
          <p className="text-xs text-slate-500 mt-3">Loading your profile</p>
        </main>
      </div>
    );
  }

  if (!draft) {
    return (
      <div className="min-h-screen bg-[#fafaf8]">
        <Navbar />
        <main className="mx-auto max-w-md px-6 py-20 text-center">
          <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-xs text-rose-800">
            {error ?? "No profile in this session."}
          </div>
        </main>
      </div>
    );
  }

  const summary = [
    draft.first_name,
    SENIORITY_LABELS[draft.seniority],
    draft.target_families.map(formatFamily).join(", "),
    draft.preferences.work_models.map(formatWorkModel).join(", "),
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <div className="min-h-screen bg-[#fafaf8] text-slate-900">
      <Navbar />

      <main className="mx-auto max-w-4xl px-6 py-8 sm:py-10 pb-32">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-6">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-black tracking-tight text-slate-950">Profile</h1>
              {draft.user_edited && (
                <span className="inline-flex items-center gap-1 rounded-full bg-purple-100 px-2.5 py-0.5 text-[11px] font-bold text-purple-800">
                  <PencilLine className="h-3 w-3" />
                  Edited {draft.correction_count}×
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-1">{summary || "Extracted from your CV"}</p>
          </div>

          {confirmNew ? (
            <div className="flex items-center gap-2 rounded-full border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs text-amber-900">
              <span>Replace this profile?</span>
              <button
                type="button"
                onClick={() => router.push("/")}
                className="rounded-full bg-amber-600 px-3 py-1 font-semibold text-white hover:bg-amber-700"
              >
                Yes
              </button>
              <button
                type="button"
                onClick={() => setConfirmNew(false)}
                className="rounded-full px-2 py-1 font-semibold hover:bg-amber-100"
              >
                No
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setConfirmNew(true)}
              className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 shadow-xs hover:bg-slate-50 self-start"
            >
              <RotateCcw className="h-3 w-3" />
              New profile
            </button>
          )}
        </div>

        <div className="space-y-6">
          {/* Identity */}
          <section className="rounded-3xl border border-slate-200/90 bg-white p-6 shadow-xs">
            <SectionTitle>Identity & target</SectionTitle>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="block text-xs font-semibold text-slate-700 mb-1">First name</span>
                <input
                  className={inputClass}
                  value={draft.first_name ?? ""}
                  onChange={(e) => update({ first_name: e.target.value || null })}
                />
              </label>
              <label className="block">
                <span className="block text-xs font-semibold text-slate-700 mb-1">Target title</span>
                <input
                  className={inputClass}
                  value={draft.target_title ?? ""}
                  onChange={(e) => update({ target_title: e.target.value || null })}
                />
              </label>
              <label className="block">
                <span className="block text-xs font-semibold text-slate-700 mb-1">
                  Years of experience
                </span>
                <input
                  type="number"
                  min={0}
                  max={60}
                  step={0.5}
                  className={inputClass}
                  value={draft.total_years_experience}
                  onChange={(e) =>
                    update({
                      total_years_experience: Math.min(60, Math.max(0, Number(e.target.value) || 0)),
                    })
                  }
                />
              </label>
              <label className="block">
                <span className="block text-xs font-semibold text-slate-700 mb-1">Seniority</span>
                <select
                  className={inputClass}
                  value={draft.seniority}
                  onChange={(e) => update({ seniority: Number(e.target.value) })}
                >
                  {Object.entries(SENIORITY_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <span className="block text-xs font-semibold text-slate-700 mt-5 mb-2">
              Target families
            </span>
            <div className="flex flex-wrap gap-2">
              {FAMILIES.map((family) => (
                <Chip
                  key={family}
                  active={draft.target_families.includes(family)}
                  onClick={() => update({ target_families: toggle(draft.target_families, family) })}
                >
                  {formatFamily(family)}
                </Chip>
              ))}
            </div>
          </section>

          {/* Skills */}
          <section className="rounded-3xl border border-slate-200/90 bg-white p-6 shadow-xs">
            <SectionTitle>Skills ({draft.skills.length})</SectionTitle>
            <div className="flex flex-wrap gap-2">
              {draft.skills.map((skill, index) => (
                <div
                  key={skill.skill_id}
                  className={`flex items-center gap-1.5 rounded-full border py-1 pl-3 pr-1 text-xs ${
                    skill.source === "user_input"
                      ? "border-purple-200 bg-purple-50"
                      : "border-slate-200 bg-[#fbfbfa]"
                  }`}
                >
                  <span className="font-semibold text-slate-900">
                    {SKILL_LABELS.get(skill.skill_id) ?? skill.skill_id}
                  </span>
                  <select
                    aria-label={`Level for ${skill.skill_id}`}
                    value={skill.level}
                    onChange={(e) =>
                      update({
                        skills: draft.skills.map((s, i) =>
                          i === index ? { ...s, level: Number(e.target.value) } : s
                        ),
                      })
                    }
                    className="rounded-full bg-transparent text-[11px] text-slate-500 focus:outline-none"
                  >
                    {Object.entries(SKILL_LEVEL_LABELS).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={() =>
                      update({ skills: draft.skills.filter((_, i) => i !== index) })
                    }
                    className="rounded-full p-1 text-slate-400 hover:bg-slate-200 hover:text-slate-700"
                    aria-label={`Remove ${skill.skill_id}`}
                  >
                    <X className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                addSkill();
              }}
              className="mt-4 flex flex-col sm:flex-row gap-2"
            >
              <input
                list="skill-referential"
                value={newSkill}
                onChange={(e) => setNewSkill(e.target.value)}
                placeholder="Add a skill (e.g. react)"
                className={`${inputClass} sm:flex-1`}
              />
              <datalist id="skill-referential">
                {(skillReferential as { id: string; label: string }[]).map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </datalist>
              <select
                value={newSkillLevel}
                onChange={(e) => setNewSkillLevel(Number(e.target.value))}
                className={`${inputClass} sm:w-36`}
              >
                {Object.entries(SKILL_LEVEL_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
              <button
                type="submit"
                disabled={!newSkill.trim()}
                className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800 disabled:opacity-40"
              >
                <Plus className="h-3.5 w-3.5" />
                Add
              </button>
            </form>
          </section>

          {/* Preferences */}
          <section className="rounded-3xl border border-slate-200/90 bg-white p-6 shadow-xs">
            <SectionTitle>Preferences</SectionTitle>
            <span className="block text-xs font-semibold text-slate-700 mb-2">Work model</span>
            <div className="flex flex-wrap gap-2">
              {WORK_MODELS.map((model) => (
                <Chip
                  key={model}
                  active={draft.preferences.work_models.includes(model)}
                  onClick={() =>
                    update({
                      preferences: {
                        ...draft.preferences,
                        work_models: toggle(draft.preferences.work_models, model),
                      },
                    })
                  }
                >
                  {formatWorkModel(model)}
                </Chip>
              ))}
            </div>
            <p className="mt-2 text-[11px] text-slate-400">
              Work model is a filter: offers outside it are not scored at all.
            </p>

            <label className="mt-5 block">
              <span className="block text-xs font-semibold text-slate-700 mb-1">
                Locations (comma separated)
              </span>
              <input
                className={inputClass}
                value={draft.preferences.locations.join(", ")}
                onChange={(e) =>
                  update({
                    preferences: {
                      ...draft.preferences,
                      locations: e.target.value
                        .split(",")
                        .map((l) => l.trim())
                        .filter(Boolean),
                    },
                  })
                }
              />
            </label>

            <label className="mt-4 flex items-center gap-2 text-xs font-semibold text-slate-700">
              <input
                type="checkbox"
                checked={draft.preferences.willing_to_relocate}
                onChange={(e) =>
                  update({
                    preferences: { ...draft.preferences, willing_to_relocate: e.target.checked },
                  })
                }
                className="h-4 w-4 accent-purple-600"
              />
              Willing to relocate
            </label>
          </section>

          {/* Languages + education + experience */}
          <section className="rounded-3xl border border-slate-200/90 bg-white p-6 shadow-xs grid gap-6 sm:grid-cols-2">
            <div>
              <SectionTitle>Languages</SectionTitle>
              {draft.languages.length === 0 ? (
                <p className="text-xs text-slate-400">None extracted.</p>
              ) : (
                <ul className="space-y-2">
                  {draft.languages.map((lang, index) => (
                    <li key={lang.language_code} className="flex items-center gap-2 text-xs">
                      <span className="w-8 font-mono font-bold uppercase text-slate-900">
                        {lang.language_code}
                      </span>
                      <select
                        value={lang.proficiency}
                        onChange={(e) =>
                          update({
                            languages: draft.languages.map((l, i) =>
                              i === index ? { ...l, proficiency: Number(e.target.value) } : l
                            ),
                          })
                        }
                        className="rounded-lg border border-slate-200 bg-[#fbfbfa] px-2 py-1"
                      >
                        {Object.entries(CEFR_LABELS).map(([value, label]) => (
                          <option key={value} value={value}>
                            {label}
                          </option>
                        ))}
                      </select>
                    </li>
                  ))}
                </ul>
              )}

              <div className="mt-6">
                <SectionTitle>Education</SectionTitle>
              </div>
              {draft.education.length === 0 ? (
                <p className="text-xs text-slate-400">None extracted.</p>
              ) : (
                <ul className="space-y-1 text-xs text-slate-700">
                  {draft.education.map((record, i) => (
                    <li key={i}>
                      <span className="font-semibold">{EDUCATION_LABELS[record.level]}</span>
                      {record.field_of_study ? ` · ${record.field_of_study}` : ""}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div>
              <SectionTitle>Experience</SectionTitle>
              {draft.experiences.length === 0 ? (
                <p className="text-xs text-slate-400">None extracted.</p>
              ) : (
                <ul className="space-y-2">
                  {draft.experiences.map((exp, i) => (
                    <li key={i} className="rounded-xl border border-slate-100 bg-[#fbfbfa] px-3 py-2 text-xs">
                      <p className="font-semibold text-slate-900">{exp.title}</p>
                      <p className="text-slate-500">
                        {exp.family ? `${formatFamily(exp.family)} · ` : ""}
                        {Math.round((exp.duration_months / 12) * 10) / 10} yrs
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </section>
        </div>
      </main>

      {/* Sticky action bar */}
      <div className="fixed inset-x-0 bottom-0 z-20 border-t border-slate-200 bg-white/95 backdrop-blur-sm">
        <div className="mx-auto flex max-w-4xl flex-col sm:flex-row sm:items-center justify-between gap-3 px-6 py-3">
          <div className="text-xs">
            {error ? (
              <span className="font-medium text-rose-700">{error}</span>
            ) : (
              <span className="text-slate-400">
                {dirty ? "Unsaved changes." : "Recalculate rescores the offers with this profile."}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={!dirty || saving}
              onClick={() => {
                setDraft(original);
                setError(null);
              }}
              className="rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleRecalculate}
              disabled={saving}
              className="inline-flex items-center gap-1.5 rounded-full bg-gradient-to-r from-purple-600 to-indigo-600 px-5 py-2 text-xs font-bold text-white shadow-md shadow-purple-500/25 hover:opacity-95 disabled:opacity-50"
            >
              {saving ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Save className="h-3.5 w-3.5" />
              )}
              Recalculate
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
