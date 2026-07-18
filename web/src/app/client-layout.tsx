"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { 
  Brain, Database, Activity, FileText, Settings, 
  RefreshCw, LogOut, ChevronDown, CheckCircle, HelpCircle 
} from "lucide-react";

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [apiStatus, setApiStatus] = useState<"REAL" | "DEMO">("DEMO");
  const [workspace, setWorkspace] = useState("workspace_default");

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch("http://localhost:8000/health");
        if (res.ok) {
          setApiStatus("REAL");
        } else {
          setApiStatus("DEMO");
        }
      } catch {
        setApiStatus("DEMO");
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { name: "Telemetry Dashboard", path: "/", icon: Activity },
    { name: "Model Registry", path: "/models", icon: Brain },
    { name: "Dataset Manager", path: "/datasets", icon: Database },
    { name: "Experiments & Lineage", path: "/experiments", icon: RefreshCw },
    { name: "Research Reports", path: "/reports", icon: FileText },
  ];

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/auth");
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#05050a] text-slate-100 antialiased">
      {/* Sidebar */}
      <aside className="w-64 bg-[#09090e] border-r border-[rgba(255,255,255,0.06)] flex flex-col justify-between">
        <div>
          {/* Header/Logo */}
          <div className="h-16 px-6 border-b border-[rgba(255,255,255,0.06)] flex items-center gap-3">
            <div className="w-6 h-6 rounded bg-[#8b5cf6] flex items-center justify-center shadow-[0_0_12px_rgba(139,92,246,0.3)]">
              <Brain className="w-3.5 h-3.5 text-white" />
            </div>
            <div>
              <span className="font-semibold text-sm tracking-tight text-white block">
                ContinuaML
              </span>
            </div>
          </div>

          {/* Active Workspace Selector */}
          <div className="p-4 border-b border-[rgba(255,255,255,0.04)]">
            <span className="block text-[9px] uppercase tracking-widest text-slate-500 font-mono mb-2">
              WORKSPACE
            </span>
            <div className="flex items-center justify-between px-3 py-2 rounded-lg bg-[#0e0e15] border border-[rgba(255,255,255,0.05)] hover:border-slate-700 transition cursor-pointer">
              <span className="text-xs font-mono text-slate-300 truncate">{workspace}</span>
              <ChevronDown className="w-3 h-3 text-slate-500" />
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.path;
              return (
                <Link
                  key={item.path}
                  href={item.path}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-xs font-medium transition-all ${
                    isActive
                      ? "bg-slate-900 text-white border-l-2 border-[#8b5cf6]"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/40"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-[#8b5cf6]" : ""}`} />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Footer info */}
        <div className="p-4 border-t border-[rgba(255,255,255,0.06)] space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="truncate max-w-[150px] font-mono text-[11px]">admin@continuaml.com</span>
            <button 
              onClick={handleLogout}
              className="p-1.5 hover:bg-slate-900 rounded text-slate-400 hover:text-red-400 transition"
              title="Sign Out"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
          
          {/* Health status badge */}
          <div className="flex items-center justify-between px-3 py-2 rounded bg-[#09090d] border border-[rgba(255,255,255,0.03)] text-[10px] font-mono">
            <span className="text-slate-500">ENGINE:</span>
            <div className="flex items-center gap-1.5">
              <div className={`w-1.5 h-1.5 rounded-full ${apiStatus === "REAL" ? "bg-emerald-500 shadow-[0_0_8px_#10b981]" : "bg-amber-500 shadow-[0_0_8px_#f59e0b]"}`}></div>
              <span className={apiStatus === "REAL" ? "text-emerald-400 font-semibold" : "text-amber-400"}>
                {apiStatus} MODE
              </span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {apiStatus === "DEMO" && (
          <div className="bg-[#1c120c] border-b border-amber-900/30 px-6 py-2 flex items-center justify-between text-[11px] text-amber-300 font-mono">
            <div className="flex items-center gap-2">
              <HelpCircle className="w-3.5 h-3.5 text-amber-500" />
              <span>Offline / Local Simulated Engine running. Connect backend for live GPU metrics.</span>
            </div>
          </div>
        )}
        
        {/* Container */}
        <div className="flex-1 overflow-y-auto p-8 lg:p-12">
          {children}
        </div>
      </main>
    </div>
  );
}
