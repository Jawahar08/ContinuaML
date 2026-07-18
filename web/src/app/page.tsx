"use client";

import React, { useEffect, useState } from "react";
import ClientLayout from "./client-layout";
import { getModels, getDatasets, getExperiments, getJobs, Model, Dataset, Experiment, Job } from "./api";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Brain, Database, RefreshCw, Clock, ArrowUpRight, Cpu } from "lucide-react";
import Link from "next/link";

export default function Dashboard() {
  const [models, setModels] = useState<Model[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [provenance, setProvenance] = useState<"REAL" | "DEMO">("DEMO");

  useEffect(() => {
    const loadDashboardData = async () => {
      setLoading(true);
      try {
        const mRes = await getModels();
        const dRes = await getDatasets();
        const eRes = await getExperiments();
        const jRes = await getJobs();
        
        setModels(mRes.data);
        setDatasets(dRes.data);
        setExperiments(eRes.data);
        setJobs(jRes.data);
        setProvenance(mRes.status);
      } catch (err) {
        setError("Error loading system metrics.");
      } finally {
        setLoading(false);
      }
    };
    loadDashboardData();
  }, []);

  const forgettingCurveData = [
    { task: "TriviaQA (T1)", Baseline: 85, EWC: 85, ExperienceReplay: 85 },
    { task: "GSM8K (T2)", Baseline: 38, EWC: 74, ExperienceReplay: 71 },
    { task: "HumanEval (T3)", Baseline: 12, EWC: 61, ExperienceReplay: 59 },
  ];

  const strategyComparisonData = [
    { name: "Naive FT", accuracy: 51, forgetting: 23 },
    { name: "EWC", accuracy: 73, forgetting: 8 },
    { name: "Replay", accuracy: 71, forgetting: 11 },
  ];

  if (loading) {
    return (
      <ClientLayout>
        <div className="flex flex-col items-center justify-center h-[60vh]">
          <div className="w-8 h-8 rounded-full border-2 border-[rgba(139,92,246,0.15)] border-t-[#8b5cf6] animate-spin mb-4"></div>
          <p className="text-slate-500 font-mono text-[10px] tracking-widest uppercase">Initializing Telemetry...</p>
        </div>
      </ClientLayout>
    );
  }

  return (
    <ClientLayout>
      <div className="space-y-12">
        {/* Header Block with Asymmetric Glow */}
        <div className="relative flex flex-col md:flex-row justify-between items-start md:items-end gap-6 border-b border-[rgba(255,255,255,0.06)] pb-8">
          <div className="absolute top-[-100px] left-[-50px] w-96 h-96 rounded-full bg-[rgba(139,92,246,0.04)] blur-3xl -z-10"></div>
          
          <div>
            <span className="text-[10px] font-mono tracking-widest text-[#8b5cf6] uppercase block mb-1">
              PLATFORM CONSOLE
            </span>
            <h1 className="text-4xl font-semibold tracking-tight text-white">
              ContinuaML
            </h1>

            <p className="text-slate-400 text-xs mt-1.5 max-w-xl leading-relaxed">
              Catastrophic forgetting mitigation registry and live evaluation telemetry metrics.
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <span className="text-[10px] font-mono text-slate-500 uppercase">PROVENANCE LOGS</span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold border ${
              provenance === "REAL" 
                ? "bg-emerald-950/20 border-emerald-800/40 text-emerald-400" 
                : "bg-amber-950/20 border-amber-800/40 text-amber-400"
            }`}>
              {provenance} RUN
            </span>
          </div>
        </div>

        {/* Bento Board Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { label: "Active Models", val: models.length, icon: Brain },
            { label: "Dataset Repos", val: datasets.length, icon: Database },
            { label: "Completed Runs", val: experiments.length, icon: RefreshCw },
            { label: "Active Workers", val: jobs.filter(j => j.status === "running").length, icon: Cpu }
          ].map((stat, i) => (
            <div key={i} className="glass-card p-6 flex items-center justify-between">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 block mb-1">{stat.label}</span>
                <span className="text-2xl font-bold text-white tracking-tight">{stat.val}</span>
              </div>
              <stat.icon className="w-5 h-5 text-slate-600" />
            </div>
          ))}
        </div>

        {/* Asymmetric Bento Layout section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Bento Column 1: Forgetting Curves Line chart (2/3 width) */}
          <div className="lg:col-span-2 glass-card p-8 space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <span className="text-[10px] font-mono uppercase text-[#8b5cf6] tracking-widest block mb-1">METRIC DECAY</span>
                <h3 className="text-base font-medium text-white">Forgetting Curves</h3>
              </div>
              <span className="text-[9px] text-slate-500 font-mono">F = ACCURACY_t1 - ACCURACY_tn</span>
            </div>
            
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={forgettingCurveData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                  <XAxis dataKey="task" stroke="#4b5563" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis stroke="#4b5563" domain={[0, 100]} fontSize={10} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: "#0c0c12", borderColor: "rgba(255,255,255,0.08)" }} labelClassName="text-[11px] font-mono text-slate-400" />
                  <Line type="monotone" dataKey="Baseline" stroke="#ef4444" strokeWidth={1.5} name="FT Baseline" dot={{ r: 3 }} activeDot={{ r: 5 }} />
                  <Line type="monotone" dataKey="EWC" stroke="#8b5cf6" strokeWidth={1.5} name="EWC" dot={{ r: 3 }} activeDot={{ r: 5 }} />
                  <Line type="monotone" dataKey="ExperienceReplay" stroke="#0ea5e9" strokeWidth={1.5} name="Exp Replay" dot={{ r: 3 }} activeDot={{ r: 5 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Structured accessibility data block */}
            <details className="text-[11px] text-slate-500 border-t border-[rgba(255,255,255,0.04)] pt-4">
              <summary className="cursor-pointer hover:text-slate-300 font-mono transition select-none">
                [Telemetry Data Table Alternative]
              </summary>
              <table className="w-full mt-2 text-left text-[11px] font-mono text-slate-400">
                <thead>
                  <tr className="text-slate-500 border-b border-[rgba(255,255,255,0.04)]">
                    <th className="py-1">Task</th>
                    <th className="py-1">Baseline</th>
                    <th className="py-1">EWC</th>
                    <th className="py-1">Exp Replay</th>
                  </tr>
                </thead>
                <tbody>
                  {forgettingCurveData.map((row, i) => (
                    <tr key={i} className="border-b border-[rgba(255,255,255,0.02)]">
                      <td className="py-1">{row.task}</td>
                      <td>{row.Baseline}%</td>
                      <td>{row.EWC}%</td>
                      <td>{row.ExperienceReplay}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </details>
          </div>

          {/* Bento Column 2: Strategy comparisons (1/3 width) */}
          <div className="lg:col-span-1 glass-card p-8 space-y-6">
            <div>
              <span className="text-[10px] font-mono uppercase text-[#8b5cf6] tracking-widest block mb-1">RETENTION AUDIT</span>
              <h3 className="text-base font-medium text-white">Strategy Metrics</h3>
            </div>
            
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={strategyComparisonData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                  <XAxis dataKey="name" stroke="#4b5563" fontSize={9} tickLine={false} axisLine={false} />
                  <YAxis stroke="#4b5563" fontSize={10} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: "#0c0c12", borderColor: "rgba(255,255,255,0.08)" }} />
                  <Bar dataKey="accuracy" fill="#8b5cf6" name="Accuracy" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="forgetting" fill="#f43f5e" name="Forgetting" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Computation Queue */}
        <div className="glass-card p-8 space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <span className="text-[10px] font-mono uppercase text-[#8b5cf6] tracking-widest block mb-1">TELEMETRY POOL</span>
              <h3 className="text-base font-medium text-white">Execution Threads</h3>
            </div>
            <Link href="/experiments" className="text-xs text-[#8b5cf6] hover:text-indigo-400 font-medium flex items-center gap-1">
              <span>Launch Run</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-[rgba(255,255,255,0.06)] text-slate-500 pb-3">
                  <th className="pb-3 font-semibold">JOB ID</th>
                  <th className="pb-3 font-semibold">TYPE</th>
                  <th className="pb-3 font-semibold">PROGRESS</th>
                  <th className="pb-3 font-semibold">STATE</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[rgba(255,255,255,0.03)] text-slate-300">
                {jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-slate-900/10">
                    <td className="py-3.5 text-slate-500 font-mono text-[11px]">{job.id}</td>
                    <td className="py-3.5 uppercase font-medium">{job.job_type.replace("-", " ")}</td>
                    <td className="py-3.5">
                      <div className="flex items-center gap-3">
                        <div className="w-32 bg-slate-950 h-1 rounded-full overflow-hidden border border-[rgba(255,255,255,0.04)]">
                          <div 
                            className="bg-[#8b5cf6] h-full transition-all duration-300"
                            style={{ width: `${job.progress}%` }}
                          ></div>
                        </div>
                        <span className="text-[10px] text-slate-400">{job.progress.toFixed(1)}%</span>
                      </div>
                    </td>
                    <td className="py-3.5">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                        job.status === "succeeded" ? "bg-emerald-950/20 text-emerald-400 border border-emerald-900/30" :
                        job.status === "running" ? "bg-indigo-950/20 text-indigo-400 border border-indigo-900/30 animate-pulse" :
                        "bg-slate-900/40 text-slate-500 border border-slate-800/40"
                      }`}>
                        {job.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </ClientLayout>
  );
}
