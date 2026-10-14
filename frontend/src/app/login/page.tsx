"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import {
  Sparkles,
  Lock,
  Mail,
  User as UserIcon,
  Eye,
  EyeOff,
  ArrowRight,
  ShieldCheck,
  Compass,
} from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login, user } = useAuth();
  const [tab, setTab] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  if (user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
        <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-600 text-white font-bold text-lg mb-3">
            {user.name.charAt(0).toUpperCase()}
          </div>
          <h2 className="text-lg font-bold text-slate-900">Signed In as {user.name}</h2>
          <p className="text-xs text-slate-500 mt-1">{user.email}</p>
          <div className="mt-6 flex justify-center gap-3">
            <button
              onClick={() => router.push("/offers")}
              className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800"
            >
              Go to Offers
            </button>
            <button
              onClick={() => router.push("/")}
              className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
            >
              Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim() || !password.trim()) return;
    login(email.trim(), name.trim());
    router.push("/offers");
  }

  function handleDemo() {
    login("jane.doe@example.com", "Jane Doe");
    router.push("/offers");
  }

  return (
    <div className="min-h-screen flex flex-col justify-center items-center bg-slate-50/70 p-6">
      {/* Brand Top */}
      <Link href="/" className="flex items-center gap-2.5 mb-8 hover:opacity-90 transition-opacity">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 text-white shadow-sm ring-1 ring-slate-900/10">
          <Compass className="h-5 w-5 text-indigo-400" />
        </div>
        <div className="flex flex-col text-left">
          <span className="text-lg font-bold tracking-tight text-slate-950">
            career<span className="text-indigo-600">-match</span>
          </span>
          <span className="text-[10px] font-semibold tracking-wider uppercase text-slate-400">
            AI Career Intelligence
          </span>
        </div>
      </Link>

      {/* Main Card */}
      <div className="w-full max-w-md rounded-2xl border border-slate-200/80 bg-white p-8 shadow-xl ring-1 ring-slate-900/5">
        <div className="text-center pb-2">
          <h1 className="text-2xl font-bold tracking-tight text-slate-950">
            {tab === "signin" ? "Sign in to CareerMatch" : "Create your account"}
          </h1>
          <p className="text-xs text-slate-500 mt-1.5">
            Saves the profile already in memory. No need to re-upload your CV.
          </p>
        </div>

        {/* Tab switch */}
        <div className="mt-6 grid grid-cols-2 rounded-xl bg-slate-100 p-1 text-xs font-semibold text-slate-600">
          <button
            type="button"
            onClick={() => setTab("signin")}
            className={`rounded-lg py-2 transition-all ${
              tab === "signin" ? "bg-white text-slate-900 shadow-sm" : "hover:text-slate-900"
            }`}
          >
            Sign in
          </button>
          <button
            type="button"
            onClick={() => setTab("signup")}
            className={`rounded-lg py-2 transition-all ${
              tab === "signup" ? "bg-white text-slate-900 shadow-sm" : "hover:text-slate-900"
            }`}
          >
            Create account
          </button>
        </div>

        {/* Demo Fast Login */}
        <div className="mt-4">
          <button
            type="button"
            onClick={handleDemo}
            className="w-full flex items-center justify-center gap-2 rounded-xl border border-indigo-200 bg-indigo-50/60 py-2.5 text-xs font-semibold text-indigo-700 hover:bg-indigo-100 transition-colors"
          >
            <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
            <span>One-Click Demo Sign In (Jane Doe)</span>
          </button>
        </div>

        <div className="relative my-5 flex items-center justify-center">
          <div className="w-full border-t border-slate-200" />
          <span className="absolute bg-white px-3 text-[11px] font-medium text-slate-400 uppercase tracking-wider">
            Or with email
          </span>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {tab === "signup" && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Full Name
              </label>
              <div className="relative">
                <UserIcon className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Jane Doe"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/50 pl-10 pr-4 py-2.5 text-sm text-slate-900 focus:bg-white focus:border-indigo-500 focus:outline-none focus:ring-4 focus:ring-indigo-500/10 transition-all"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Email address
            </label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                className="w-full rounded-xl border border-slate-200 bg-slate-50/50 pl-10 pr-4 py-2.5 text-sm text-slate-900 focus:bg-white focus:border-indigo-500 focus:outline-none focus:ring-4 focus:ring-indigo-500/10 transition-all"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
              <input
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full rounded-xl border border-slate-200 bg-slate-50/50 pl-10 pr-10 py-2.5 text-sm text-slate-900 focus:bg-white focus:border-indigo-500 focus:outline-none focus:ring-4 focus:ring-indigo-500/10 transition-all"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3.5 top-3 text-slate-400 hover:text-slate-600"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="w-full flex items-center justify-center gap-2 rounded-xl bg-slate-950 py-3 text-xs font-semibold text-white shadow-md hover:bg-slate-800 transition-all mt-4"
          >
            <span>{tab === "signin" ? "Sign in" : "Create account"}</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-center gap-1.5 text-[11px] text-slate-400">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
          <span>Never a paywall before matching. Guest = try, Account = save.</span>
        </div>
      </div>
    </div>
  );
}
