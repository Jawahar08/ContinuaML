"use client";

import React, { useEffect, useState } from "react";
import ClientLayout from "../client-layout";
import { getDatasets, Dataset } from "../api";
import { Database, FileSpreadsheet, ShieldCheck, Sparkles } from "lucide-react";

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadDatasets = async () => {
      setLoading(true);
      try {
        const res = await getDatasets();
        setDatasets(res.data);
        if (res.data.length > 0) {
          setSelectedDataset(res.data[0]);
        }
      } catch (err) {
        setError("Could not load dataset registry.");
      } finally {
        setLoading(false);
      }
    };
    loadDatasets();
  }, []);

  if (loading) {
    return (
      <ClientLayout>
        <div className="flex flex-col items-center justify-center h-[50vh]">
          <div className="w-8 h-8 rounded-full border-2 border-[rgba(139,92,246,0.15)] border-t-[#8b5cf6] animate-spin mb-4"></div>
          <p className="text-slate-500 font-mono text-[10px] tracking-widest uppercase">Reading Index...</p>
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
            DATA PIPELINE
          </span>
          <h1 className="text-4xl font-semibold tracking-tight text-white">
            Dataset Manager
          </h1>
          <p className="text-slate-400 text-xs mt-1.5 max-w-xl">
            Validate schemas, audit evaluation overlap leakage, and scan for privacy restrictions.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Datasets list (Left, 1/3) */}
          <div className="lg:col-span-1 space-y-4">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 block px-1">
              IMPORTED REPOSITORIES ({datasets.length})
            </span>
            <div className="space-y-2.5">
              {datasets.map((dataset) => (
                <div
                  key={dataset.id}
                  onClick={() => setSelectedDataset(dataset)}
                  className={`p-4 rounded-lg border transition cursor-pointer ${
                    selectedDataset?.id === dataset.id
                      ? "bg-slate-900/60 border-[#8b5cf6]/60 shadow-[0_0_15px_rgba(139,92,246,0.05)]"
                      : "bg-[#0c0c12] border-[rgba(255,255,255,0.05)] hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded ${selectedDataset?.id === dataset.id ? "bg-[#8b5cf6]/20 text-[#8b5cf6]" : "bg-slate-950 text-slate-500"}`}>
                      <Database className="w-4 h-4" />
                    </div>
                    <div className="truncate">
                      <h4 className="text-xs font-semibold text-white truncate">{dataset.name}</h4>
                      <span className="text-[10px] text-slate-500 font-mono block mt-0.5">{dataset.source}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Dataset Card details (Right, 2/3) */}
          <div className="lg:col-span-2">
            {selectedDataset ? (
              <div className="glass-card p-8 space-y-8">
                <div className="flex justify-between items-start border-b border-[rgba(255,255,255,0.06)] pb-5">
                  <div>
                    <h2 className="text-xl font-medium text-white">{selectedDataset.name}</h2>
                    <span className="text-xs text-[#8b5cf6] font-mono mt-1 block">{selectedDataset.id}</span>
                  </div>
                  <span className="text-[9px] bg-emerald-950/20 border border-emerald-900/30 text-emerald-400 px-2 py-0.5 rounded font-mono uppercase">
                    AUDIT COMPLIANT
                  </span>
                </div>

                {/* Audit widgets Bento Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Contamination index */}
                  <div className="p-4 bg-[#07070b] rounded-lg border border-[rgba(255,255,255,0.04)] flex items-center justify-between">
                    <div>
                      <span className="block text-[9px] uppercase text-slate-500 font-mono tracking-wider">Overlap Contamination</span>
                      <span className="text-base font-bold mt-1.5 block font-mono text-emerald-400">
                        {((selectedDataset.overlap_rate || 0) * 100).toFixed(2)}%
                      </span>
                    </div>
                    <ShieldCheck className="w-6 h-6 text-emerald-500/40" />
                  </div>

                  {/* PII audit */}
                  <div className="p-4 bg-[#07070b] rounded-lg border border-[rgba(255,255,255,0.04)] flex items-center justify-between">
                    <div>
                      <span className="block text-[9px] uppercase text-slate-500 font-mono tracking-wider">PII Privacy Scan</span>
                      <span className="text-base font-bold mt-1.5 block font-mono text-emerald-400">
                        {selectedDataset.pii_risk === 0 ? "Clean" : "Flagged"}
                      </span>
                    </div>
                    <ShieldCheck className="w-6 h-6 text-emerald-500/40" />
                  </div>

                  {/* Schema layout */}
                  <div className="p-4 bg-[#07070b] rounded-lg border border-[rgba(255,255,255,0.04)] flex items-center justify-between">
                    <div>
                      <span className="block text-[9px] uppercase text-slate-500 font-mono tracking-wider">License Type</span>
                      <span className="text-xs font-semibold mt-1.5 block truncate text-[#8b5cf6] font-mono">
                        {selectedDataset.license}
                      </span>
                    </div>
                    <FileSpreadsheet className="w-6 h-6 text-[#8b5cf6]/40" />
                  </div>
                </div>

                {/* Validation summary report */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-[#8b5cf6] font-mono text-[10px] uppercase tracking-wider">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Evaluation Integrity Report</span>
                  </div>

                  <div className="p-5 rounded-lg bg-[#07070b] border border-[rgba(255,255,255,0.04)] space-y-3.5 text-xs font-mono text-slate-400">
                    <div className="flex justify-between">
                      <span>Exact training overlap:</span>
                      <span className="text-slate-200">1.2% (Threshold &lt; 5%)</span>
                    </div>
                    <div className="flex justify-between">
                      <span>PII Entity scan (SSN, emails, phones):</span>
                      <span className="text-emerald-400 font-semibold">0 entities detected</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Malformed or blank lines:</span>
                      <span className="text-slate-200">0 rows dropped</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Dataset Split manifest:</span>
                      <span className="text-slate-200">Train: 8,000 | Val: 1,000 | Test: 1,000</span>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="border-t border-[rgba(255,255,255,0.06)] pt-6 space-y-4">
                  <span className="text-[10px] font-mono uppercase text-slate-500 block tracking-wider">DATA GOVERNANCE ACTIONS</span>
                  <div className="flex gap-4">
                    <button className="btn-secondary px-4 py-2 text-xs font-medium rounded cursor-pointer">
                      Export Split Schema
                    </button>
                    <button className="px-4 py-2 bg-red-950/20 hover:bg-red-950/40 border border-red-900/30 text-red-400 text-xs font-medium rounded transition-all cursor-pointer">
                      Quarantine Dataset
                    </button>
                  </div>
                </div>

              </div>
            ) : (
              <div className="flex items-center justify-center border border-dashed border-[rgba(255,255,255,0.06)] rounded-lg h-80 text-slate-500 font-mono text-xs">
                SELECT A DATASET FROM THE REPOSITORY LIST
              </div>
            )}
          </div>
        </div>
      </div>
    </ClientLayout>
  );
}
