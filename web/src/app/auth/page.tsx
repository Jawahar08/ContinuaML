"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { login, signup } from "../api";
import { Brain, ShieldAlert, ArrowRight } from "lucide-react";

export default function AuthPage() {
  const router = useRouter();
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("admin@continuaml.com");
  const [password, setPassword] = useState("AdminPass123!");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");

    try {
      if (isLogin) {
        const res = await login(email, password);
        localStorage.setItem("token", res.data.access_token);
        router.push("/");
      } else {
        await signup(email, password);
        setMessage("Account created. Please log in using your password.");
        setIsLogin(true);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Authentication session failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#030307] flex items-center justify-center p-6 relative overflow-hidden">
      {/* Decorative Radial Glowing Backdrops */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-[rgba(139,92,246,0.06)] blur-3xl -z-10"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-[rgba(14,165,233,0.03)] blur-3xl -z-10"></div>

      {/* Screen-centered auth sheet */}
      <div className="w-full max-w-md glass-card p-10 border border-[rgba(255,255,255,0.07)] backdrop-blur-md relative">
        <div className="flex flex-col items-center text-center space-y-6">
          
          {/* Logo symbol */}
          <div className="w-10 h-10 rounded bg-[#8b5cf6] flex items-center justify-center shadow-[0_0_20px_rgba(139,92,246,0.4)]">
            <Brain className="w-5 h-5 text-white" />
          </div>

          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              {isLogin ? "Welcome back" : "Establish node credentials"}
            </h1>
            <p className="text-xs text-slate-500 font-mono mt-1.5 uppercase tracking-wider">
              {isLogin ? "ContinuaML Login" : "ContinuaML Register"}
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-5">
          {error && (
            <div className="flex items-center gap-2 p-3.5 rounded bg-red-950/20 border border-red-900/30 text-xs text-red-400 font-mono">
              <ShieldAlert className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {message && (
            <div className="p-3.5 rounded bg-emerald-950/20 border border-emerald-900/30 text-xs text-emerald-400 font-mono">
              {message}
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block" htmlFor="email-input">
              EMAIL ADDRESS
            </label>
            <input
              id="email-input"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="researcher@continuaml.com"
              className="w-full px-3.5 py-2.5 rounded bg-[#09090d] border border-[rgba(255,255,255,0.06)] text-xs text-white placeholder-slate-600 focus:border-[#8b5cf6] focus:ring-1 focus:ring-[#8b5cf6] transition font-mono"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block" htmlFor="password-input">
              PASSWORD
            </label>
            <input
              id="password-input"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full px-3.5 py-2.5 rounded bg-[#09090d] border border-[rgba(255,255,255,0.06)] text-xs text-white placeholder-slate-600 focus:border-[#8b5cf6] focus:ring-1 focus:ring-[#8b5cf6] transition font-mono"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 rounded bg-[#8b5cf6] hover:bg-[#7c3aed] text-white text-xs font-medium transition flex items-center justify-center gap-2 shadow-[0_0_12px_rgba(139,92,246,0.2)]"
          >
            {loading ? (
              <span className="w-3.5 h-3.5 rounded-full border border-white/20 border-t-white animate-spin"></span>
            ) : (
              <>
                <span>{isLogin ? "Authenticate Credentials" : "Initialize Account"}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => {
              setIsLogin(!isLogin);
              setError("");
              setMessage("");
            }}
            className="text-[10px] font-mono uppercase text-[#8b5cf6] hover:text-indigo-400 tracking-wider transition"
          >
            {isLogin ? "Create New Node Profile" : "Login with existing credentials"}
          </button>
        </div>
      </div>
    </main>
  );
}
