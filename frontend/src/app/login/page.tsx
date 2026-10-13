"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { AuthForm } from "@/components/auth-form";
import { Sparkles } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen flex flex-col justify-center items-center bg-[#fafaf8] p-6">
      <Link href="/" className="flex items-center gap-2.5 mb-8 hover:opacity-90 transition-opacity">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-600 to-violet-500 text-white shadow-sm">
          <Sparkles className="h-4 w-4" />
        </div>
        <span className="text-lg font-extrabold tracking-tight text-slate-950">
          career<span className="text-purple-600">match</span>
        </span>
      </Link>

      <div className="w-full max-w-md rounded-2xl border border-slate-200/80 bg-white p-8 shadow-xl ring-1 ring-slate-900/5">
        {user ? (
          <div className="text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-purple-600 text-white font-bold text-lg mb-3">
              {user.name.charAt(0).toUpperCase()}
            </div>
            <h1 className="text-lg font-bold text-slate-900">Signed in as {user.name}</h1>
            <p className="text-xs text-slate-500 mt-1">{user.email}</p>
            <div className="mt-6 flex justify-center gap-3">
              <button
                onClick={() => router.push("/offers")}
                className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800"
              >
                Go to offers
              </button>
              <button
                onClick={() => logout()}
                className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
              >
                Sign out
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="text-center pb-5">
              <h1 className="text-2xl font-bold tracking-tight text-slate-950">
                Sign in to careermatch
              </h1>
              <p className="text-xs text-slate-500 mt-1.5">
                Saves the profile already in memory. No need to re-upload your CV.
              </p>
            </div>
            <AuthForm onSuccess={() => router.push("/offers")} />
          </>
        )}
      </div>
    </div>
  );
}
