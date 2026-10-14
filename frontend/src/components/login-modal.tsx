"use client";

import { useAuth } from "@/context/auth-context";
import { AuthForm } from "./auth-form";
import { X, Sparkles } from "lucide-react";

/** Login overlay (wireframe 05): the current page stays behind, never blocking. */
export function LoginModal() {
  const { isLoginModalOpen, closeLoginModal, user, logout } = useAuth();

  if (!isLoginModalOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="fixed inset-0 bg-slate-950/40 backdrop-blur-sm transition-opacity"
        onClick={closeLoginModal}
      />

      <div
        role="dialog"
        aria-modal="true"
        className="relative w-full max-w-md overflow-hidden rounded-2xl border border-slate-200/80 bg-white p-7 shadow-2xl ring-1 ring-slate-900/5 sm:p-8 animate-in fade-in zoom-in-95 duration-200"
      >
        <button
          type="button"
          onClick={closeLoginModal}
          className="absolute right-4 top-4 rounded-xl p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
          aria-label="Close"
        >
          <X className="h-4 w-4" />
        </button>

        {user ? (
          <div className="space-y-5 text-left">
            <div className="flex items-center gap-3.5">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-tr from-purple-600 to-indigo-600 text-white font-bold text-lg shadow-sm">
                {user.name.charAt(0).toUpperCase()}
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">{user.name}</h3>
                <p className="text-xs text-slate-500 font-mono">{user.email}</p>
              </div>
            </div>

            <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-4 text-xs text-slate-600 leading-relaxed">
              Your profile and matched offers are saved to this account.
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
                onClick={async () => {
                  await logout();
                  closeLoginModal();
                }}
                className="rounded-xl bg-rose-600 px-4 py-2 text-xs font-semibold text-white hover:bg-rose-700 transition-colors"
              >
                Sign out
              </button>
            </div>
          </div>
        ) : (
          <div>
            <div className="text-center pb-5">
              <div className="mx-auto mb-3 flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-tr from-purple-600 to-indigo-600 text-white shadow-md shadow-purple-500/20">
                <Sparkles className="h-5 w-5" />
              </div>
              <h2 className="text-xl font-bold tracking-tight text-slate-900">
                Save your profile
              </h2>
              <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto">
                Saves the profile already in memory. No need to re-upload your CV.
              </p>
            </div>
            <AuthForm onSuccess={closeLoginModal} />
          </div>
        )}
      </div>
    </div>
  );
}
