"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import ClientLayout from "../../client-layout";
import { getModels, mergeModels, getMerge, Model, ModelMerge } from "../../api";
import { ArrowLeft, GitMerge, Brain, Cpu, Layers, Settings2, CheckCircle2, Loader2, Play } from "lucide-react";

export default function ModelMergePage() {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Form states
  const [parentA, setParentA] = useState("");
  const [parentB, setParentB] = useState("");
  const [mergeMethod, setMergeMethod] = useState("slerp");
  const [mergeRatio, setMergeRatio] = useState(0.5);
  const [mergeName, setMergeName] = useState("");

  // Job tracking states
  const [activeMergeId, setActiveMergeId] = useState<string | null>(null);
  const [activeMerge, setActiveMerge] = useState<ModelMerge | null>(null);
  const [logs, setLogs] = useState<{ content: string; level: string; created_at: string }[]>([]);
  const [jobProgress, setJobProgress] = useState(0);
  const [polling, setPolling] = useState(false);

  useEffect(() => {
    const loadModels = async () => {
      try {
        const res = await getModels();
        setModels(res.data);
        if (res.data.length >= 2) {
          setParentA(`${res.data[0].id}-v1`);
          setParentB(`${res.data[1].id}-v1`);
        } else if (res.data.length === 1) {
          setParentA(`${res.data[0].id}-v1`);
          setParentB(`${res.data[0].id}-v1`);
        }
      } catch (err) {
        setError("Could not load model registry.");
      } finally {
        setLoading(false);
      }
    };
    loadModels();
  }, []);

  // Update default name based on selected models
  useEffect(() => {
    if (parentA && parentB && models.length > 0) {
      const nameA = models.find(m => `${m.id}-v1` === parentA)?.name || "Model A";
      const nameB = models.find(m => `${m.id}-v1` === parentB)?.name || "Model B";
      setMergeName(`Merged-${nameA.split(" ")[0]}-${nameB.split(" ")[0]}`);
    }
  }, [parentA, parentB, models]);

  // Poll job status
  useEffect(() => {
    let intervalId: NodeJS.Timeout;
    if (polling && activeMergeId) {
      const poll = async () => {
        try {
          const res = await getMerge(activeMergeId);
          const merge = res.data.merge;
          setActiveMerge(merge);
          setLogs(res.data.logs);

          // Update progress based on state / logs
          if (merge.status === "succeeded") {
            setJobProgress(100);
            setPolling(false);
          } else if (merge.status === "failed") {
            setJobProgress(0);
            setPolling(false);
          } else if (merge.status === "running") {
            // Dynamically estimate based on log count or just show 50%
            setJobProgress(prev => Math.min(prev + 10, 90));
          }
        } catch (err) {
          console.error("Error polling merge status:", err);
        }
      };
      // Poll every 1.5 seconds
      intervalId = setInterval(poll, 1500);
      poll();
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [polling, activeMergeId]);

  const handleStartMerge = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!parentA || !parentB) {
      setError("Please select both parent models.");
      return;
    }

    setJobProgress(10);
    setLogs([{ content: "Submitting merge request to coordinator...", level: "INFO", created_at: new Date().toISOString() }]);
    
    try {
      const payload: ModelMerge = {
        name: mergeName || "Derivative Model Merge",
        parent_a_version_id: parentA,
        parent_b_version_id: parentB,
        merge_method: mergeMethod,
        merge_ratio: mergeRatio
      };

      const res = await mergeModels(payload);
      if (res.data.id) {
        setActiveMergeId(res.data.id);
        setActiveMerge(res.data);
        setPolling(true);
      }
    } catch (err: any) {
      setError(err.message || "Failed to submit merge job.");
    }
  };

  const modelAInfo = models.find(m => `${m.id}-v1` === parentA);
  const modelBInfo = models.find(m => `${m.id}-v1` === parentB);
  const isArchitectureMismatch = modelAInfo && modelBInfo && modelAInfo.architecture !== modelBInfo.architecture;

  if (loading) {
    return (
      <ClientLayout>
        <div className="flex flex-col items-center justify-center h-[50vh]">
          <Loader2 className="w-8 h-8 text-[#8b5cf6] animate-spin mb-4" />
          <p className="text-slate-500 font-mono text-[10px] tracking-widest uppercase">Querying Registry...</p>
        </div>
      </ClientLayout>
    );
  }

  return (
    <ClientLayout>
      <div className="space-y-8 max-w-6xl mx-auto">
        {/* Back and Header */}
        <div className="flex items-center gap-4">
          <Link
            href="/models"
            className="p-2 rounded bg-slate-900 border border-[rgba(255,255,255,0.05)] hover:border-slate-700 text-slate-400 hover:text-white transition"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono tracking-widest text-[#8b5cf6] uppercase">
                RESEARCH LABORATORIES
              </span>
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-ping"></span>
            </div>
            <h1 className="text-3xl font-semibold tracking-tight text-white flex items-center gap-2.5">
              <GitMerge className="w-7 h-7 text-[#8b5cf6]" />
              Model Merging Playground
            </h1>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-950/20 border border-red-900/30 text-red-400 text-xs rounded font-mono">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Form and Controls Column (2/3) */}
          <div className="lg:col-span-2 space-y-6">
            <form onSubmit={handleStartMerge} className="glass-card p-6 md:p-8 space-y-8">
              
              {/* Step 1: Parent Selection */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-xs font-semibold text-white uppercase tracking-wider font-mono">
                  <span className="w-5 h-5 rounded-full bg-slate-900 border border-slate-700 text-[#8b5cf6] flex items-center justify-center text-[10px]">1</span>
                  <span>Select Parent Models to Intersect</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Parent Model A */}
                  <div className="space-y-2">
                    <label className="block text-[10px] font-mono uppercase text-slate-500">Parent Model A</label>
                    <select
                      value={parentA}
                      onChange={(e) => setParentA(e.target.value)}
                      className="w-full bg-[#05050a] border border-[rgba(255,255,255,0.06)] focus:border-[#8b5cf6] rounded px-3 py-2.5 text-xs text-white focus:outline-none transition"
                    >
                      {models.map(m => (
                        <option key={m.id} value={`${m.id}-v1`}>{m.name} ({m.architecture})</option>
                      ))}
                    </select>

                    {modelAInfo && (
                      <div className="p-3 bg-[#05050a]/60 border border-[rgba(255,255,255,0.03)] rounded space-y-1 text-[11px] text-slate-400 font-mono">
                        <div className="flex justify-between"><span className="text-slate-600">Params:</span> <span>{(modelAInfo.param_count / 1e9).toFixed(1)}B</span></div>
                        <div className="flex justify-between"><span className="text-slate-600">Context:</span> <span>{modelAInfo.context_length}</span></div>
                        <div className="flex justify-between truncate"><span className="text-slate-600">Source:</span> <span className="truncate">{modelAInfo.source}</span></div>
                      </div>
                    )}
                  </div>

                  {/* Parent Model B */}
                  <div className="space-y-2">
                    <label className="block text-[10px] font-mono uppercase text-slate-500">Parent Model B</label>
                    <select
                      value={parentB}
                      onChange={(e) => setParentB(e.target.value)}
                      className="w-full bg-[#05050a] border border-[rgba(255,255,255,0.06)] focus:border-[#8b5cf6] rounded px-3 py-2.5 text-xs text-white focus:outline-none transition"
                    >
                      {models.map(m => (
                        <option key={m.id} value={`${m.id}-v1`}>{m.name} ({m.architecture})</option>
                      ))}
                    </select>

                    {modelBInfo && (
                      <div className="p-3 bg-[#05050a]/60 border border-[rgba(255,255,255,0.03)] rounded space-y-1 text-[11px] text-slate-400 font-mono">
                        <div className="flex justify-between"><span className="text-slate-600">Params:</span> <span>{(modelBInfo.param_count / 1e9).toFixed(1)}B</span></div>
                        <div className="flex justify-between"><span className="text-slate-600">Context:</span> <span>{modelBInfo.context_length}</span></div>
                        <div className="flex justify-between truncate"><span className="text-slate-600">Source:</span> <span className="truncate">{modelBInfo.source}</span></div>
                      </div>
                    )}
                  </div>
                </div>

                {isArchitectureMismatch && (
                  <div className="p-3 bg-amber-950/20 border border-amber-900/30 text-amber-400 text-[11px] rounded font-mono">
                    ⚠️ <strong>Architecture Mismatch:</strong> Merging models of different architectures ({modelAInfo?.architecture} vs {modelBInfo?.architecture}) is highly experimental and may result in catastrophic structural anomalies.
                  </div>
                )}
              </div>

              {/* Step 2: Merge Method */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-xs font-semibold text-white uppercase tracking-wider font-mono">
                  <span className="w-5 h-5 rounded-full bg-slate-900 border border-slate-700 text-[#8b5cf6] flex items-center justify-center text-[10px]">2</span>
                  <span>Select Weight Intersect Method</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {[
                    { id: "slerp", name: "SLERP", desc: "Spherical Linear Interpolation. Aligns weight representations spherically to maintain activation scale." },
                    { id: "ties", name: "TIES-Merging", desc: "Consensus-based sign agreement. Resolves weight conflict polarity and prunes redundant shifts." },
                    { id: "dare", name: "DARE-Merging", desc: "Drops delta shifts randomly to prevent saturation and rescales parameters to lock variance." }
                  ].map(m => (
                    <div
                      key={m.id}
                      onClick={() => setMergeMethod(m.id)}
                      className={`p-4 rounded-lg border cursor-pointer transition flex flex-col justify-between ${
                        mergeMethod === m.id
                          ? "bg-slate-900/60 border-[#8b5cf6]/60 text-white"
                          : "bg-[#05050a] border-[rgba(255,255,255,0.05)] text-slate-400 hover:border-slate-800"
                      }`}
                    >
                      <div>
                        <span className="text-xs font-semibold block">{m.name}</span>
                        <p className="text-[10px] text-slate-500 mt-2 leading-normal">{m.desc}</p>
                      </div>
                      <span className={`w-2.5 h-2.5 rounded-full mt-4 self-end ${mergeMethod === m.id ? "bg-[#8b5cf6]" : "bg-slate-800"}`}></span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Step 3: Interpolation Ratio & Name */}
              <div className="space-y-6">
                <div className="flex items-center gap-2 text-xs font-semibold text-white uppercase tracking-wider font-mono">
                  <span className="w-5 h-5 rounded-full bg-slate-900 border border-slate-700 text-[#8b5cf6] flex items-center justify-center text-[10px]">3</span>
                  <span>Merge Settings</span>
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between text-[10px] font-mono uppercase">
                    <span className="text-slate-500">Weight Bias: {modelAInfo?.name || "Model A"}</span>
                    <span className="text-[#8b5cf6] font-bold">{Math.round((1 - mergeRatio) * 100)}% / {Math.round(mergeRatio * 100)}%</span>
                    <span className="text-slate-500">{modelBInfo?.name || "Model B"}</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={mergeRatio}
                    onChange={(e) => setMergeRatio(parseFloat(e.target.value))}
                    className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-[#8b5cf6]"
                  />
                </div>

                <div className="space-y-2">
                  <label className="block text-[10px] font-mono uppercase text-slate-500">Destination Model Version Tag</label>
                  <input
                    type="text"
                    required
                    value={mergeName}
                    onChange={(e) => setMergeName(e.target.value)}
                    placeholder="e.g. Merged-TinyLlama-Phi"
                    className="w-full bg-[#05050a] border border-[rgba(255,255,255,0.06)] focus:border-[#8b5cf6] rounded px-3 py-2.5 text-xs text-white focus:outline-none transition font-mono"
                  />
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={polling || !parentA || !parentB}
                className="w-full flex items-center justify-center gap-2 py-3 text-xs font-semibold text-white bg-[#8b5cf6] hover:bg-[#7c3aed] transition-all rounded-md shadow-[0_0_15px_rgba(139,92,246,0.15)] hover:shadow-[0_0_20px_rgba(139,92,246,0.3)] disabled:opacity-50"
              >
                {polling ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Executing Weight Interpolation...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-white" />
                    Initiate Model Merge
                  </>
                )}
              </button>

            </form>
          </div>

          {/* Progress / Outputs Column (1/3) */}
          <div className="lg:col-span-1 space-y-6">
            <div className="glass-card p-6 space-y-6 flex flex-col h-full min-h-[500px]">
              <div className="border-b border-[rgba(255,255,255,0.05)] pb-4">
                <h3 className="text-xs font-semibold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                  <Settings2 className="w-4 h-4 text-[#8b5cf6]" />
                  Execution Console
                </h3>
                <span className="text-[10px] text-slate-500 font-mono block mt-1">Live task queue observer</span>
              </div>

              {!activeMergeId ? (
                <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-slate-500 font-mono text-[10px] leading-relaxed">
                  <GitMerge className="w-12 h-12 text-slate-700 mb-3 animate-pulse" />
                  WAITING FOR SCIENTIFIC MERGING JOB SUBMISSION
                </div>
              ) : (
                <div className="flex-1 flex flex-col justify-between space-y-6">
                  {/* Job Details Card */}
                  <div className="bg-[#05050a] border border-[rgba(255,255,255,0.04)] rounded-lg p-4 space-y-3 font-mono text-[10px]">
                    <div className="flex justify-between"><span className="text-slate-500">Merge Job ID:</span> <span className="text-slate-300 font-bold">{activeMergeId.slice(0, 14)}...</span></div>
                    <div className="flex justify-between"><span className="text-slate-500">Status:</span> 
                      <span className={`px-2 py-0.5 rounded uppercase font-semibold ${
                        activeMerge?.status === "succeeded" ? "bg-emerald-950/20 text-emerald-400 border border-emerald-900/30" :
                        activeMerge?.status === "failed" ? "bg-red-950/20 text-red-400 border border-red-900/30" :
                        "bg-indigo-950/20 text-indigo-400 border border-indigo-900/30 animate-pulse"
                      }`}>{activeMerge?.status || "queued"}</span>
                    </div>

                    {/* Progress Bar */}
                    <div className="space-y-1.5 pt-2">
                      <div className="flex justify-between text-[9px] text-slate-400"><span>Progress</span> <span>{jobProgress}%</span></div>
                      <div className="w-full bg-slate-950 h-1.5 rounded overflow-hidden">
                        <div
                          className="bg-[#8b5cf6] h-full transition-all duration-500 rounded"
                          style={{ width: `${jobProgress}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>

                  {/* Scrolling Log console */}
                  <div className="flex-1 bg-black border border-slate-900 rounded p-4 font-mono text-[9px] text-slate-400 overflow-y-auto max-h-60 space-y-2 flex flex-col">
                    {logs.map((log, idx) => (
                      <div key={idx} className="leading-relaxed">
                        <span className="text-slate-600">[{log.level || "INFO"}]</span> {log.content}
                      </div>
                    ))}
                    {polling && (
                      <div className="flex items-center gap-1.5 text-slate-500 italic mt-auto">
                        <Loader2 className="w-2.5 h-2.5 animate-spin" />
                        Listening for compiler states...
                      </div>
                    )}
                  </div>

                  {/* Successful Merge Outputs */}
                  {activeMerge?.status === "succeeded" && (
                    <div className="bg-emerald-950/10 border border-emerald-900/20 rounded p-4 text-center space-y-3">
                      <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
                      <div>
                        <h4 className="text-xs font-semibold text-white">Merge Completed</h4>
                        <p className="text-[10px] text-slate-400 mt-1 leading-normal">
                          The weight tensors were successfully interpolated and saved as a new artifact.
                        </p>
                      </div>
                      <Link
                        href="/models"
                        className="block w-full py-2 text-center text-[10px] font-semibold text-emerald-400 bg-emerald-950/30 border border-emerald-900/30 hover:bg-emerald-900/20 rounded transition"
                      >
                        Open Model Registry
                      </Link>
                    </div>
                  )}
                </div>
              )}

            </div>
          </div>
        </div>

      </div>
    </ClientLayout>
  );
}
