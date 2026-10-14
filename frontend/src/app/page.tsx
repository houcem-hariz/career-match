"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/navbar";
import { matchExample, matchText, matchPdf, ApiError } from "@/lib/api";
import {
  Loader2,
  Upload,
  FileText,
  X,
  Sparkles,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  CheckCircle2,
  Zap,
  Target,
  BookOpen,
  Award,
} from "lucide-react";

interface PresetProfile {
  id: string;
  title: string;
  role: string;
  company: string;
  matchScore: number;
  skills: string[];
  action: "example" | "text";
  value: string;
}

const PRESETS: PresetProfile[] = [
  {
    id: "jane",
    title: "Senior Backend Engineer",
    role: "Python · Django · PostgreSQL",
    company: "Acme & Globex",
    matchScore: 61,
    skills: ["Python", "Django", "PostgreSQL", "AWS"],
    action: "example",
    value: "jane_doe_backend",
  },
  {
    id: "frontend",
    title: "Frontend Developer",
    role: "React · TypeScript · CSS",
    company: "Paris Tech",
    matchScore: 78,
    skills: ["React", "TypeScript", "Tailwind", "Next.js"],
    action: "text",
    value:
      "Mid-level frontend developer, React, TypeScript, CSS, Next.js, 4 years experience, hybrid, Paris",
  },
  {
    id: "data",
    title: "Data Analyst Junior",
    role: "Python · SQL · Statistics",
    company: "Decathlon & Qonto",
    matchScore: 72,
    skills: ["Python", "SQL", "Pandas", "Analytics"],
    action: "text",
    value:
      "Junior data analyst, Python, SQL, pandas, statistics, remote",
  },
];

