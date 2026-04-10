"use client";

import { motion } from "framer-motion";
import { useEffect, useState, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { UploadCloud, PlayCircle, Lock, AlertCircle, RefreshCw } from "lucide-react";
import { generateDemoData } from "@/lib/demo-data";

const STAGES = [
  "Ingesting & Validating Data",
  "Profiling Schema & Structure",
  "Cleaning & Transforming",
  "Running Anomaly Detection (Isolation Forest)",
  "Attributing Root Causes (9 Dimensions)",
  "Generating 14-Day Forecast",
  "Building Strategic Recommendations",
  "Synthesizing Executive Intelligence",
  "Preparing AI Assistant Context",
];

export default function UploadClient() {
  const router = useRouter();
  const params = useSearchParams();
  const [status, setStatus] = useState<"idle" | "processing" | "error">("idle");
  const [stage, setStage] = useState(-1);
  const [progress, setProgress] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string>("");
  const fileRef = useRef<HTMLInputElement>(null);
  const hasAutoRun = useRef(false);

  useEffect(() => {
    if (params.get("demo") === "true" && !hasAutoRun.current) {
      hasAutoRun.current = true;
      runDemo();
    }
  }, [params]); // eslint-disable-line

  async function animate(data: any) {
    setStatus("processing");
    for (let i = 0; i < STAGES.length; i++) {
      setStage(i);
      setProgress(Math.round(((i + 1) / STAGES.length) * 100));
      await new Promise((r) => setTimeout(r, 380 + Math.random() * 280));
    }
    await new Promise((r) => setTimeout(r, 400));
    sessionStorage.setItem("cosmos_data", JSON.stringify(data));
    router.push("/dashboard");
  }

  async function handleFile(file: File) {
    // Validate file size (50 MB limit)
    const MAX_SIZE = 50 * 1024 * 1024;
    if (file.size > MAX_SIZE) {
      setErrorMsg("File is too large. Maximum size is 50 MB. Please reduce the file size and try again.");
      setStatus("error");
      return;
    }

    // Validate file type
    const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
    const allowed = ["csv", "xlsx", "xls"];
    if (!allowed.includes(ext)) {
      setErrorMsg(`Unsupported file format ".${ext}". Please upload a CSV (.csv) or Excel (.xlsx / .xls) file.`);
      setStatus("error");
      return;
    }

    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch("/api/upload", { method: "POST", body: fd });
      if (!res.ok) {
        let detail = `Server error (${res.status})`;
        try {
          const errJson = await res.json();
          if (errJson?.detail) detail = errJson.detail;
        } catch { /* ignore json parse error */ }
        throw new Error(detail);
      }
      const data = await res.json();
      await animate(data);
    } catch (err: any) {
      console.error("Upload failed:", err);
      const raw: string = err?.message ?? String(err);
      let friendly: string;
      if (raw.toLowerCase().includes("fetch") || raw.toLowerCase().includes("networkerror") || raw.toLowerCase().includes("failed to fetch")) {
        friendly = "Cannot reach the analysis server. Make sure the backend is running on port 8000 and try again.";
      } else if (raw.toLowerCase().includes("date")) {
        friendly = "Your file has no recognisable date column. Please ensure a column named 'date' (or similar) exists with valid dates.";
      } else if (raw.toLowerCase().includes("empty") || raw.toLowerCase().includes("no rows")) {
        friendly = "The uploaded file appears to be empty or has no usable rows after validation. Please check your data.";
      } else if (raw.toLowerCase().includes("pipeline")) {
        friendly = `Analysis pipeline error: ${raw}`;
      } else {
        friendly = raw || "An unexpected error occurred. Please check your file and try again.";
      }
      setErrorMsg(friendly);
      setStatus("error");
    }
  }

  async function runDemo() {
    await animate(generateDemoData());
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  function resetToIdle() {
    setStatus("idle");
    setErrorMsg("");
    setStage(-1);
    setProgress(0);
    if (fileRef.current) fileRef.current.value = "";
  }

  return (
    <div className="min-h-screen bg-[#020208] text-white flex flex-col items-center justify-center p-6 relative overflow-hidden font-sans">
      <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-violet-700/12 blur-[140px] rounded-full pointer-events-none" />
      <div className="absolute bottom-[-15%] right-[-8%] w-[50%] h-[50%] bg-cyan-500/8 blur-[120px] rounded-full pointer-events-none" />
      <div className="fixed inset-0 pointer-events-none opacity-15"
        style={{ backgroundImage: "radial-gradient(circle, rgba(167,139,250,0.4) 1px, transparent 1px)", backgroundSize: "48px 48px" }} />

      <div className="max-w-2xl w-full mx-auto z-10 text-center">
        {status === "error" ? (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }} className="text-center">
            <div className="inline-flex items-center gap-2.5 mb-8">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-600 to-cyan-400 flex items-center justify-center text-sm shadow-[0_0_20px_rgba(124,58,237,0.4)]">✦</div>
              <span className="font-bold text-gray-300 tracking-tight">COSMOS INTELLIGENCE</span>
            </div>
            <div className="p-8 rounded-3xl border border-rose-500/30 bg-rose-500/5 mb-6 text-left">
              <div className="flex items-start gap-4">
                <AlertCircle size={24} className="text-rose-400 shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-rose-400 font-bold text-lg mb-2">Upload Failed</h3>
                  <p className="text-gray-300 text-sm leading-relaxed">{errorMsg}</p>
                </div>
              </div>
            </div>
            <button
              onClick={resetToIdle}
              className="w-full py-4 rounded-2xl border-2 border-violet-500/40 hover:border-violet-400/70 bg-violet-500/8 hover:bg-violet-500/15 text-violet-300 hover:text-violet-200 font-bold transition-all duration-200 flex items-center justify-center gap-2 mb-4"
            >
              <RefreshCw size={18} /> Try Again
            </button>
            <button onClick={runDemo}
              className="w-full py-4 rounded-2xl border-2 border-white/10 hover:border-cyan-400/40 hover:bg-cyan-400/5 text-gray-400 hover:text-cyan-400 font-bold transition-all duration-200 flex items-center justify-center gap-2">
              <PlayCircle size={18} /> Run Demo Analysis Instead
            </button>
          </motion.div>
        ) : status === "idle" ? (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <div className="inline-flex items-center gap-2.5 mb-8">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-600 to-cyan-400 flex items-center justify-center text-sm shadow-[0_0_20px_rgba(124,58,237,0.4)]">✦</div>
              <span className="font-bold text-gray-300 tracking-tight">COSMOS INTELLIGENCE</span>
            </div>
            <div className="inline-block px-4 py-1.5 rounded-full border border-cyan-500/25 bg-cyan-500/8 text-cyan-400 text-[11px] font-bold tracking-widest uppercase mb-5">GET STARTED</div>
            <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-4 leading-tight">
              <span className="bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">Ready to See Your Data</span>
              <br /><span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">Come Alive?</span>
            </h1>
            <p className="text-gray-400 mb-10 text-sm">Drop any business CSV — revenue, orders, campaigns — and get full AI decision intelligence in seconds.</p>

            <div
              onClick={() => fileRef.current?.click()}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDrop}
              className={`relative p-16 rounded-3xl border-2 border-dashed cursor-pointer transition-all duration-300 mb-6 group ${
                dragOver ? "border-cyan-400 bg-cyan-400/5 shadow-[0_0_50px_rgba(0,229,255,0.15)]" : "border-white/15 hover:border-violet-500/50 hover:bg-violet-500/4 bg-white/2"
              }`}
            >
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-violet-500/4 to-cyan-500/3 group-hover:from-violet-500/8 group-hover:to-cyan-500/5 transition-all" />
              <input ref={fileRef} type="file" accept=".csv,.xlsx,.xls" className="hidden"
                onChange={(e) => { if (e.target.files?.[0]) handleFile(e.target.files[0]); }} />
              <UploadCloud size={48} className={`mx-auto mb-5 transition-colors ${dragOver ? "text-cyan-400" : "text-violet-400 group-hover:text-violet-300"}`} />
              <h3 className="text-xl font-bold mb-2">{dragOver ? "Release to upload" : "Drop your CSV file here"}</h3>
              <p className="text-gray-400 text-sm mb-3">or click to browse files</p>
              <p className="text-gray-600 text-xs font-mono">Supports CSV, Excel (.xlsx, .xls) · Max 50 MB · Columns: date, revenue, orders, region, category, channel, campaign</p>
            </div>

            <div className="flex items-center gap-4 text-gray-600 text-sm font-medium mb-6">
              <div className="h-px bg-white/8 flex-1" />OR<div className="h-px bg-white/8 flex-1" />
            </div>

            <button onClick={runDemo}
              className="w-full py-4 rounded-2xl border-2 border-white/10 hover:border-cyan-400/40 hover:bg-cyan-400/5 text-gray-300 hover:text-cyan-400 font-bold transition-all duration-200 flex items-center justify-center gap-2">
              <PlayCircle size={18} /> Run Demo Analysis (No Upload Required)
            </button>
            <p className="text-xs text-gray-600 mt-5 flex items-center justify-center gap-1.5">
              <Lock size={11} /> Demo runs entirely in your browser. Upload mode: data deleted on session end.
            </p>
          </motion.div>
        ) : (
          <motion.div initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} className="text-left">
            <h2 className="text-4xl font-black mb-2 bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">✦ COSMOS</h2>
            <p className="text-gray-400 text-sm mb-10">Analyzing your data with 7 AI engines...</p>
            <div className="flex flex-col gap-3.5 mb-10">
              {STAGES.map((s, i) => (
                <div key={i} className={`flex items-center gap-4 text-sm transition-all duration-300 ${stage >= i ? "text-white" : "text-gray-700"}`}>
                  <div className="shrink-0 w-5 h-5 flex items-center justify-center">
                    {stage > i ? <span className="text-emerald-400 font-black">✓</span>
                     : stage === i ? <div className="w-4 h-4 border-2 border-violet-500/40 border-t-cyan-400 rounded-full animate-spin" />
                     : <div className="w-3 h-3 border border-gray-700 rounded-full" />}
                  </div>
                  <span className={stage === i ? "text-white font-semibold" : ""}>{s}</span>
                </div>
              ))}
            </div>
            <div className="mb-3 flex justify-between text-xs text-gray-500">
              <span>Running pipeline...</span><span>{progress}%</span>
            </div>
            <div className="h-1.5 bg-white/8 rounded-full overflow-hidden mb-5">
              <div className="h-1.5 bg-gradient-to-r from-violet-600 to-cyan-400 rounded-full transition-all duration-500" style={{ width: `${progress}%` }} />
            </div>
            <p className="text-[11px] text-gray-600 font-mono tracking-wide text-center">
              Powered by Isolation Forest · Prophet · Claude AI · Weighted Attribution
            </p>
          </motion.div>
        )}
      </div>
    </div>
  );
}
