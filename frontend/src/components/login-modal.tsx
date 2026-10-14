"use client";

import { useState } from "react";
import { useAuth } from "@/context/auth-context";
import {
  X,
  Sparkles,
  Eye,
  EyeOff,
  CheckCircle2,
  Lock,
  Mail,
  User as UserIcon,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";

export function LoginModal() {
  const { isLoginModalOpen, closeLoginModal, login, user, logout } = useAuth();
  const [tab, setTab] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [success, setSuccess] = useState(false);

  if (!isLoginModalOpen) return null;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim() || !password.trim()) return;

    login(email.trim(), name.trim());
    setSuccess(true);
    setTimeout(() => {
      setSuccess(false);
      closeLoginModal();
    }, 800);
  }

  function handleQuickDemoLogin() {
    login("jane.doe@example.com", "Jane Doe");
    setSuccess(true);
    setTimeout(() => {
      setSuccess(false);
      closeLoginModal();
    }, 700);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/40 backdrop-blur-sm transition-opacity"
        onClick={closeLoginModal}
      />

      {/* Modal Dialog */}
      <div className="relative w-full max-w-md overflow-hidden rounded-2xl border border-slate-200/80 bg-white p-7 shadow-2xl ring-1 ring-slate-900/5 sm:p-8 animate-in fade-in zoom-in-95 duration-200">
        {/* Close Button */}
        <button
          type="button"
          onClick={closeLoginModal}
          className="absolute right-4 top-4 rounded-xl p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
        >
          <X className="h-4 w-4" />
        </button>

        {user ? (
          /* Profile Details if already logged in */
          <div className="space-y-5 text-left">
            <div className="flex items-center gap-3.5">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-tr from-indigo-600 to-indigo-800 text-white font-bold text-lg shadow-sm">
                {user.name.charAt(0).toUpperCase()}
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">{user.name}</h3>
                <p className="text-xs text-slate-500 font-mono">{user.email}</p>
                <span className="inline-block mt-1 rounded-md bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700 border border-emerald-200">
                  Active Workspace Session
                </span>
              </div>
            </div>

            <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-4 text-xs text-slate-600 leading-relaxed">
              <p className="font-semibold text-slate-900 mb-1">
                Persistent Profile Storage
              </p>
              Your extracted profiles, job matches, and gap simulations are automatically
              linked to your account.
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-2">
              <button
                type="button"
                onClick={closeLoginModal}
                className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
              >
                Close
              </button>
              <button
                type="button"
                onClick={() => {
                  logout();
                  closeLoginModal();
                }}
                className="rounded-xl bg-rose-600 px-4 py-2 text-xs font-semibold text-white hover:bg-rose-700 transition-colors"
              >
                Sign out
              </button>
            </div>
          </div>
        ) : (
          /* Sign In / Sign Up Form */
          <div>
            {/* Brand Header */}
            <div className="text-center pb-2">
              <div className="mx-auto mb-3 flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-600 text-white shadow-md shadow-indigo-500/20">
                <Sparkles className="h-5 w-5" />
              </div>
              <h2 className="text-xl font-bold tracking-tight text-slate-900">
                {tab === "signin" ? "Welcome back" : "Create your account"}
              </h2>
              <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto">
                Save your matched profile and gaps without re-uploading your CV.
              </p>
            </div>

            {/* Tabs */}
            <div className="mt-5 grid grid-cols-2 rounded-xl bg-slate-100 p-1 text-xs font-semibold text-slate-600">
              <button
                type="button"
                onClick={() => setTab("signin")}
                className={`rounded-lg py-1.5 transition-all ${
                  tab === "signin"
                    ? "bg-white text-slate-900 shadow-sm"
                    : "hover:text-slate-900"
                }`}
              >
                Sign in
              </button>
              <button
                type="button"
                onClick={() => setTab("signup")}
                className={`rounded-lg py-1.5 transition-all ${
                  tab === "signup"
                    ? "bg-white text-slate-900 shadow-sm"
                    : "hover:text-slate-900"
                }`}
              >
                Create account
              </button>
            </div>

            {/* Quick Demo Fill button */}
            <div className="mt-4">
              <button
                type="button"
                onClick={handleQuickDemoLogin}
                className="w-full flex items-center justify-center gap-2 rounded-xl border border-indigo-200 bg-indigo-50/50 py-2 text-xs font-semibold text-indigo-700 hover:bg-indigo-100/60 transition-colors"
              >
                <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
                <span>Instant Sign In as Demo (Jane Doe)</span>
              </button>
            </div>

            <div className="relative my-4 flex items-center justify-center">
              <div className="w-full border-t border-slate-200" />
              <span className="absolute bg-white px-3 text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                Or with email
              </span>
            </div>

            {success ? (
              <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-6 text-center text-xs text-emerald-800 space-y-2">
                <CheckCircle2 className="h-8 w-8 text-emerald-600 mx-auto" />
                <p className="text-sm font-bold text-emerald-950">
                  Signed in successfully!
                </p>
                <p className="text-emerald-700">Linking your active match session...</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-3.5">
                {tab === "signup" && (
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Full Name
                    </label>
                    <div className="relative">
                      <UserIcon className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-400" />
                      <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Jane Doe"
                        className="w-full rounded-xl border border-slate-200 bg-slate-50/50 pl-10 pr-4 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-indigo-500 focus:outline-none focus:ring-4 focus:ring-indigo-500/10 transition-all"
                      />
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Email address
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-400" />
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="name@company.com"
                      className="w-full rounded-xl border border-slate-200 bg-slate-50/50 pl-10 pr-4 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-indigo-500 focus:outline-none focus:ring-4 focus:ring-indigo-500/10 transition-all"
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-xs font-semibold text-slate-700">
                      Password
                    </label>
                    {tab === "signin" && (
                      <span className="text-[11px] font-medium text-indigo-600 hover:text-indigo-700 cursor-pointer">
                        Forgot password?
                      </span>
                    )}
                  </div>
                  <div className="relative">
                    <Lock className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-400" />
                    <input
                      type={showPassword ? "text" : "password"}
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••••••"
                      className="w-full rounded-xl border border-slate-200 bg-slate-50/50 pl-10 pr-10 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-indigo-500 focus:outline-none focus:ring-4 focus:ring-indigo-500/10 transition-all"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3.5 top-2.5 text-slate-400 hover:text-slate-600"
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  className="w-full flex items-center justify-center gap-2 rounded-xl bg-slate-900 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-slate-800 transition-all mt-4"
                >
                  <span>{tab === "signin" ? "Sign in" : "Create account"}</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </button>
              </form>
            )}

            {/* Philosophy Note from wireframe */}
            <div className="mt-5 pt-3.5 border-t border-slate-100 flex items-center justify-center gap-1.5 text-[11px] text-slate-400">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
              <span>Never a paywall before matching. Guest = try, Account = save.</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
