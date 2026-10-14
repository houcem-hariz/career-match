"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { LoginModal } from "./login-modal";
import {
  Sparkles,
  ChevronDown,
  LogOut,
  Layers,
  ArrowRight,
  User,
} from "lucide-react";

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, logout, openLoginModal } = useAuth();
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  return (
    <>
      {/* Top Floating Header inspired by SuperCareer & Jobbie */}
      <header className="sticky top-0 z-40 w-full px-4 pt-3 pb-2 transition-all">
        <div className="mx-auto flex h-14 max-w-5xl items-center justify-between rounded-full border border-slate-200/80 bg-white/90 px-6 shadow-sm backdrop-blur-md ring-1 ring-slate-900/5">
          {/* Left: Brand Logo */}
          <Link
            href="/"
            className="flex items-center gap-2.5 transition-opacity hover:opacity-90"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-600 to-violet-500 text-white shadow-sm shadow-indigo-500/30">
              <Sparkles className="h-4 w-4" />
            </div>
            <span className="text-base font-extrabold tracking-tight text-slate-900 font-sans">
              career<span className="text-purple-600">match</span>
            </span>
          </Link>

          {/* Center: Navigation Links */}
          <nav className="hidden md:flex items-center gap-1.5">
            <Link
              href="/"
              className={`rounded-full px-4 py-1.5 text-xs font-semibold transition-all ${
                pathname === "/"
                  ? "bg-slate-900 text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-950 hover:bg-slate-100/70"
              }`}
            >
              Match
            </Link>

            <Link
              href="/offers"
              className={`rounded-full px-4 py-1.5 text-xs font-semibold transition-all ${
                pathname.startsWith("/offers")
                  ? "bg-slate-900 text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-950 hover:bg-slate-100/70"
              }`}
            >
              Job Offers
            </Link>

            <a
              href="#how-it-works"
              className="rounded-full px-4 py-1.5 text-xs font-semibold text-slate-600 hover:text-slate-950 hover:bg-slate-100/70 transition-all"
            >
              How it works
            </a>
          </nav>

          {/* Right: User Authentication actions */}
          <div className="flex items-center gap-2.5">
            {isAuthenticated && user ? (
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 py-1 pl-2.5 pr-2 text-xs font-semibold text-slate-800 hover:bg-slate-100 transition-all shadow-sm"
                >
                  <span className="max-w-[110px] truncate">{user.name}</span>
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-purple-600 text-[10px] font-bold text-white shadow-xs">
                    {user.name.charAt(0).toUpperCase()}
                  </div>
                  <ChevronDown className="h-3 w-3 text-slate-400" />
                </button>

                {userMenuOpen && (
                  <div className="absolute right-0 mt-2 w-52 rounded-2xl border border-slate-200 bg-white p-2 shadow-xl ring-1 ring-slate-900/5 animate-in fade-in zoom-in-95 duration-150 z-50">
                    <div className="px-3 py-2 border-b border-slate-100">
                      <p className="text-xs font-bold text-slate-900 truncate">
                        {user.name}
                      </p>
                      <p className="text-[11px] text-slate-500 font-mono truncate">
                        {user.email}
                      </p>
                    </div>

                    <div className="py-1">
                      <Link
                        href="/offers"
                        onClick={() => setUserMenuOpen(false)}
                        className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors"
                      >
                        <Layers className="h-3.5 w-3.5 text-purple-600" />
                        <span>View Matched Offers</span>
                      </Link>
                    </div>

                    <div className="pt-1 border-t border-slate-100">
                      <button
                        type="button"
                        onClick={() => {
                          logout();
                          setUserMenuOpen(false);
                        }}
                        className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-xs font-semibold text-rose-600 hover:bg-rose-50 transition-colors"
                      >
                        <LogOut className="h-3.5 w-3.5" />
                        <span>Sign out</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <>
                <button
                  type="button"
                  onClick={openLoginModal}
                  className="rounded-full px-3.5 py-1.5 text-xs font-semibold text-slate-600 hover:text-slate-950 transition-colors"
                >
                  Sign in
                </button>

                <button
                  type="button"
                  onClick={() => router.push("/#match-form")}
                  className="inline-flex items-center gap-1.5 rounded-full bg-slate-900 px-4 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-purple-700 transition-all"
                >
                  <span>Start Match</span>
                  <ArrowRight className="h-3 w-3" />
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Global Login Dialog */}
      <LoginModal />
    </>
  );
}
