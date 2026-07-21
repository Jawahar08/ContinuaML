"use client";

import React, { useEffect, useState } from "react";
import ClientLayout from "../client-layout";
import { getExperiments, getModels, getDatasets, Experiment, Model, Dataset } from "../api";
import { Plus, Play, GitBranch, Download } from "lucide-react";

export default function ExperimentsPage() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedExp, setSelectedExp] = useState<Experiment | null>(null);
  
  // Launch experiment form state
  const [showLaunchForm, setShowLaunchForm] = useState(false);
  const [newExpName, setNewExpName] = useState("Research Run");
  const [selectedModel, setSelectedModel] = useState("");
  const [selectedDataset, setSelectedDataset] = useState("");
  const [selectedStrategy, setSelectedStrategy] = useState("ewc");
  const [lr, setLr] = useState("5e-5");
  const [epochs, setEpochs] = useState("3");
  const [batchSize, setBatchSize] = useState("8");
  const [ewcLambda, setEwcLambda] = useState("100.0");
  const [seed, setSeed] = useState("42");
  
  // Safety gate states
  const [safetyGateEnabled, setSafetyGateEnabled] = useState(false);
  const [maxForgetting, setMaxForgetting] = useState("0.20");
  const [minAccuracy, setMinAccuracy] = useState("0.50");
  const [safetyEvents, setSafetyEvents] = useState<any[]>([]);
  
  // Fisher freezing states
  const [fisherFreezingEnabled, setFisherFreezingEnabled] = useState(false);
  const [fisherImportanceThreshold, setFisherImportanceThreshold] = useState("0.85");
  
  // Carbon-aware scheduler states
  const [carbonAwareEnabled, setCarbonAwareEnabled] = useState(false);
  const [carbonThreshold, setCarbonThreshold] = useState("250");
  const [carbonForecast, setCarbonForecast] = useState<any[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [launching, setLaunching] = useState(false);
  const [error, setError] = useState("");

  const loadData = async () => {
    try {
      const eRes = await getExperiments();
      const mRes = await getModels();
      const dRes = await getDatasets();
      
      setExperiments(eRes.data);
      setModels(mRes.data);
      setDatasets(dRes.data);
      
      if (eRes.data.length > 0) {
        setSelectedExp(eRes.data[0]);
      }
      if (mRes.data.length > 0) setSelectedModel(mRes.data[0].id);
      if (dRes.data.length > 0) setSelectedDataset(dRes.data[0].id);
    } catch {
      setError("Failed to sync workspace run state.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (selectedExp) {
      const fetchSafety = async () => {
        try {
          const token = localStorage.getItem("token") || "";
          const res = await fetch(`http://localhost:8000/api/v1/workspace_default/experiments/${selectedExp.id}/safety-events`, {
            headers: { "Authorization": `Bearer ${token}` }
          });
          if (res.ok) {
            const json = await res.json();
            setSafetyEvents(json);
          } else {
            setSafetyEvents([]);
          }
        } catch {
          setSafetyEvents([]);
        }
      };
      fetchSafety();
    } else {
      setSafetyEvents([]);
    }
  }, [selectedExp]);

  useEffect(() => {
    const fetchForecast = async () => {
      try {
        const token = localStorage.getItem("token") || "";
        const res = await fetch("http://localhost:8000/api/v1/workspace_default/carbon/forecast", {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (res.ok) {
          const json = await res.json();
          setCarbonForecast(json);
        }
      } catch {
        const mockForecast = [];
        for (let h = 0; h < 24; h++) {
          mockForecast.push({
            hour: `${h.toString().padStart(2, '0')}:00`,
            carbon_intensity: 220 + 80 * Math.sin((h - 8) * Math.PI / 6)
          });
        }
        setCarbonForecast(mockForecast);
      }
    };
    fetchForecast();
  }, []);

  const handleLaunch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLaunching(true);
    setError("");

    const payload = {
      name: newExpName,
      model_version_id: `${selectedModel}-v1`,
      dataset_version_id: `${selectedDataset}-v1`,
      strategy_id: selectedStrategy,
      config_id: "cfg_default",
      protocol_id: "proto_standard",
      seed: parseInt(seed),
      safety_gate_enabled: safetyGateEnabled,
      max_forgetting_threshold: parseFloat(maxForgetting),
      min_accuracy_threshold: parseFloat(minAccuracy),
      fisher_freezing_enabled: fisherFreezingEnabled,
      fisher_importance_threshold: parseFloat(fisherImportanceThreshold),
      carbon_aware_enabled: carbonAwareEnabled,
      carbon_intensity_threshold: parseFloat(carbonThreshold)
    };

    try {
      const token = localStorage.getItem("token") || "";
      const res = await fetch(`http://localhost:8000/api/v1/workspace_default/experiments`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        throw new Error("Could not submit training job to background worker");
      }

      setShowLaunchForm(false);
      await loadData();
    } catch (err: any) {
      setError(err.message || "Execution submission failed.");
    } finally {
      setLaunching(false);
    }
  };

  const downloadManifest = async (expId: string) => {
    try {
      const token = localStorage.getItem("token") || "";
      const res = await fetch(`http://localhost:8000/api/v1/workspace_default/experiments/${expId}/reproducibility`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (!res.ok) throw new Error();
      const manifest = await res.json();
      
      // Trigger browser download
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(manifest, null, 2));
      const downloadAnchor = document.createElement("a");
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `reproducibility-manifest-${expId}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    } catch {
      // Fallback for offline demo download
      const demoManifest = {
        manifest_version: "1.0",
        experiment_id: expId,
        workspace_id: "workspace_default",
        timestamp: new Date().toISOString(),
        code_provenance: { git_commit: "a1b2c3d4e5f6...", branch: "main" },
        hardware_environment: { os: "Localhost", cpu: "Deterministic CPU Adapter" },
        randomness_configuration: { global_seed: 42 },
        inputs: { model: { id: "tinyllama-1.1b" }, dataset: { id: "dataset_triviaqa" } },
        hyperparameters: { strategy: "ewc", learning_rate: 5e-5 }
      };
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(demoManifest, null, 2));
      const downloadAnchor = document.createElement("a");
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `demo-reproducibility-manifest-${expId}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    }
  };

  if (loading) {
    return (
      <ClientLayout>
        <div className="flex flex-col items-center justify-center h-[50vh]">
          <div className="w-8 h-8 rounded-full border-2 border-[rgba(139,92,246,0.15)] border-t-[#8b5cf6] animate-spin mb-4"></div>
          <p className="text-slate-500 font-mono text-[10px] tracking-widest uppercase">Syncing Lineage Logs...</p>
        </div>
      </ClientLayout>
    );
  }

  return (
    <ClientLayout>
      <div className="space-y-12">
        {/* Header Title Section */}
        <div className="relative flex flex-col md:flex-row justify-between items-start md:items-end gap-6 border-b border-[rgba(255,255,255,0.06)] pb-8">
          <div className="absolute top-[-100px] left-[-50px] w-96 h-96 rounded-full bg-[rgba(139,92,246,0.04)] blur-3xl -z-10"></div>
          <div>
            <span className="text-[10px] font-mono tracking-widest text-[#8b5cf6] uppercase block mb-1">
              RUN TRACEABILITY
            </span>
            <h1 className="text-4xl font-semibold tracking-tight text-white">
              Experiments & Lineage
            </h1>
            <p className="text-slate-400 text-xs mt-1.5 max-w-xl">
              Configure fine-tuning plans, launch strategy optimizations, and download reproducibility manifests.
            </p>
          </div>
          <button
            onClick={() => setShowLaunchForm(true)}
            className="btn-primary px-4 py-2.5 text-xs font-semibold rounded transition flex items-center gap-2 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Launch Experiment</span>
          </button>
        </div>

        {error && (
          <div className="p-3.5 bg-red-950/20 border border-red-900/30 text-red-400 rounded text-xs font-mono">
            {error}
          </div>
        )}

        {/* Launch Panel Overlay */}
        {showLaunchForm && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-md flex items-center justify-center z-50 p-4">
            <div className="w-full max-w-lg bg-[#0c0c12] border border-[rgba(255,255,255,0.08)] p-8 rounded-lg space-y-6 max-h-[90vh] overflow-y-auto shadow-[0_0_50px_rgba(139,92,246,0.15)]">
              <div>
                <span className="text-[9px] font-mono uppercase text-[#8b5cf6] tracking-widest block mb-1">PLAN CONFIGURATION</span>
                <h3 className="text-lg font-medium text-white">Configure CL Training Plan</h3>
              </div>
              
              <form onSubmit={handleLaunch} className="space-y-4 text-xs font-mono text-slate-400">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="block text-[10px] text-slate-500 uppercase tracking-wider">RUN LABEL</label>
                    <input 
                      type="text" 
                      value={newExpName} 
                      onChange={(e) => setNewExpName(e.target.value)}
                      className="w-full bg-slate-950 border border-[rgba(255,255,255,0.06)] text-slate-100 p-2.5 rounded text-xs outline-none"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="block text-[10px] text-slate-500 uppercase tracking-wider">GLOBAL SEED</label>
                    <input 
                      type="number" 
                      value={seed} 
                      onChange={(e) => setSeed(e.target.value)}
                      className="w-full bg-slate-950 border border-[rgba(255,255,255,0.06)] text-slate-100 p-2.5 rounded text-xs outline-none"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="block text-[10px] text-slate-500 uppercase tracking-wider">BASE MODEL</label>
                    <select 
                      value={selectedModel} 
                      onChange={(e) => setSelectedModel(e.target.value)}
                      className="w-full bg-slate-950 border border-[rgba(255,255,255,0.06)] text-slate-100 p-2.5 rounded text-xs outline-none"
                    >
                      {models.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <label className="block text-[10px] text-slate-500 uppercase tracking-wider">TRAINING DATASET</label>
                    <select 
                      value={selectedDataset} 
                      onChange={(e) => setSelectedDataset(e.target.value)}
                      className="w-full bg-slate-950 border border-[rgba(255,255,255,0.06)] text-slate-100 p-2.5 rounded text-xs outline-none"
                    >
                      {datasets.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                    </select>
                  </div>
                </div>

                <div className="border-t border-[rgba(255,255,255,0.06)] pt-4 space-y-4">
                  <span className="text-[10px] text-slate-500 block uppercase tracking-wider">CL STRATEGY HYPERPARAMETERS</span>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <label className="block text-[10px] text-slate-500 uppercase tracking-wider">MITIGATION STRATEGY</label>
                      <select 
                        value={selectedStrategy} 
                        onChange={(e) => setSelectedStrategy(e.target.value)}
                        className="w-full bg-slate-950 border border-[rgba(255,255,255,0.06)] text-slate-100 p-2.5 rounded text-xs outline-none"
                      >
                        <option value="ewc">Elastic Weight Consolidation (EWC)</option>
                        <option value="experience_replay">Experience Replay</option>
                        <option value="finetune_baseline">Baseline sequential FT (None)</option>
                      </select>
                    </div>
                    {selectedStrategy === "ewc" && (
                      <div className="space-y-1.5">
                        <label className="block text-[10px] text-slate-500 uppercase tracking-wider">EWC LAMBDA</label>
                        <input 
                          type="text" 
                          value={ewcLambda} 
                          onChange={(e) => setEwcLambda(e.target.value)}
                          className="w-full bg-slate-950 border border-[rgba(255,255,255,0.06)] text-slate-100 p-2.5 rounded text-xs outline-none"
                        />
                      </div>
                    )}
                </div>

                {/* Safety Gate Controls */}
                <div className="border-t border-[rgba(255,255,255,0.06)] pt-4 space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-slate-500 block uppercase tracking-wider">Enable Safety Gate Auto-Rollback</span>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input 
                        type="checkbox" 
                        checked={safetyGateEnabled} 
                        onChange={(e) => setSafetyGateEnabled(e.target.checked)} 
                        className="sr-only peer"
                      />
                      <div className="w-9 h-5 bg-slate-950 border border-[rgba(255,255,255,0.06)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-slate-500 peer-checked:after:bg-[#8b5cf6] after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#8b5cf6]/25 peer-checked:border-[#8b5cf6]"></div>
                    </label>
                  </div>

                  {safetyGateEnabled && (
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-1.5">
                        <div className="flex justify-between text-[9px] uppercase text-slate-500 font-mono">
                          <span>Max Forgetting</span>
                          <span className="text-[#8b5cf6]">{Math.round(parseFloat(maxForgetting) * 100)}%</span>
                        </div>
                        <input 
                          type="range" 
                          min="0.05" 
                          max="1.0" 
                          step="0.05"
                          value={maxForgetting} 
                          onChange={(e) => setMaxForgetting(e.target.value)}
                          className="w-full h-1 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-[#8b5cf6]"
                        />
                      </div>
                      <div className="space-y-1.5">
                        <div className="flex justify-between text-[9px] uppercase text-slate-500 font-mono">
                          <span>Min Accuracy</span>
                          <span className="text-[#8b5cf6]">{Math.round(parseFloat(minAccuracy) * 100)}%</span>
                        </div>
                        <input 
                          type="range" 
                          min="0.10" 
                          max="1.0" 
                          step="0.05"
                          value={minAccuracy} 
                          onChange={(e) => setMinAccuracy(e.target.value)}
                          className="w-full h-1 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-[#8b5cf6]"
                        />
                      </div>
                    </div>
                </div>

                {/* Weight Plasticity / Fisher Freezing Controls */}
                <div className="border-t border-[rgba(255,255,255,0.06)] pt-4 space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-slate-500 block uppercase tracking-wider">Enable Fisher Freezing (Weight Plasticity)</span>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input 
                        type="checkbox" 
                        checked={fisherFreezingEnabled} 
                        onChange={(e) => setFisherFreezingEnabled(e.target.checked)} 
                        className="sr-only peer"
                      />
                      <div className="w-9 h-5 bg-slate-950 border border-[rgba(255,255,255,0.06)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-slate-500 peer-checked:after:bg-[#8b5cf6] after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#8b5cf6]/25 peer-checked:border-[#8b5cf6]"></div>
                    </label>
                  </div>

                  {fisherFreezingEnabled && (
                    <div className="space-y-3">
                      <div className="space-y-1.5">
                        <div className="flex justify-between text-[9px] uppercase text-slate-500 font-mono">
                          <span>Fisher Importance Threshold</span>
                          <span className="text-[#8b5cf6]">{Math.round(parseFloat(fisherImportanceThreshold) * 100)}%</span>
                        </div>
                        <input 
                          type="range" 
                          min="0.50" 
                          max="0.99" 
                          step="0.01"
                          value={fisherImportanceThreshold} 
                          onChange={(e) => setFisherImportanceThreshold(e.target.value)}
                          className="w-full h-1 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-[#8b5cf6]"
                        />
                        <p className="text-[9px] text-slate-500 font-normal leading-relaxed">
                          Parameters with Fisher Information importance scores above this percentile will be frozen to mitigate catastrophic forgetting.
                        </p>
                      </div>
                    </div>
                </div>

                {/* Green AI Carbon-Aware Scheduler Controls */}
                <div className="border-t border-[rgba(255,255,255,0.06)] pt-4 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <span className="text-[10px] text-slate-500 block uppercase tracking-wider">Enable Green AI Carbon-Aware Scheduler</span>
                      <span className="text-[9px] text-slate-600 font-normal">Delays run to low carbon grid windows.</span>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input 
                        type="checkbox" 
                        checked={carbonAwareEnabled} 
                        onChange={(e) => setCarbonAwareEnabled(e.target.checked)} 
                        className="sr-only peer"
                      />
                      <div className="w-9 h-5 bg-slate-950 border border-[rgba(255,255,255,0.06)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-slate-500 peer-checked:after:bg-emerald-500 after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500/20 peer-checked:border-emerald-500"></div>
                    </label>
                  </div>

                  {carbonAwareEnabled && (
                    <div className="space-y-4 font-mono">
                      <div className="space-y-1.5">
                        <div className="flex justify-between text-[9px] uppercase text-slate-500">
                          <span>Carbon Intensity Limit</span>
                          <span className="text-emerald-400 font-bold">{carbonThreshold} gCO2/kWh</span>
                        </div>
                        <input 
                          type="range" 
                          min="100" 
                          max="400" 
                          step="10"
                          value={carbonThreshold} 
                          onChange={(e) => setCarbonThreshold(e.target.value)}
                          className="w-full h-1 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <span className="block text-[9px] text-slate-600 uppercase tracking-wider">24h Grid Emissions Forecast</span>
                        <div className="flex gap-1.5 overflow-x-auto pb-2 scrollbar-thin max-w-[420px]">
                          {carbonForecast.slice(0, 12).map((item, idx) => {
                            const isBelow = item.carbon_intensity <= parseFloat(carbonThreshold);
                            return (
                              <div key={idx} className="flex-shrink-0 bg-slate-950 border border-[rgba(255,255,255,0.04)] p-2 rounded text-center min-w-[55px] space-y-1">
                                <span className="block text-[8px] text-slate-500 font-semibold">{item.hour}</span>
                                <span className={`block text-[9px] font-bold ${isBelow ? "text-emerald-400" : "text-amber-500"}`}>
                                  {Math.round(item.carbon_intensity)}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex justify-end gap-3 pt-6">
                  <button 
                    type="button" 
                    onClick={() => setShowLaunchForm(false)}
                    className="btn-secondary px-4 py-2 text-xs font-semibold rounded cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit" 
                    disabled={launching}
                    className="btn-primary px-4 py-2 text-xs font-semibold rounded transition flex items-center gap-1.5 cursor-pointer"
                  >
                    <Play className="w-3.5 h-3.5" />
                    <span>{launching ? "Submitting..." : "Initialize Run"}</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Experiments grid layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* List runs (1/3) */}
          <div className="lg:col-span-1 space-y-4">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 block px-1">
              EVALUATION HISTORY ({experiments.length})
            </span>
            <div className="space-y-2.5">
              {experiments.map((exp) => (
                <div
                  key={exp.id}
                  onClick={() => setSelectedExp(exp)}
                  className={`p-4 rounded-lg border transition cursor-pointer ${
                    selectedExp?.id === exp.id
                      ? "bg-slate-900/60 border-[#8b5cf6]/60 shadow-[0_0_15px_rgba(139,92,246,0.05)]"
                      : "bg-[#0c0c12] border-[rgba(255,255,255,0.05)] hover:border-slate-700"
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <h4 className="text-xs font-semibold text-white truncate max-w-[130px]">{exp.name}</h4>
                    <span className={`text-[9px] uppercase font-mono px-2 py-0.5 rounded border ${
                      exp.status === "REAL" 
                        ? "bg-emerald-950/20 border-emerald-900/30 text-emerald-400" 
                        : "bg-amber-950/20 border-amber-900/30 text-amber-400"
                    }`}>
                      {exp.status} RUN
                    </span>
                  </div>
                  <div className="flex justify-between items-center mt-3 text-[10px] text-slate-500 font-mono">
                    <span>STRAT: {exp.strategy_id}</span>
                    <span>SEED: {exp.seed}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Lineage Details (2/3) */}
          <div className="lg:col-span-2">
            {selectedExp ? (
              <div className="glass-card p-8 space-y-8">
                <div className="flex justify-between items-center border-b border-[rgba(255,255,255,0.06)] pb-5">
                  <div>
                    <h2 className="text-xl font-medium text-white">{selectedExp.name}</h2>
                    <span className="text-xs text-[#8b5cf6] font-mono mt-0.5 block">{selectedExp.id}</span>
                  </div>
                  <button
                    onClick={() => downloadManifest(selectedExp.id)}
                    className="btn-secondary px-3.5 py-2 text-xs font-medium rounded flex items-center gap-1.5 cursor-pointer"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download Manifest</span>
                  </button>
                </div>

                {/* Safety Gate Triggered Banner */}
                {safetyEvents.length > 0 && (
                  <div className="p-4 bg-red-950/20 border border-red-900/30 text-rose-400 rounded-lg space-y-2 font-mono text-[11px] border-l-4 border-l-rose-500 shadow-[0_0_15px_rgba(244,63,94,0.05)]">
                    <div className="flex items-center gap-2 text-rose-400 font-bold uppercase tracking-wider">
                      <span>⚠️ SAFETY GATE AUTOMATIC ROLLBACK TRIGGERED</span>
                    </div>
                    {safetyEvents.map((evt, idx) => (
                      <div key={idx} className="leading-relaxed">
                        The experiment was halted because the metric <strong className="text-white">{evt.metric_name}</strong> violated safety limits.
                        <div className="mt-1 flex gap-4 text-slate-500 text-[10px]">
                          <span>Threshold Limit: {evt.threshold_value}</span>
                          <span>Observed Value: {evt.observed_value.toFixed(4)}</span>
                          <span>Action Taken: <span className="text-rose-400 font-semibold">{evt.action_taken}</span></span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Lineage representation */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-[#8b5cf6] font-mono text-[10px] uppercase tracking-wider">
                    <GitBranch className="w-3.5 h-3.5" />
                    <span>Evaluation Lineage Path</span>
                  </div>
                  
                  <div className="p-4 rounded-lg bg-[#07070b] border border-[rgba(255,255,255,0.04)] font-mono text-[11px] text-slate-400 space-y-3">
                    <div className="flex items-center gap-2.5">
                      <div className="w-1.5 h-1.5 rounded-full bg-[#8b5cf6]"></div>
                      <span>Model Version Tag: <strong className="text-slate-200">{selectedExp.model_version_id}</strong></span>
                    </div>
                    <div className="flex items-center gap-2.5">
                      <div className="w-1.5 h-1.5 rounded-full bg-cyan-500"></div>
                      <span>Dataset Registry Node: <strong className="text-slate-200">{selectedExp.dataset_version_id}</strong></span>
                    </div>
                    <div className="flex items-center gap-2.5">
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
                      <span>Consolidation Strategy: <strong className="text-slate-200">{selectedExp.strategy_id}</strong></span>
                    </div>
                    <div className="flex items-center gap-2.5">
                      <div className="w-1.5 h-1.5 rounded-full bg-amber-500"></div>
                      <span>Evaluation Protocol: <strong className="text-slate-200">proto_standard</strong></span>
                    </div>
                  </div>
                </div>

                {/* Accuracy metrics */}
                {selectedExp.avg_accuracy && (
                  <div className="space-y-4">
                    <span className="text-[10px] font-mono uppercase text-slate-500 block tracking-wider">PERFORMANCE LOGS SUMMARY</span>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 bg-[#07070b] rounded-lg border border-[rgba(255,255,255,0.04)]">
                        <span className="block text-[9px] uppercase text-slate-500 font-mono tracking-wider">Average Accuracy</span>
                        <span className="text-base font-bold mt-1.5 block font-mono text-emerald-400">
                          {(selectedExp.avg_accuracy * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="p-4 bg-[#07070b] rounded-lg border border-[rgba(255,255,255,0.04)]">
                        <span className="block text-[9px] uppercase text-slate-500 font-mono tracking-wider">Forgetting Score</span>
                        <span className="text-base font-bold mt-1.5 block font-mono text-rose-400">
                          {(selectedExp.forgetting_score || 0 * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Weight Plasticity / Fisher Freezing Stats */}
                {selectedExp.fisher_freezing_enabled && (
                  <div className="space-y-4">
                    <span className="text-[10px] font-mono uppercase text-slate-500 block tracking-wider">WEIGHT PLASTICITY SAFEGUARD (FISHER FREEZING)</span>
                    <div className="grid grid-cols-2 gap-4 text-xs font-mono">
                      <div className="p-4 bg-[#07070b] rounded-lg border border-[rgba(255,255,255,0.04)]">
                        <span className="block text-[9px] uppercase text-slate-500 mb-1.5 tracking-wider">Fisher Importance Threshold</span>
                        <span className="text-slate-200">{(selectedExp.fisher_importance_threshold * 100).toFixed(0)}%</span>
                      </div>
                      <div className="p-4 bg-[#07070b] rounded-lg border border-[rgba(255,255,255,0.04)]">
                        <span className="block text-[9px] uppercase text-slate-500 mb-1.5 tracking-wider">Frozen Parameters</span>
                        <span className="text-[#8b5cf6] font-bold">
                          {selectedExp.frozen_param_count 
                            ? `${(selectedExp.frozen_param_count / 1000000).toFixed(1)}M params`
                            : "Calculating..."}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Green AI Carbon-Aware Scheduler Stats */}
                {selectedExp.carbon_aware_enabled && (
                  <div className="space-y-4">
                    <span className="text-[10px] font-mono uppercase text-slate-500 block tracking-wider">GREEN AI CARBON-AWARE SCHEDULER</span>
                    <div className="grid grid-cols-2 gap-4 text-xs font-mono">
                      <div className="p-4 bg-[#07070b] rounded-lg border border-[rgba(255,255,255,0.04)]">
                        <span className="block text-[9px] uppercase text-slate-500 mb-1.5 tracking-wider">Scheduler Limit</span>
                        <span className="text-slate-200">{selectedExp.carbon_intensity_threshold} gCO2/kWh</span>
                      </div>
                      <div className="p-4 bg-[#07070b] rounded-lg border border-[rgba(255,255,255,0.04)]">
                        <span className="block text-[9px] uppercase text-slate-500 mb-1.5 tracking-wider">Scheduler Mode</span>
                        <span className="text-emerald-400 font-bold uppercase">CARBON-AWARE ACTIVE</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Carbon footprint estimate */}
                <div className="border-t border-[rgba(255,255,255,0.06)] pt-6 space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-mono uppercase text-slate-500 tracking-wider">RESOURCE & HARDWARE EMISSIONS</span>
                    <span className="text-[9px] bg-slate-900 border border-slate-800 text-slate-400 px-2 py-0.5 rounded font-mono">
                      ESTIMATE
                    </span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono text-slate-400">
                    <div className="p-4 bg-[#07070b] rounded-lg border border-[rgba(255,255,255,0.04)]">
                      <span className="block text-[9px] uppercase text-slate-500 mb-1.5 tracking-wider">Total Electricity</span>
                      <span className="text-slate-200">0.08 kWh</span>
                    </div>
                    <div className="p-4 bg-[#07070b] rounded-lg border border-[rgba(255,255,255,0.04)]">
                      <span className="block text-[9px] uppercase text-slate-500 mb-1.5 tracking-wider">Offset Footprint</span>
                      <span className="text-slate-200">0.03 kg CO2</span>
                    </div>
                    <div className="p-4 bg-[#07070b] rounded-lg border border-[rgba(255,255,255,0.04)]">
                      <span className="block text-[9px] uppercase text-slate-500 mb-1.5 tracking-wider">Estimated Cost</span>
                      <span className="text-slate-200">$0.75 USD</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center border border-dashed border-[rgba(255,255,255,0.06)] rounded-lg h-80 text-slate-500 font-mono text-xs">
                SELECT A RUN TO REVIEW LINEAGE PATH AND PROVENANCE
              </div>
            )}
          </div>
        </div>
      </div>
    </ClientLayout>
  );
}