export default function HomePage() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);

  const [inputTab, setInputTab] = useState<"pdf" | "text">("pdf");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingPresetId, setLoadingPresetId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const canSubmit = !loading && (text.trim().length > 0 || file !== null);

  async function handleLaunchMatch() {
    if (!canSubmit) return;
    setLoading(true);
    setError(null);
    try {
      if (file) {
        await matchPdf(file);
      } else if (text.trim()) {
        await matchText(text.trim());
      }
      router.push("/offers");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to run matching pipeline. Check backend connection.");
      }
      setLoading(false);
    }
  }

  async function handleSelectPreset(preset: PresetProfile) {
    if (loading) return;
    setLoading(true);
    setLoadingPresetId(preset.id);
    setError(null);
    try {
      if (preset.action === "example") {
        await matchExample(preset.value);
      } else {
        await matchText(preset.value);
      }
      router.push("/offers");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to run matching for this preset profile.");
      }
      setLoading(false);
      setLoadingPresetId(null);
    }
  }

  function handleFileSelect(selected: File | null) {
    if (!selected) return;
    if (!selected.name.toLowerCase().endsWith(".pdf")) {
      setError("Please choose a valid PDF file.");
      return;
    }
    setFile(selected);
    setText("");
    setError(null);
    setInputTab("pdf");
  }

  return (
    <div className="min-h-screen bg-[#fafaf8] text-slate-900 selection:bg-purple-100 selection:text-purple-900">
      <Navbar />

      {/* Hero Section inspired by Jobbie.fr */}
      <section className="relative overflow-hidden pt-8 pb-16 sm:pb-24">
        {/* Glow ambient background element */}
        <div className="pointer-events-none absolute -top-40 left-1/2 h-[500px] w-[800px] -translate-x-1/2 rounded-full bg-gradient-to-tr from-purple-200/50 via-indigo-100/40 to-pink-100/30 blur-3xl" />

        <div className="relative mx-auto max-w-5xl px-6">
          {/* Hero Headlines */}
          <div className="text-center max-w-2xl mx-auto space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full border border-purple-200 bg-purple-50/80 px-4 py-1.5 text-xs font-semibold text-purple-800 shadow-xs">
              <Sparkles className="h-3.5 w-3.5 text-purple-600" />
              <span>Intelligent Tech Career Matching</span>
            </div>

            <h1 className="text-4xl sm:text-5xl font-black tracking-tight text-slate-950 leading-[1.15]">
              Every job offer receives a{" "}
              <span className="bg-gradient-to-r from-purple-600 via-indigo-600 to-pink-600 bg-clip-text text-transparent">
                score out of 100
              </span>
            </h1>

            <p className="text-base text-slate-600 leading-relaxed max-w-xl mx-auto">
              Deposit your CV once, receive every verified tech opportunity scored specifically
              for your skills, and simulate taking certified courses to bridge gaps.
            </p>

            <div className="pt-1 flex items-center justify-center gap-3 text-xs text-slate-500">
              <span className="flex items-center gap-1 font-medium">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" /> 100% Free
              </span>
              <span>·</span>
              <span className="flex items-center gap-1 font-medium">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" /> Instant in-memory session
              </span>
              <span>·</span>
              <span className="flex items-center gap-1 font-medium">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" /> 6-Axis AI evaluation
              </span>
            </div>
          </div>

          {/* Interactive Match Card (Upload / Text / Presets) */}
          <div
            id="match-form"
            className="mt-12 rounded-3xl border border-slate-200/90 bg-white p-6 sm:p-10 shadow-xl shadow-purple-500/5 ring-1 ring-slate-900/5"
          >
            {/* Tab Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-5 mb-6">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setInputTab("pdf");
                    setText("");
                  }}
                  className={`flex items-center gap-2 rounded-full px-5 py-2 text-xs font-bold transition-all ${
                    inputTab === "pdf"
                      ? "bg-slate-900 text-white shadow-sm"
                      : "text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  <Upload className="h-3.5 w-3.5" />
                  <span>Upload CV (PDF)</span>
                  {file && (
                    <span className="rounded-full bg-purple-500 px-1.5 py-0.2 text-[10px] text-white">
                      1
                    </span>
                  )}
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setInputTab("text");
                    setFile(null);
                  }}
                  className={`flex items-center gap-2 rounded-full px-5 py-2 text-xs font-bold transition-all ${
                    inputTab === "text"
                      ? "bg-slate-900 text-white shadow-sm"
                      : "text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  <FileText className="h-3.5 w-3.5" />
                  <span>Paste Mini-CV Summary</span>
                </button>
              </div>

              <span className="text-xs text-slate-400 font-medium">
                Not a search bar — matching starts from who you are
              </span>
            </div>

            {/* PDF Mode */}
            {inputTab === "pdf" && (
              <div className="space-y-4">
                <input
                  ref={fileRef}
                  type="file"
                  accept=".pdf,application/pdf"
                  className="hidden"
                  onChange={(e) => handleFileSelect(e.target.files?.[0] ?? null)}
                />

                {!file ? (
                  <div
                    onDragOver={(e) => {
                      e.preventDefault();
                      setIsDragging(true);
                    }}
                    onDragLeave={() => setIsDragging(false)}
                    onDrop={(e) => {
                      e.preventDefault();
                      setIsDragging(false);
                      handleFileSelect(e.dataTransfer.files?.[0] ?? null);
                    }}
                    onClick={() => fileRef.current?.click()}
                    className={`flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-10 text-center cursor-pointer transition-all ${
                      isDragging
                        ? "border-purple-500 bg-purple-50/50"
                        : "border-slate-200 bg-[#fbfbfa] hover:border-purple-300 hover:bg-purple-50/20"
                    }`}
                  >
                    <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-purple-100/80 text-purple-700 mb-3 shadow-inner">
                      <Upload className="h-6 w-6" />
                    </div>
                    <p className="text-sm font-bold text-slate-900">
                      Click to choose or drag and drop your CV (PDF)
                    </p>
                    <p className="text-xs text-slate-500 mt-1">
                      Jane Doe backend PDF, technical resume, or CV in standard text PDF format
                    </p>
                  </div>
                ) : (
                  <div className="flex items-center justify-between rounded-2xl border border-purple-200 bg-purple-50/30 p-4">
                    <div className="flex items-center gap-3">
                      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-purple-600 text-white font-bold shadow-sm">
                        <FileText className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="text-sm font-bold text-slate-900">{file.name}</p>
                        <p className="text-xs text-slate-500">
                          {(file.size / 1024).toFixed(1)} KB · Ready for parsing & matching
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setFile(null)}
                      className="rounded-lg p-2 text-slate-400 hover:bg-slate-200/50 hover:text-slate-700 transition-colors"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Text Mode */}
            {inputTab === "text" && (
              <div className="space-y-3">
                <div className="relative">
                  <textarea
                    value={text}
                    onChange={(e) => {
                      setText(e.target.value);
                      if (e.target.value.trim()) setFile(null);
                    }}
                    rows={4}
                    disabled={loading}
                    placeholder="Senior backend engineer, Python, Django, PostgreSQL, Kubernetes, 6 years experience, remote..."
                    className="w-full rounded-2xl border border-slate-200 bg-[#fbfbfa] p-4 text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-purple-500 focus:outline-none focus:ring-4 focus:ring-purple-500/10 transition-all resize-none leading-relaxed"
                  />
                  <div className="absolute right-3.5 bottom-3.5 text-[11px] text-slate-400">
                    {text.trim().length > 0
                      ? `${text.trim().length} chars`
                      : "English mini-CV"}
                  </div>
                </div>
              </div>
            )}

            {/* Launch CTA Button */}
            <div className="mt-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-4 border-t border-slate-100">
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <ShieldCheck className="h-4 w-4 text-emerald-600 shrink-0" />
                <span>Deterministic normalization across 154 grounded skills</span>
              </div>

              <button
                type="button"
                onClick={handleLaunchMatch}
                disabled={!canSubmit}
                className="inline-flex h-11 items-center justify-center gap-2 rounded-full bg-gradient-to-r from-purple-600 via-indigo-600 to-purple-700 px-7 text-xs font-bold text-white shadow-md shadow-purple-500/25 hover:opacity-95 transition-all disabled:opacity-40"
              >
                {loading && !loadingPresetId ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin text-white" />
                    <span>Scoring candidates...</span>
                  </>
                ) : (
                  <>
                    <span>Match my profile</span>
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </div>

            {/* Error Banner */}
            {error && (
              <div className="mt-5 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-xs font-medium text-rose-800 leading-relaxed flex items-start gap-2.5">
                <div className="mt-0.5 h-2 w-2 rounded-full bg-rose-500 shrink-0" />
                <div className="flex-1">{error}</div>
              </div>
            )}

            {/* 3 Presets Cards (Inspired by Jobbie sample feeds) */}
            <div className="mt-8 pt-6 border-t border-slate-100">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                Or test with pre-curated candidate profiles:
              </p>

              <div className="grid gap-3 sm:grid-cols-3">
                {PRESETS.map((preset) => {
                  const isCurrent = loading && loadingPresetId === preset.id;
                  return (
                    <button
                      key={preset.id}
                      type="button"
                      onClick={() => handleSelectPreset(preset)}
                      disabled={loading}
                      className="group flex flex-col justify-between rounded-2xl border border-slate-200/90 bg-[#fbfbfa] p-4 text-left transition-all hover:border-purple-300 hover:bg-white hover:shadow-md disabled:opacity-50"
                    >
                      <div>
                        <div className="flex items-center justify-between gap-2 mb-1.5">
                          <span className="text-xs font-bold text-slate-900 group-hover:text-purple-600 transition-colors">
                            {preset.title}
                          </span>
                          {isCurrent ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin text-purple-600" />
                          ) : (
                            <span className="rounded-full bg-purple-100 px-2 py-0.5 text-[10px] font-black text-purple-800">
                              ~{preset.matchScore}%
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-500 mb-2.5">{preset.role}</p>

                        <div className="flex flex-wrap gap-1">
                          {preset.skills.map((skill) => (
                            <span
                              key={skill}
                              className="rounded-md bg-white border border-slate-200/80 px-1.5 py-0.5 text-[10px] font-medium text-slate-600"
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="mt-3.5 pt-2.5 border-t border-slate-200/60 flex items-center justify-between text-[11px] font-bold text-purple-600">
                        <span>Instant Match</span>
                        <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4 Pastel Feature Cards (Directly matching Screenshot 2!) */}
      <section className="mx-auto max-w-5xl px-6 py-12">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Score /100 (Mint Green) */}
          <div className="rounded-2xl border border-emerald-100 bg-[#e8f7f0] p-5 space-y-1.5 shadow-xs">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-800 font-bold mb-2">
              <Target className="h-5 w-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900">Score /100</h3>
            <p className="text-xs text-slate-600">
              Multi-criteria AI comparison evaluating skills, seniority, and alignment.
            </p>
          </div>

          {/* Card 2: Real-time (Pastel Yellow) */}
          <div className="rounded-2xl border border-amber-100 bg-[#fef9e7] p-5 space-y-1.5 shadow-xs">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-500/15 text-amber-800 font-bold mb-2">
              <Zap className="h-5 w-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900">Real-Time Search</h3>
            <p className="text-xs text-slate-600">
              Continuous hybrid cosine retrieval with PostgreSQL vector indexing.
            </p>
          </div>

          {/* Card 3: Transparency (Pastel Periwinkle/Lavender) */}
          <div className="rounded-2xl border border-indigo-100 bg-[#eef0fb] p-5 space-y-1.5 shadow-xs">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/15 text-indigo-800 font-bold mb-2">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900">Full Transparency</h3>
            <p className="text-xs text-slate-600">
              Granular breakdown across 6 dimensions with clear gap identification.
            </p>
          </div>

          {/* Card 4: Simulations (Pastel Pink) */}
          <div className="rounded-2xl border border-pink-100 bg-[#fdebf0] p-5 space-y-1.5 shadow-xs">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-pink-500/15 text-pink-800 font-bold mb-2">
              <TrendingUp className="h-5 w-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900">Course Impact</h3>
            <p className="text-xs text-slate-600">
              What-if simulation projecting score jumps and bucket upgrades from courses.
            </p>
          </div>
        </div>
      </section>

      {/* 4-Step "How it works" Journey (Matching Screenshot 3!) */}
      <section id="how-it-works" className="mx-auto max-w-5xl px-6 py-16 border-t border-slate-200/80">
        <div className="text-center max-w-xl mx-auto mb-12">
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-950">
            How it works
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-2">
            One CV. A matched feed. Deep gap insights. From the first upload to the final offer.
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-4">
          {/* Step 1 */}
          <div className="rounded-2xl border border-slate-200/80 bg-white p-5 space-y-2 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-purple-100 text-xs font-black text-purple-700">
                01
              </span>
              <Upload className="h-4 w-4 text-slate-400" />
            </div>
            <h3 className="text-sm font-bold text-slate-900 pt-1">Create your profile</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Upload your CV (PDF) or paste a summary. We extract verified skills and experience.
            </p>
          </div>

          {/* Step 2 */}
          <div className="rounded-2xl border border-slate-200/80 bg-white p-5 space-y-2 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-purple-100 text-xs font-black text-purple-700">
                02
              </span>
              <Target className="h-4 w-4 text-slate-400" />
            </div>
            <h3 className="text-sm font-bold text-slate-900 pt-1">Receive your matches</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Jobs are scored 0–100 and partitioned into Eligible, Reachable, and Out of Reach.
            </p>
          </div>

          {/* Step 3 */}
          <div className="rounded-2xl border border-slate-200/80 bg-white p-5 space-y-2 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-purple-100 text-xs font-black text-purple-700">
                03
              </span>
              <Award className="h-4 w-4 text-slate-400" />
            </div>
            <h3 className="text-sm font-bold text-slate-900 pt-1">Inspect your gaps</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              See exact mandatory vs preferred requirements you are missing for every role.
            </p>
          </div>

          {/* Step 4 */}
          <div className="rounded-2xl border border-slate-200/80 bg-white p-5 space-y-2 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-purple-100 text-xs font-black text-purple-700">
                04
              </span>
              <BookOpen className="h-4 w-4 text-slate-400" />
            </div>
            <h3 className="text-sm font-bold text-slate-900 pt-1">Simulate courses</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Take simulated training courses to upgrade your bucket and jump from Out of Reach to Reachable!
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
