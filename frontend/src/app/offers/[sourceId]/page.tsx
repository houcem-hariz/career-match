"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Navbar } from "@/components/navbar";
import { getOffer, type CardPayload } from "@/lib/api";
import {
  bucketLabel,
  bucketStyles,
  formatWorkModel,
  formatFamily,
  DIMENSIONS_INFO,
} from "@/lib/utils";
import {
  ArrowLeft,
  Loader2,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Sparkles,
  ArrowRight,
  Heart,
  X,
} from "lucide-react";

export default function OfferDetailPage() {
  const params = useParams<{ sourceId: string }>();
  const router = useRouter();
  const [card, setCard] = useState<CardPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [liked, setLiked] = useState(false);

  useEffect(() => {
    if (!params.sourceId) return;
    getOffer(params.sourceId)
      .then((result) => {
        if (!result) {
          setNotFound(true);
        } else {
          setCard(result);
        }
      })
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }, [params.sourceId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#fafaf8]">
        <Navbar />
        <main className="mx-auto max-w-5xl px-6 py-28 flex flex-col items-center justify-center text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-purple-100 text-purple-700 mb-4 shadow-sm animate-pulse">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
          <h2 className="text-base font-bold text-slate-900">Loading offer scorecard</h2>
          <p className="text-xs text-slate-500 mt-1">
            Calculating 6D dimensions and simulated course impacts
          </p>
        </main>
      </div>
    );
  }

  if (notFound || !card) {
    return (
      <div className="min-h-screen bg-[#fafaf8]">
        <Navbar />
        <main className="mx-auto max-w-4xl px-6 py-20 text-center">
          <div className="rounded-3xl border border-slate-200 bg-white p-12 max-w-md mx-auto shadow-sm">
            <AlertTriangle className="h-10 w-10 text-amber-500 mx-auto mb-3" />
            <h2 className="text-lg font-bold text-slate-900">Offer not found</h2>
            <p className="text-xs text-slate-500 mt-1">
              This card is not in your current active session.
            </p>
            <div className="mt-6 flex justify-center gap-2">
              <Link
                href="/offers"
                className="rounded-full bg-slate-900 px-5 py-2 text-xs font-semibold text-white"
              >
                Back to Offers
              </Link>
            </div>
          </div>
        </main>
      </div>
    );
  }

  const styles = bucketStyles(card.bucket);
  const companyInitial = card.company ? card.company.charAt(0).toUpperCase() : "C";

  return (
    <div className="min-h-screen bg-[#fafaf8] text-slate-900">
      <Navbar />

      <main className="mx-auto max-w-4xl px-6 py-8 sm:py-10">
        {/* Navigation Breadcrumb */}
        <div className="mb-6">
          <Link
            href="/offers"
            className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-4 py-1.5 text-xs font-bold text-slate-700 shadow-xs hover:bg-slate-50 transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Back to Offers</span>
          </Link>
        </div>

        {/* Hero Scorecard Box (Directly inspired by Jobbie Screenshot 2!) */}
        <div className="relative rounded-3xl border border-slate-200/90 bg-white p-7 sm:p-9 shadow-lg shadow-purple-500/5 ring-1 ring-slate-900/5 mb-8">
          {/* Top Row: Company & Jobbie Circular Score Badge (82%) */}
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-center gap-3.5">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-tr from-purple-600 to-indigo-600 text-white font-black text-xl shadow-sm">
                {companyInitial}
              </div>
              <div>
                <h1 className="text-2xl font-black text-slate-950 tracking-tight">
                  {card.title}
                </h1>
                <p className="text-xs font-medium text-slate-500 mt-0.5">
                  {card.company ?? "Verified Partner"} · {formatFamily(card.family)} · {formatWorkModel(card.work_model)}
                </p>
              </div>
            </div>

            {/* Circular Badge from Screenshot 2 */}
            <div className="flex flex-col items-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full border-4 border-emerald-400 bg-emerald-50 text-emerald-900 font-black text-lg shadow-sm">
                {Math.round(card.score)}%
              </div>
              <span className={`mt-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-black border ${styles.badge}`}>
                {bucketLabel(card.bucket)}
              </span>
            </div>
          </div>

          {/* Circular Dimension Gauges (Exp., Skills, Semantic etc. matching Screenshot 2!) */}
          <div className="mt-8 pt-6 border-t border-slate-100">
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-3 text-center">
              {Object.entries(card.dimensions).map(([key, val], idx) => {
                const percent = Math.min(Math.round(val * 100), 100);
                const circleColors = [
                  "border-purple-300 text-purple-700 bg-purple-50",
                  "border-pink-300 text-pink-700 bg-pink-50",
                  "border-indigo-300 text-indigo-700 bg-indigo-50",
                  "border-emerald-300 text-emerald-700 bg-emerald-50",
                  "border-amber-300 text-amber-700 bg-amber-50",
                  "border-sky-300 text-sky-700 bg-sky-50",
                ];
                const colorClass = circleColors[idx % circleColors.length];

                return (
                  <div key={key} className="flex flex-col items-center">
                    <div
                      className={`flex h-12 w-12 items-center justify-center rounded-full border-2 font-black text-xs ${colorClass}`}
                    >
                      {percent}%
                    </div>
                    <span className="text-[11px] font-bold text-slate-600 mt-2 truncate max-w-[80px]">
                      {DIMENSIONS_INFO[key]?.label.split(" ")[0] ?? key}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* "Pourquoi c'est un match" (Why it's a match checklist from Screenshot 2!) */}
          <div className="mt-8 pt-6 border-t border-slate-100">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-3">
              Why it&apos;s a match
            </span>
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Work Model: {formatWorkModel(card.work_model)}</span>
              </span>

              <span className="inline-flex items-center gap-1 rounded-full bg-indigo-50 px-3 py-1 text-xs font-bold text-indigo-700 border border-indigo-200">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Semantic Fit: {(card.similarity * 100).toFixed(0)}%</span>
              </span>

              {card.mandatory_gap_count === 0 ? (
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>All mandatory skills matched</span>
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-3 py-1 text-xs font-bold text-rose-700 border border-rose-200">
                  <XCircle className="h-3.5 w-3.5" />
                  <span>{card.mandatory_gap_count} Mandatory Skill Gaps</span>
                </span>
              )}
            </div>
          </div>

          {/* Floating Tinder-like Action buttons from Screenshot 2 (Cross & Heart) */}
          <div className="mt-8 pt-6 border-t border-slate-100 flex items-center justify-center gap-4">
            <button
              type="button"
              onClick={() => router.push("/offers")}
              className="flex h-12 w-12 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 shadow-sm hover:bg-slate-100 hover:text-slate-900 transition-all"
              title="Pass"
            >
              <X className="h-5 w-5" />
            </button>

            <button
              type="button"
              onClick={() => setLiked(!liked)}
              className={`flex h-12 w-12 items-center justify-center rounded-full border shadow-sm transition-all ${
                liked
                  ? "border-pink-300 bg-pink-100 text-pink-600 scale-105"
                  : "border-pink-200 bg-pink-50 text-pink-500 hover:bg-pink-100"
              }`}
              title="Save / Love"
            >
              <Heart className="h-5 w-5 fill-current" />
            </button>
          </div>
        </div>

        {/* Gaps Section */}
        <section className="rounded-3xl border border-slate-200/90 bg-white p-6 sm:p-8 shadow-xs mb-8">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-5">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              <h2 className="text-base font-black text-slate-900">
                Identified Skill Gaps ({card.gaps.length})
              </h2>
            </div>
            <span className="text-xs text-slate-400">
              {card.mandatory_gap_count} Mandatory
            </span>
          </div>

          {card.gaps.length === 0 ? (
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-6 text-center text-xs text-emerald-800">
              <CheckCircle2 className="h-6 w-6 text-emerald-600 mx-auto mb-1.5" />
              <p className="font-bold">No gaps identified for this role!</p>
              <p className="text-slate-500 mt-0.5">Your profile satisfies all core specifications.</p>
            </div>
          ) : (
            <div className="space-y-2.5">
              {card.gaps.map((gap, i) => (
                <div
                  key={i}
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 rounded-2xl border border-slate-200/80 bg-[#fbfbfa] px-4 py-3 text-xs"
                >
                  <div className="flex items-center gap-2.5">
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-[10px] font-black uppercase tracking-wider ${
                        gap.requirement === "mandatory"
                          ? "bg-rose-100 text-rose-800"
                          : "bg-amber-100 text-amber-800"
                      }`}
                    >
                      {gap.requirement ?? gap.kind}
                    </span>
                    <span className="font-bold text-slate-900 font-mono">
                      {gap.skill_id ?? gap.kind}
                    </span>
                  </div>

                  <div className="text-slate-500 font-mono text-[11px]">
                    have: <span className="font-bold text-slate-700">{gap.have ?? "missing"}</span> · need:{" "}
                    <span className="font-bold text-purple-700">{gap.need ?? "WORKING"}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Curriculum Simulations Section */}
        <section className="rounded-3xl border border-purple-200/80 bg-gradient-to-b from-purple-50/30 to-white p-6 sm:p-8 shadow-xs">
          <div className="flex items-center justify-between pb-4 border-b border-purple-100 mb-6">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-purple-600" />
              <h2 className="text-base font-black text-slate-900">
                Impact Simulation: Certified Training Recommendations
              </h2>
            </div>
            <span className="rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-bold text-purple-800">
              {card.simulations.length} courses
            </span>
          </div>

          {card.simulations.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-8 text-center text-xs text-slate-400">
              No training simulations available for remaining requirements.
            </div>
          ) : (
            <div className="grid gap-3.5 sm:grid-cols-2">
              {card.simulations.map((sim) => (
                <div
                  key={sim.course_id}
                  className="rounded-2xl border border-purple-200/90 bg-white p-5 shadow-xs transition-all hover:border-purple-400 hover:shadow-md"
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div>
                      <span className="rounded-full bg-purple-100 px-2 py-0.5 text-[10px] font-bold text-purple-700 uppercase">
                        Target: {sim.skill_id}
                      </span>
                      <h3 className="text-sm font-bold text-slate-900 mt-1">
                        {sim.title}
                      </h3>
                    </div>

                    <div className="flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-black text-emerald-700 border border-emerald-200 shrink-0">
                      <TrendingUp className="h-3 w-3" />
                      <span>+{sim.delta.toFixed(1)} pts</span>
                    </div>
                  </div>

                  {/* Score progression */}
                  <div className="mt-4 rounded-xl bg-slate-50 p-2.5 flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-500 font-sans">Projected score:</span>
                    <div className="flex items-center gap-2">
                      <span className="text-slate-400 line-through">
                        {sim.score_before.toFixed(1)}
                      </span>
                      <ArrowRight className="h-3 w-3 text-slate-400" />
                      <span className="font-black text-slate-950">
                        {sim.score_after.toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  {/* Bucket upgrade */}
                  <div className="mt-2.5 flex items-center justify-between text-[11px] pt-2 border-t border-slate-100">
                    <span className="text-slate-400">Bucket progression:</span>
                    <div className="flex items-center gap-1.5 font-bold">
                      <span className="rounded-full px-2 py-0.5 bg-slate-100 text-slate-600">
                        {bucketLabel(sim.bucket_before)}
                      </span>
                      <ArrowRight className="h-3 w-3 text-slate-400" />
                      <span className="rounded-full px-2 py-0.5 bg-emerald-100 text-emerald-800">
                        {bucketLabel(sim.bucket_after)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
