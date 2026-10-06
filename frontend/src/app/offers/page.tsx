"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Navbar } from "@/components/navbar";
import { useAuth } from "@/context/auth-context";
import { listOffers, type CardPayload, type MatchResponse } from "@/lib/api";
import {
  bucketLabel,
  bucketStyles,
  formatWorkModel,
  formatFamily,
} from "@/lib/utils";
import {
  Loader2,
  ArrowRight,
  RotateCcw,
  Search,
  Sparkles,
  Info,
  CheckCircle2,
  AlertTriangle,
  Bookmark,
  Building2,
  MapPin,
  TrendingUp,
} from "lucide-react";

type BucketFilter = "all" | "eligible" | "reachable" | "out_of_reach";

export default function OffersPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [data, setData] = useState<MatchResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<BucketFilter>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [savedIds, setSavedIds] = useState<string[]>([]);

  useEffect(() => {
    listOffers().then((result) => {
      if (!result) {
        router.replace("/");
        return;
      }
      setData(result);
      setLoading(false);
    });
  }, [router]);

  const toggleSave = (sourceId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setSavedIds((prev) =>
      prev.includes(sourceId)
        ? prev.filter((id) => id !== sourceId)
        : [...prev, sourceId]
    );
  };

  const grouped = useMemo(() => {
    const map: Record<string, CardPayload[]> = {
      eligible: [],
      reachable: [],
      out_of_reach: [],
    };
    if (data?.cards) {
      for (const card of data.cards) {
        if (map[card.bucket]) {
          map[card.bucket].push(card);
        }
      }
    }
    return map;
  }, [data]);

  const displayedCards = useMemo(() => {
    if (!data?.cards) return [];
    let list = activeTab === "all" ? data.cards : grouped[activeTab] || [];

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (c) =>
          c.title.toLowerCase().includes(q) ||
          (c.company && c.company.toLowerCase().includes(q)) ||
          c.family.toLowerCase().includes(q)
      );
    }
    return list;
  }, [data, activeTab, searchQuery, grouped]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#fafaf8]">
        <Navbar />
        <main className="mx-auto max-w-5xl px-6 py-28 flex flex-col items-center justify-center text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-purple-100 text-purple-700 mb-4 shadow-sm animate-pulse">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
          <h2 className="text-base font-bold text-slate-900">Loading matched feed</h2>
          <p className="text-xs text-slate-500 mt-1">
            Scoring candidates and preparing gap recommendations
          </p>
        </main>
      </div>
    );
  }

  const candidateName = user ? user.name : "Jane Doe";
  const totalCards = data!.cards.length;
  const bestCard = data!.cards[0];

  return (
    <div className="min-h-screen bg-[#fafaf8] text-slate-900">
      <Navbar />

      <main className="mx-auto max-w-5xl px-6 py-8 sm:py-10">
        {/* Greeting Banner inspired by Jobbie Dashboard */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-black tracking-tight text-slate-950">
                Hello {candidateName}
              </h1>
              <span className="inline-flex items-center gap-1 rounded-full bg-purple-100/80 px-2.5 py-0.5 text-xs font-bold text-purple-800">
                <Sparkles className="h-3 w-3 text-purple-600" />
                <span>Scout matched {totalCards} offers for you</span>
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Top-{totalCards} opportunities from {data!.candidate_count} eligible roles evaluated
              in this session.
            </p>
          </div>

          <button
            type="button"
            onClick={() => router.push("/")}
            className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 shadow-xs hover:bg-slate-50 self-start sm:self-auto transition-colors"
          >
            <RotateCcw className="h-3 w-3" />
            <span>New Profile Match</span>
          </button>
        </div>

        {/* Bucket Tabs & Search Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-3 mb-8">
          <div className="flex flex-wrap items-center gap-2 text-xs font-bold text-slate-600">
            <button
              type="button"
              onClick={() => setActiveTab("all")}
              className={`rounded-full px-4 py-1.5 transition-all ${
                activeTab === "all"
                  ? "bg-purple-600 text-white shadow-xs"
                  : "hover:bg-slate-200/60"
              }`}
            >
              All Offers ({totalCards})
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("eligible")}
              className={`flex items-center gap-1.5 rounded-full px-3.5 py-1.5 transition-all ${
                activeTab === "eligible"
                  ? "bg-emerald-600 text-white shadow-xs"
                  : "hover:bg-slate-200/60"
              }`}
            >
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              <span>Eligible ({grouped.eligible.length})</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("reachable")}
              className={`flex items-center gap-1.5 rounded-full px-3.5 py-1.5 transition-all ${
                activeTab === "reachable"
                  ? "bg-amber-600 text-white shadow-xs"
                  : "hover:bg-slate-200/60"
              }`}
            >
              <span className="h-2 w-2 rounded-full bg-amber-400" />
              <span>Reachable ({grouped.reachable.length})</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("out_of_reach")}
              className={`flex items-center gap-1.5 rounded-full px-3.5 py-1.5 transition-all ${
                activeTab === "out_of_reach"
                  ? "bg-slate-900 text-white shadow-xs"
                  : "hover:bg-slate-200/60"
              }`}
            >
              <span className="h-2 w-2 rounded-full bg-slate-400" />
              <span>Out of reach ({grouped.out_of_reach.length})</span>
            </button>
          </div>

          {/* Search box */}
          <div className="relative min-w-[200px]">
            <Search className="absolute left-3.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search title, company..."
              className="w-full rounded-full border border-slate-200 bg-white pl-9 pr-4 py-1.5 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500/20"
            />
          </div>
        </div>

        {/* Featured Job Card (Inspired by Jobbie's "TOP PICK DU JOUR") */}
        {bestCard && activeTab === "all" && !searchQuery && (
          <div className="mb-10 rounded-3xl border border-purple-200/80 bg-gradient-to-br from-white via-purple-50/20 to-indigo-50/20 p-6 sm:p-7 shadow-md shadow-purple-500/5 ring-1 ring-purple-900/5">
            <div className="flex items-center justify-between gap-2 mb-3">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-900 px-3 py-1 text-[10px] font-black uppercase tracking-wider text-white">
                <Sparkles className="h-3 w-3 text-purple-400" />
                <span>Top Pick of the Session</span>
              </span>

              {/* Circular Gauge Score (Matching Jobbie screenshot!) */}
              <div className="flex h-11 w-11 items-center justify-center rounded-full border-2 border-emerald-500 bg-emerald-50 font-black text-xs text-emerald-800 shadow-xs">
                {Math.round(bestCard.score)}%
              </div>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
              <div>
                <h2 className="text-xl font-black text-slate-950">
                  {bestCard.title}
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  {bestCard.company ?? "Verified Tech Partner"} · {formatFamily(bestCard.family)} · {bestCard.seniority}
                </p>

                <div className="mt-3 flex flex-wrap gap-1.5">
                  <span className="rounded-full bg-purple-100/80 px-2.5 py-0.5 text-[11px] font-semibold text-purple-800">
                    {formatWorkModel(bestCard.work_model)}
                  </span>
                  <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-semibold text-slate-700">
                    {bucketLabel(bestCard.bucket)}
                  </span>
                  {bestCard.simulations.length > 0 && (
                    <span className="rounded-full bg-emerald-100/80 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-800">
                      +{bestCard.simulations[0].delta.toFixed(1)} pts with simulation
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* AI Thought Bubble (Inspired by Jobbie's "IRIS PENSE") */}
            <div className="mt-5 rounded-2xl border border-purple-200/60 bg-white/90 p-4 text-xs text-slate-700 leading-relaxed shadow-xs flex items-start gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-purple-600 text-white font-bold text-xs shrink-0 shadow-xs">
                AI
              </div>
              <div className="flex-1">
                <span className="font-extrabold text-purple-900 uppercase text-[10px] tracking-wider block mb-0.5">
                  AI Fit Insight
                </span>
                {bestCard.mandatory_gap_count === 0
                  ? "All core requirements are satisfied by your profile. You have high alignment for this role!"
                  : `Your skills match the role fundamentals. Closing ${bestCard.mandatory_gap_count} gap(s) through catalog training can significantly elevate your matching score.`}
              </div>
            </div>

            <div className="mt-5 flex items-center justify-between pt-2">
              <Link
                href={`/offers/${bestCard.source_id}`}
                className="inline-flex items-center gap-1.5 rounded-full bg-purple-600 px-5 py-2 text-xs font-bold text-white shadow-sm hover:bg-purple-700 transition-colors"
              >
                <span>Inspect full 6D breakdown</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>
        )}

        {/* Section Heading */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xs font-black uppercase tracking-wider text-slate-400">
            {activeTab === "all" ? "Recommended Tech Roles" : `${bucketLabel(activeTab)} Roles`}
          </h3>
          <span className="text-xs text-slate-400">{displayedCards.length} offers</span>
        </div>

        {/* Empty State */}
        {displayedCards.length === 0 ? (
          <div className="rounded-3xl border border-dashed border-slate-200 bg-white p-12 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100 text-slate-400 mx-auto mb-3">
              <Info className="h-6 w-6" />
            </div>
            <h4 className="text-sm font-bold text-slate-900">
              No offers in this view
            </h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
              {activeTab === "eligible"
                ? "For strict remote criteria, mandatory skills or seniority thresholds were not met without gaps. Check Reachable to see achievable roles."
                : "No job matches found for current search filters."}
            </p>
          </div>
        ) : (
          /* Cards Grid inspired by Jobbie Screenshot 1 & 2 */
          <div className="grid gap-4 sm:grid-cols-2">
            {displayedCards.map((card) => {
              const styles = bucketStyles(card.bucket);
              const isSaved = savedIds.includes(card.source_id);
              const companyInitial = card.company
                ? card.company.charAt(0).toUpperCase()
                : "C";

              return (
                <Link
                  key={card.source_id}
                  href={`/offers/${card.source_id}`}
                  className="group relative flex flex-col justify-between rounded-3xl border border-slate-200/90 bg-white p-5 shadow-xs transition-all hover:border-purple-300 hover:shadow-lg hover:-translate-y-0.5"
                >
                  <div>
                    {/* Top Row: Company initial & Circular Match Score Gauge */}
                    <div className="flex items-start justify-between gap-3 mb-3">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-purple-100/80 font-black text-purple-700 text-sm group-hover:bg-purple-600 group-hover:text-white transition-colors">
                          {companyInitial}
                        </div>
                        <div className="min-w-0">
                          <h4 className="text-sm font-bold text-slate-900 group-hover:text-purple-600 transition-colors truncate">
                            {card.title}
                          </h4>
                          <p className="text-xs text-slate-500 truncate">
                            {card.company ?? "Verified Partner"} · {formatWorkModel(card.work_model)}
                          </p>
                        </div>
                      </div>

                      {/* Jobbie Circular Score Gauge */}
                      <div
                        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 font-black text-xs shadow-xs ${
                          card.score >= 70
                            ? "border-emerald-500 bg-emerald-50 text-emerald-800"
                            : card.score >= 55
                            ? "border-amber-500 bg-amber-50 text-amber-800"
                            : "border-slate-300 bg-slate-50 text-slate-800"
                        }`}
                      >
                        {Math.round(card.score)}%
                      </div>
                    </div>

                    {/* Meta Tags */}
                    <div className="flex flex-wrap gap-1.5 mb-3">
                      <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[10px] font-bold text-slate-600">
                        {formatFamily(card.family)}
                      </span>
                      <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold border ${styles.badge}`}>
                        {bucketLabel(card.bucket)}
                      </span>
                      {card.mandatory_gap_count > 0 ? (
                        <span className="rounded-full bg-amber-50 px-2.5 py-0.5 text-[10px] font-semibold text-amber-700 border border-amber-200">
                          {card.mandatory_gap_count} gap{card.mandatory_gap_count > 1 ? "s" : ""}
                        </span>
                      ) : (
                        <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-700 border border-emerald-200">
                          0 gaps
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Card Action Row */}
                  <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between">
                    <button
                      type="button"
                      onClick={(e) => toggleSave(card.source_id, e)}
                      className={`p-1.5 rounded-full transition-colors ${
                        isSaved ? "text-purple-600 bg-purple-50" : "text-slate-400 hover:text-slate-700"
                      }`}
                      title={isSaved ? "Saved" : "Save offer"}
                    >
                      <Bookmark className="h-4 w-4" />
                    </button>

                    <div className="flex items-center gap-1 text-xs font-bold text-purple-600 group-hover:underline">
                      <span>View offer</span>
                      <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
