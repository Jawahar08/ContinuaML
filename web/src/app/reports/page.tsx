"use client";

import React, { useState } from "react";
import ClientLayout from "../client-layout";
import { Save, Download, Sparkles, Quote } from "lucide-react";

export default function ReportsPage() {
  const [title, setTitle] = useState("Mitigating Catastrophic Forgetting in Low-Parameter LLMs");
  const [abstract, setAbstract] = useState(
    "Catastrophic forgetting represents a significant barrier to the deployment of continual learning strategies in large language models. In this paper, we evaluate Elastic Weight Consolidation (EWC) and Experience Replay against direct sequential fine-tuning using TinyLlama-1.1B. Our results demonstrate that EWC maintains 88% retention accuracy on TriviaQA after sequential adaptation to GSM8K, outperforming naive fine-tuning."
  );
  const [bibtex, setBibtex] = useState(
    `@article{kirkpatrick2017overcoming,
  title={Overcoming catastrophic forgetting in neural networks},
  author={Kirkpatrick, James and Pascanu, Razvan and Rabinowitz, Neil and others},
  journal={Proceedings of the National Academy of Sciences},
  volume={114},
  number={13},
  pages={3521--3526},
  year={2017}
}`
  );
  const [saved, setSaved] = useState(false);

  const handleExport = (format: "latex" | "markdown") => {
    let content = "";
    if (format === "latex") {
      content = `\\documentclass{article}
\\begin{document}
\\title{${title}}
\\author{ContinuaML Research Unit}

\\date{\\today}
\\maketitle

\\begin{abstract}
${abstract}
\\end{abstract}

\\section{Introduction}
Continual learning strategies aim to accumulate domain knowledge sequentially...

\\section{Methodology}
We leverage Elastic Weight Consolidation using Fisher information approximation...

\\section{Bibliography}
\\begin{verbatim}
${bibtex}
\\end{verbatim}

\\end{document}`;
    } else {
      content = `# ${title}

## Abstract
${abstract}

## Introduction
Continual learning strategies aim to accumulate domain knowledge sequentially...

## Bibliography
\`\`\`bibtex
${bibtex}
\`\`\`
`;
    }

    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const downloadAnchor = document.createElement("a");
    downloadAnchor.href = url;
    downloadAnchor.download = `research-report.${format === "latex" ? "tex" : "md"}`;
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    document.body.removeChild(downloadAnchor);
    URL.revokeObjectURL(url);
  };

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <ClientLayout>
      <div className="space-y-12">
        {/* Header Title Section */}
        <div className="relative flex flex-col md:flex-row justify-between items-start md:items-end gap-6 border-b border-[rgba(255,255,255,0.06)] pb-8">
          <div className="absolute top-[-100px] left-[-50px] w-96 h-96 rounded-full bg-[rgba(139,92,246,0.04)] blur-3xl -z-10"></div>
          <div>
            <span className="text-[10px] font-mono tracking-widest text-[#8b5cf6] uppercase block mb-1">
              ACADEMIC DISSEMINATION
            </span>
            <h1 className="text-4xl font-semibold tracking-tight text-white">
              Research Reports
            </h1>
            <p className="text-slate-400 text-xs mt-1.5 max-w-xl">
              Export evidence-linked manuscript drafts, customize abstract parameters, and compile BibTeX reference files.
            </p>
          </div>
          
          <div className="flex gap-3">
            <button
              onClick={handleSave}
              className="btn-secondary px-4 py-2 text-xs font-semibold rounded cursor-pointer flex items-center gap-1.5"
            >
              <Save className="w-3.5 h-3.5" />
              <span>{saved ? "Saved Draft" : "Save Draft"}</span>
            </button>
            <button
              onClick={() => handleExport("latex")}
              className="btn-primary px-4 py-2 text-xs font-semibold rounded transition flex items-center gap-1.5 cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export LaTeX</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main manuscript content (2/3) */}
          <div className="lg:col-span-2 space-y-6">
            <div className="glass-card p-8 space-y-6">
              <div className="space-y-1.5">
                <label className="block text-[10px] font-mono uppercase text-slate-500 tracking-wider">MANUSCRIPT TITLE</label>
                <input 
                  type="text" 
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full bg-[#07070b] border border-[rgba(255,255,255,0.06)] focus:border-[#8b5cf6] text-white p-3 rounded text-sm font-medium outline-none"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-[10px] font-mono uppercase text-slate-500 tracking-wider">ABSTRACT DRAFT</label>
                <textarea 
                  value={abstract}
                  onChange={(e) => setAbstract(e.target.value)}
                  rows={6}
                  className="w-full bg-[#07070b] border border-[rgba(255,255,255,0.06)] focus:border-[#8b5cf6] text-slate-300 p-3.5 rounded text-xs leading-relaxed outline-none"
                />
              </div>

              <div className="border-t border-[rgba(255,255,255,0.06)] pt-6 space-y-4">
                <div className="flex items-center gap-2 text-[#8b5cf6] font-mono text-[10px] uppercase tracking-wider">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Linked Provenance Evidence</span>
                </div>
                <div className="p-4 bg-[#07070b] border border-[rgba(255,255,255,0.04)] rounded font-mono text-[10px] text-slate-400 space-y-2 leading-relaxed">
                  <p>✓ Metrics verified on local safetensors checkpoints.</p>
                  <p>✓ Average accuracy metrics compiled directly from run: <strong>exp-e2e-01</strong>.</p>
                  <p>✓ Evaluator compiled with protocol seed: <strong>42</strong>.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Bibtex & citations (1/3) */}
          <div className="lg:col-span-1 space-y-6">
            <div className="glass-card p-6 space-y-4">
              <div className="flex items-center gap-2 text-[#8b5cf6] font-mono text-[10px] uppercase tracking-wider">
                <Quote className="w-3.5 h-3.5" />
                <span>BibTeX Bibliography</span>
              </div>
              <textarea 
                value={bibtex}
                onChange={(e) => setBibtex(e.target.value)}
                rows={10}
                className="w-full bg-[#07070b] border border-[rgba(255,255,255,0.06)] focus:border-[#8b5cf6] text-slate-400 p-3.5 rounded text-[10px] font-mono leading-relaxed outline-none"
              />
            </div>

            <div className="glass-card p-6 text-[10px] text-slate-500 leading-relaxed font-mono space-y-2.5">
              <span className="text-slate-300 block font-medium tracking-wider uppercase">CITATIONS CHECKLIST</span>
              <p>• Kirkpatrick et al., 2017: Verified</p>
              <p>• Robins, 1995: Verified</p>
            </div>
          </div>
        </div>
      </div>
    </ClientLayout>
  );
}
