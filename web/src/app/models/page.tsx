"use client";

import React, { useEffect, useState } from "react";
import ClientLayout from "../client-layout";
import { getModels, Model } from "../api";
import { Brain, FileText, ShieldCheck } from "lucide-react";

export default function ModelsPage() {
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadModels = async () => {
      setLoading(true);
      try {
        const res = await getModels();
        setModels(res.data);
        if (res.data.length > 0) {
          setSelectedModel(res.data[0]);
        }
      } catch (err) {
        setError("Could not load model registry.");
      } finally {
        setLoading(false);
      }
    };
    loadModels();
  }, []);

  if (loading) {
    return (
      <ClientLayout>
        <div className="flex flex-col items-center justify-center h-[50vh]">
          <div className="w-8 h-8 rounded-full border-2 border-[rgba(139,92,246,0.15)] border-t-[#8b5cf6] animate-spin mb-4"></div>
          <p className="text-slate-500 font-mono text-[10px] tracking-widest uppercase">Querying Registry...</p>
        </div>
      </ClientLayout>
    );
  }

  return (
    <ClientLayout>
      <div className="space-y-12">
        {/* Header Title Section */}
        <div className="relative border-b border-[rgba(255,255,255,0.06)] pb-8">
          <div className="absolute top-[-100px] left-[-50px] w-96 h-96 rounded-full bg-[rgba(139,92,246,0.04)] blur-3xl -z-10"></div>
          <span className="text-[10px] font-mono tracking-widest text-[#8b5cf6] uppercase block mb-1">
            INTELLIGENCE ASSETS
          </span>
          <h1 className="text-4xl font-semibold tracking-tight text-white">
            Model Registry
          </h1>
          <p className="text-slate-400 text-xs mt-1.5 max-w-xl">
            Governance, specifications, licensing, and metadata cards for registered causal language models.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Models list (Left, 1/3) */}
          <div className="lg:col-span-1 space-y-4">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 block px-1">
              REGISTERED CORE ({models.length})
            </span>
            <div className="space-y-2.5">
              {models.map((model) => (
                <div
                  key={model.id}
                  onClick={() => setSelectedModel(model)}
                  className={`p-4 rounded-lg border transition cursor-pointer ${
                    selectedModel?.id === model.id
                      ? "bg-slate-900/60 border-[#8b5cf6]/60 shadow-[0_0_15px_rgba(139,92,246,0.05)]"
                      : "bg-[#0c0c12] border-[rgba(255,255,255,0.05)] hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded ${selectedModel?.id === model.id ? "bg-[#8b5cf6]/20 text-[#8b5cf6]" : "bg-slate-950 text-slate-500"}`}>
                      <Brain className="w-4 h-4" />
                    </div>
                    <div className="truncate">
                      <h4 className="text-xs font-semibold text-white truncate">{model.name}</h4>
                      <span className="text-[10px] text-slate-500 font-mono block mt-0.5">{model.architecture}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Model Card Detail Panel (Right, 2/3) */}
          <div className="lg:col-span-2">
            {selectedModel ? (
              <div className="glass-card p-8 space-y-8">
                <div className="flex justify-between items-start border-b border-[rgba(255,255,255,0.06)] pb-5">
                  <div>
                    <h2 className="text-xl font-medium text-white">{selectedModel.name}</h2>
                    <span className="text-xs text-[#8b5cf6] font-mono mt-1 block">{selectedModel.id}</span>
                  </div>
                  <span className="text-[9px] bg-emerald-950/20 border border-emerald-900/30 text-emerald-400 px-2 py-0.5 rounded font-mono uppercase">
                    ACTIVE VERIFIED
                  </span>
                </div>

                {/* Specs Bento Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {[
                    { label: "Parameters", val: `${(selectedModel.param_count / 1000000000).toFixed(1)}B` },
                    { label: "Context Window", val: `${selectedModel.context_length} tokens` },
                    { label: "License Terms", val: selectedModel.license },
                    { label: "Registry Hub", val: selectedModel.source }
                  ].map((spec, idx) => (
                    <div key={idx} className="p-4 bg-[#07070b] rounded-lg border border-[rgba(255,255,255,0.04)]">
                      <span className="block text-[9px] uppercase text-slate-500 font-mono tracking-wider">{spec.label}</span>
                      <span className="text-xs font-semibold mt-1.5 block font-mono text-slate-200">{spec.val}</span>
                    </div>
                  ))}
                </div>

                {/* Details Section */}
                <div className="space-y-6">
                  <div className="flex items-center gap-2 text-[#8b5cf6] font-mono text-[10px] uppercase tracking-wider">
                    <FileText className="w-3.5 h-3.5" />
                    <span>Hugging Face Model Card Specification</span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs leading-relaxed text-slate-400">
                    <div className="space-y-1">
                      <h4 className="font-medium text-slate-200">Intended Uses</h4>
                      <p className="text-[11px] text-slate-400">
                        Designed for zero-shot tasks, continual fine-tuning alignments, and catastrophic forgetting evaluation frameworks.
                      </p>
                    </div>

                    <div className="space-y-1">
                      <h4 className="font-medium text-slate-200">Known Limitations</h4>
                      <p className="text-[11px] text-slate-400">
                        Highly susceptible to forgetting patterns during subsequent task tuning sequence steps. Requires strategic mitigation modules.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Compliance Preflights */}
                <div className="border-t border-[rgba(255,255,255,0.06)] pt-6 space-y-4">
                  <span className="text-[10px] font-mono uppercase text-slate-500 block tracking-wider">PREFLIGHT GOVERNANCE CHECKS</span>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px] text-slate-400 font-mono">
                    {[
                      "Tokenizer Signature Checked",
                      "Safetensors Format Validation Pass",
                      "Subprocess Sandboxed Loader",
                      "Permissible Non-Contaminated Licensing"
                    ].map((check, idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        <ShieldCheck className="w-4 h-4 text-emerald-500" />
                        <span>{check}</span>
                      </div>
                    ))}
                  </div>
                </div>

              </div>
            ) : (
              <div className="flex items-center justify-center border border-dashed border-[rgba(255,255,255,0.06)] rounded-lg h-80 text-slate-500 font-mono text-xs">
                SELECT A MODEL FROM THE REGISTRY CARD LIST
              </div>
            )}
          </div>
        </div>
      </div>
    </ClientLayout>
  );
}
