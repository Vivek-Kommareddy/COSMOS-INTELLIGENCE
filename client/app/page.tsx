"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import {
  ArrowRight, Zap, Cpu, Trash2, Lock, Shield, FileClock,
  BarChart3, Activity, Target, TrendingUp, PieChart,
  Lightbulb, MessageSquare, FileText, ChevronRight,
} from "lucide-react";

const fadeUp = { hidden: { opacity: 0, y: 28 }, show: { opacity: 1, y: 0 } };

export default function Home() {
  return (
    <div className="min-h-screen bg-[#020208] text-gray-100 font-sans selection:bg-violet-700/30 selection:text-white overflow-x-hidden">

      {/* ── Ambient background glows ─────────────────────────────────────────── */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-5%] w-[55%] h-[55%] bg-violet-700/12 blur-[130px] rounded-full" />
        <div className="absolute top-[20%] right-[-10%] w-[45%] h-[50%] bg-cyan-500/8 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-5%] left-[20%] w-[50%] h-[40%] bg-purple-600/10 blur-[140px] rounded-full" />
      </div>

      {/* ── Star grid overlay ──────────────────────────────────────────────────── */}
      <div className="fixed inset-0 pointer-events-none z-0 opacity-20"
        style={{ backgroundImage: "radial-gradient(circle, rgba(167,139,250,0.4) 1px, transparent 1px)", backgroundSize: "48px 48px" }} />

      {/* ── NAVBAR ────────────────────────────────────────────────────────────── */}
      <nav className="fixed w-full flex justify-between items-center px-8 md:px-16 py-4 z-50 border-b border-white/5 bg-[#020208]/80 backdrop-blur-2xl">
        <div className="flex items-center gap-3 font-bold tracking-tight">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-600 to-cyan-400 flex items-center justify-center text-sm shadow-[0_0_20px_rgba(124,58,237,0.5)]">✦</div>
          <div className="flex flex-col">
            <span className="text-lg bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent leading-none">COSMOS INTELLIGENCE</span>
            <span className="text-[9px] text-violet-400/80 font-bold tracking-[0.2em] mt-1">ARCHITECTED BY VIVEK KOMMAREDDY</span>
          </div>
        </div>
        <div className="hidden md:flex gap-8 text-sm font-medium text-gray-400">
          <a href="#features" className="hover:text-cyan-400 transition-colors duration-200">Features</a>
          <a href="#pipeline" className="hover:text-cyan-400 transition-colors duration-200">Platform</a>
          <a href="#privacy" className="hover:text-cyan-400 transition-colors duration-200">Privacy</a>
        </div>
        <Link href="/upload"
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-violet-500 text-white font-semibold text-sm shadow-[0_4px_20px_rgba(124,58,237,0.4)] hover:shadow-[0_8px_32px_rgba(124,58,237,0.5)] hover:-translate-y-0.5 transition-all duration-200">
          Start Analyzing →
        </Link>
      </nav>

      <main className="relative z-10">

        {/* ── HERO ──────────────────────────────────────────────────────────────── */}
        <section className="min-h-screen flex items-center justify-center px-6 md:px-16 pt-24 pb-16">
          <div className="max-w-7xl w-full mx-auto grid md:grid-cols-2 gap-16 items-center">
            <motion.div variants={fadeUp} initial="hidden" animate="show" transition={{ duration: 0.7 }}>
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-violet-500/30 bg-violet-500/8 text-violet-300 text-[11px] font-bold tracking-[0.12em] uppercase mb-8">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse shadow-[0_0_6px_#00E5FF]" />
                Autonomous Business Intelligence
              </div>
              <h1 className="text-5xl md:text-[68px] font-black tracking-tight leading-[1.06] mb-7">
                <span className="bg-gradient-to-br from-white via-gray-100 to-gray-300 bg-clip-text text-transparent">Your Data</span>
                <br /><span className="bg-gradient-to-r from-violet-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">Knows Why.</span>
                <br /><span className="bg-gradient-to-br from-white via-gray-100 to-gray-300 bg-clip-text text-transparent">We Make It</span>
                <br /><span className="bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">Tell You.</span>
              </h1>
              <p className="text-gray-400 text-lg md:text-xl max-w-lg mb-10 leading-relaxed">
                Upload any business dataset. Cosmos Intelligence instantly detects anomalies, attributes root causes, forecasts the future, and generates C-suite ready decisions — in seconds.
              </p>
              <div className="flex flex-wrap gap-4 mb-10">
                <Link href="/upload"
                  className="group px-8 py-4 rounded-2xl bg-gradient-to-r from-violet-600 to-violet-500 text-white font-bold shadow-[0_4px_24px_rgba(124,58,237,0.4)] hover:-translate-y-1 hover:shadow-[0_10px_36px_rgba(124,58,237,0.5)] transition-all duration-300 flex items-center gap-2">
                  Upload Your Data <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
                </Link>
                <Link href="/upload?demo=true"
                  className="px-8 py-4 rounded-2xl border-2 border-white/10 hover:border-cyan-400/50 hover:bg-cyan-400/5 text-gray-300 hover:text-cyan-400 font-bold transition-all duration-300">
                  ▷ Live Demo
                </Link>
              </div>
              <div className="flex flex-wrap gap-6 text-xs text-gray-500 font-medium">
                <span className="flex items-center gap-1.5"><Lock size={13} className="text-cyan-500" /> Zero data retention</span>
                <span className="flex items-center gap-1.5"><Zap size={13} className="text-violet-400" /> &lt; 3s analysis</span>
                <span className="flex items-center gap-1.5"><Cpu size={13} className="text-purple-400" /> 7 AI engines</span>
                <span className="flex items-center gap-1.5"><Trash2 size={13} className="text-rose-400" /> One-click deletion</span>
              </div>
            </motion.div>

            {/* Hero visual — animated data card */}
            <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.8, delay: 0.3 }}
              className="hidden md:block">
              <div className="relative p-8 rounded-3xl border border-white/8 bg-gradient-to-br from-white/4 to-white/1 backdrop-blur-xl shadow-[0_0_80px_rgba(124,58,237,0.12)]">
                <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-violet-500/5 to-cyan-500/5" />
                {/* Fake terminal header */}
                <div className="flex items-center gap-2 mb-6">
                  <div className="w-3 h-3 rounded-full bg-rose-500/70" />
                  <div className="w-3 h-3 rounded-full bg-amber-500/70" />
                  <div className="w-3 h-3 rounded-full bg-emerald-500/70" />
                  <span className="ml-3 text-xs text-gray-500 font-mono">cosmos_intelligence.ai</span>
                </div>
                {/* Analysis result mock */}
                <div className="space-y-4 text-sm">
                  <div className="p-4 rounded-2xl bg-rose-500/8 border border-rose-500/20">
                    <div className="text-rose-400 text-xs font-bold uppercase tracking-wider mb-2">⚠ CRITICAL ANOMALY DETECTED</div>
                    <div className="text-white font-semibold">Revenue declined 18.3% in last 14 days</div>
                    <div className="text-gray-400 text-xs mt-1">Isolation Forest · 87% confidence</div>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    {[{ l: "Revenue", v: "$284K", c: "text-rose-400", chg: "-18.3%" }, { l: "Orders", v: "1,847", c: "text-amber-400", chg: "-12.1%" }, { l: "AOV", c: "text-cyan-400", v: "$153.8", chg: "-7.2%" }].map((k) => (
                      <div key={k.l} className="p-3 rounded-xl bg-white/4 border border-white/8">
                        <div className="text-[10px] text-gray-500 font-semibold mb-1">{k.l}</div>
                        <div className={`text-lg font-black ${k.c}`}>{k.v}</div>
                        <div className="text-[10px] text-rose-400">{k.chg}</div>
                      </div>
                    ))}
                  </div>
                  <div className="p-4 rounded-2xl bg-violet-500/8 border border-violet-500/20">
                    <div className="text-violet-400 text-xs font-bold uppercase tracking-wider mb-2">✦ AI ROOT CAUSE</div>
                    <div className="text-gray-300 text-xs leading-relaxed">Campaign_A pause accounts for 62.1% of the revenue shortfall. West-region electronics stockout contributed an additional 21.3%. Combined intervention recovers 35–50% within 10 days.</div>
                  </div>
                  <div className="flex gap-2">
                    {["HIGH", "HIGH", "MEDIUM"].map((p, i) => (
                      <div key={i} className={`flex-1 p-2 rounded-xl text-center text-[10px] font-black ${p === "HIGH" ? "bg-rose-500/10 text-rose-400 border border-rose-500/20" : "bg-amber-500/10 text-amber-400 border border-amber-500/20"}`}>{p}</div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* ── STATS ─────────────────────────────────────────────────────────────── */}
        <section className="py-20 px-6 md:px-16">
          <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-5">
            {[{ v: "<3s", l: "Analysis Time", c: "from-cyan-400 to-blue-400" }, { v: "7", l: "AI Engines", c: "from-violet-400 to-purple-400" }, { v: "95%", l: "Signal Accuracy", c: "from-emerald-400 to-cyan-400" }, { v: "Zero", l: "Configuration", c: "from-amber-400 to-orange-400" }].map((s, i) => (
              <motion.div key={i} variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }} transition={{ delay: i * 0.08 }}
                className="p-8 rounded-3xl bg-white/3 border border-white/8 hover:border-white/15 hover:-translate-y-1 transition-all duration-300 text-center backdrop-blur-xl group">
                <div className={`text-4xl md:text-5xl font-black mb-3 bg-gradient-to-r ${s.c} bg-clip-text text-transparent`}>{s.v}</div>
                <div className="text-xs font-bold uppercase tracking-widest text-gray-500 group-hover:text-gray-400 transition-colors">{s.l}</div>
              </motion.div>
            ))}
          </div>
        </section>

        {/* ── PROBLEM / SOLUTION ────────────────────────────────────────────────── */}
        <section className="py-24 px-6 md:px-16">
          <div className="max-w-7xl mx-auto">
            <motion.div variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}>
              <div className="inline-block px-4 py-1.5 rounded-full border border-cyan-500/25 bg-cyan-500/8 text-cyan-400 text-[11px] font-bold tracking-widest uppercase mb-6">THE DIFFERENCE</div>
              <h2 className="text-4xl md:text-5xl font-black mb-5 leading-tight">Beyond Dashboards.<br /><span className="text-violet-400">Into Decisions.</span></h2>
              <p className="text-gray-400 text-lg max-w-2xl mb-16">Traditional BI tools stop at "what happened." Cosmos Intelligence explains why, predicts what's next, and tells you exactly what to do.</p>
            </motion.div>
            <div className="grid md:grid-cols-2 gap-8">
              <motion.div variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }} transition={{ delay: 0.1 }}
                className="p-10 rounded-3xl bg-rose-500/4 border border-rose-500/15">
                <h3 className="text-rose-500 font-black uppercase tracking-wider text-xs flex items-center gap-2 mb-8">✕ Traditional BI Tools</h3>
                <ul className="space-y-3">
                  {["\"Revenue dropped 18% this month.\"", "\"Customer churn has increased.\"", "\"Sales are lower than last quarter.\"", "\"Orders declined in the West region.\""].map((t, i) => (
                    <li key={i} className="p-4 rounded-2xl bg-rose-500/5 border-l-2 border-rose-500/30 text-gray-400 text-sm leading-relaxed">{t}</li>
                  ))}
                  <li className="p-4 text-gray-600 text-sm italic">→ No explanation. No next steps. You're on your own.</li>
                </ul>
              </motion.div>
              <motion.div variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }} transition={{ delay: 0.2 }}
                className="p-10 rounded-3xl bg-gradient-to-br from-violet-500/8 to-cyan-500/5 border border-violet-500/25 shadow-[0_0_60px_rgba(124,58,237,0.08)]">
                <h3 className="text-cyan-400 font-black uppercase tracking-wider text-xs flex items-center gap-2 mb-8">✦ Cosmos Intelligence</h3>
                <ul className="space-y-3 text-sm">
                  {[
                    { b: "Revenue dropped 18%", t: "primarily due to a 32% decline in returning electronics customers, correlating with Campaign_A pause and a 14% drop in discount usage." },
                    { b: "Root cause attributed:", t: "Campaign pause (62%), West region stockout (21%), Web channel friction (17%). Ranked by contribution, not just correlation." },
                    { b: "Forecast:", t: "If unaddressed, -12% additional decline next month. Intervening recovers +8-12% within 14 days." },
                    { b: "Recommended action:", t: "Reactivate Campaign_A at +25% budget. Target electronics repeat buyers with 15% discount. Launch re-engagement email sequence." },
                  ].map((item, i) => (
                    <li key={i} className="p-4 rounded-2xl bg-violet-500/8 border-l-2 border-violet-500 leading-relaxed text-gray-200">
                      <span className="text-cyan-400 font-bold">{item.b} </span>{item.t}
                    </li>
                  ))}
                </ul>
              </motion.div>
            </div>
          </div>
        </section>

        {/* ── INTELLIGENCE LEVELS ───────────────────────────────────────────────── */}
        <section className="py-24 px-6 md:px-16" id="features">
          <div className="max-w-7xl mx-auto">
            <motion.div variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}>
              <div className="inline-block px-4 py-1.5 rounded-full border border-cyan-500/25 bg-cyan-500/8 text-cyan-400 text-[11px] font-bold tracking-widest uppercase mb-6">INTELLIGENCE FRAMEWORK</div>
              <h2 className="text-4xl md:text-5xl font-black mb-5 leading-tight">Five Levels Deep.<br /><span className="text-violet-400">Every Time.</span></h2>
              <p className="text-gray-400 text-lg max-w-2xl mb-16">Most analytics answers one question. Cosmos Intelligence answers five — automatically, from every dataset you upload.</p>
            </motion.div>
            <div className="flex flex-col gap-5">
              {[
                { n: "01", t: "Surface Metrics — What Happened", d: "Instant KPIs: revenue, orders, AOV, conversion rate, and health score — computed and compared against prior periods with statistical significance scoring.", from: "from-blue-800", to: "to-blue-500", text: "text-blue-200" },
                { n: "02", t: "Root Cause Analysis — Why It Happened", d: "Multi-dimensional attribution across 9 axes — campaign, region, category, channel, discount band, inventory status, and more. Ranked by % contribution, not just correlation.", from: "from-violet-800", to: "to-violet-500", text: "text-violet-200" },
                { n: "03", t: "Predictive Forecast — What Will Happen", d: "14-day multi-metric forecast with confidence intervals. Uses Prophet time-series or weighted regression with automatic model selection based on data characteristics.", from: "from-emerald-800", to: "to-emerald-500", text: "text-emerald-200" },
                { n: "04", t: "Strategic Recommendations — What To Do", d: "Priority-ranked action items with owner assignment, expected impact range (% revenue recovery), AI trust score, timeline, and confidence score built from dimensional playbooks.", from: "from-amber-800", to: "to-amber-500", text: "text-amber-200" },
                { n: "05", t: "Scenario Simulation — What If", d: "Ask the AI assistant \"What if we increase discounts by 10%?\" or \"What happens if Campaign_B is paused?\" and receive quantified impact estimates grounded in your actual data patterns.", from: "from-pink-800", to: "to-pink-500", text: "text-pink-200" },
              ].map((lvl, i) => (
                <motion.div key={i} variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }} transition={{ delay: i * 0.07 }}
                  className="flex gap-6 p-7 rounded-3xl bg-white/3 border border-white/8 hover:border-white/15 hover:bg-white/5 transition-all duration-300 items-start group">
                  <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${lvl.from} ${lvl.to} ${lvl.text} flex items-center justify-center font-black text-xl shrink-0 group-hover:scale-110 transition-transform shadow-lg`}>{lvl.n}</div>
                  <div>
                    <h3 className="text-lg font-bold mb-2 text-white">{lvl.t}</h3>
                    <p className="text-gray-400 text-sm leading-relaxed">{lvl.d}</p>
                  </div>
                  <ChevronRight size={18} className="text-gray-600 group-hover:text-white group-hover:translate-x-1 transition-all mt-1 shrink-0 hidden md:block" />
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* ── PIPELINE ──────────────────────────────────────────────────────────── */}
        <section className="py-24 px-6 md:px-16" id="pipeline">
          <div className="max-w-7xl mx-auto">
            <motion.div variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}>
              <div className="inline-block px-4 py-1.5 rounded-full border border-cyan-500/25 bg-cyan-500/8 text-cyan-400 text-[11px] font-bold tracking-widest uppercase mb-6">THE PIPELINE</div>
              <h2 className="text-4xl md:text-5xl font-black mb-5 leading-tight">Nine Stages.<br /><span className="text-violet-400">One Upload.</span></h2>
              <p className="text-gray-400 text-lg max-w-2xl mb-16">Every dataset runs through a fully automated intelligence pipeline. No configuration, no schemas, no SQL.</p>
            </motion.div>
            <div className="grid md:grid-cols-3 gap-5">
              {[
                { s: "STAGE 01", t: "Ingest", d: "Accepts any CSV. Auto-detects date columns, numeric fields, dimensions, and categorical variables. Handles messy real-world data." },
                { s: "STAGE 02", t: "Validate", d: "Schema validation, null handling, data type coercion, duplicate detection. Returns data quality report before processing." },
                { s: "STAGE 03", t: "Profile", d: "Statistical profiling — distributions, cardinality, temporal coverage, outlier surface scan. Maps to insight templates automatically." },
                { s: "STAGE 04", t: "Transform", d: "Derives AOV, conversion rate, growth rates, rolling averages. Aggregates by all dimensions. Produces enriched analytical dataset." },
                { s: "STAGE 05", t: "Detect", d: "Isolation Forest anomaly detection across all metric dimensions. Severity scoring: CRITICAL / WARNING / NORMAL. Period-over-period comparison." },
                { s: "STAGE 06", t: "Attribute", d: "Nine-dimension root cause attribution. Contribution % per driver. Enterprise signals: inventory, incidents, discount bands." },
                { s: "STAGE 07", t: "Forecast", d: "14-day multi-metric projection. Confidence intervals. Prophet preferred, linear regression fallback. Trend + seasonality decomposition." },
                { s: "STAGE 08", t: "Recommend", d: "Playbook-driven action generation. Priority assignment by contribution magnitude and severity. Owner, impact range, AI trust score per action." },
                { s: "STAGE 09", t: "Synthesize", d: "Claude AI generates executive briefing. Confidence score from multi-metric signal strength. Deterministic fallback when no API key provided." },
              ].map((st, i) => (
                <motion.div key={i} variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }} transition={{ delay: (i % 3) * 0.08 }}
                  className="p-7 rounded-3xl bg-white/3 border border-white/8 hover:-translate-y-1 hover:border-violet-500/40 hover:bg-violet-500/4 transition-all duration-300 relative overflow-hidden group">
                  <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-violet-600 to-cyan-400 opacity-40 group-hover:opacity-100 transition-opacity" />
                  <div className="text-cyan-400 font-mono text-xs font-bold mb-4 tracking-widest">{st.s}</div>
                  <h3 className="text-base font-bold mb-3 text-white">{st.t}</h3>
                  <p className="text-gray-400 text-sm leading-relaxed">{st.d}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* ── CAPABILITIES ──────────────────────────────────────────────────────── */}
        <section className="py-24 px-6 md:px-16">
          <div className="max-w-7xl mx-auto">
            <motion.div variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}>
              <div className="inline-block px-4 py-1.5 rounded-full border border-cyan-500/25 bg-cyan-500/8 text-cyan-400 text-[11px] font-bold tracking-widest uppercase mb-6">CAPABILITIES</div>
              <h2 className="text-4xl md:text-5xl font-black mb-5 leading-tight">Every Analysis<br /><span className="text-violet-400">You'll Ever Need.</span></h2>
              <p className="text-gray-400 text-lg max-w-2xl mb-16">Cosmos generates 20+ analytics views from a single CSV. No dashboard building required.</p>
            </motion.div>
            <div className="grid md:grid-cols-3 gap-5">
              {[
                { I: BarChart3, t: "Revenue Intelligence", d: "Trend analysis, Bollinger bands, moving averages, multi-metric overlay, period decomposition." },
                { I: Activity, t: "Anomaly Detection", d: "Isolation Forest ML across all metrics. Severity scoring. Statistical significance. Anomaly calendar heatmap." },
                { I: Target, t: "Root Cause Attribution", d: "9-dimension waterfall analysis. Contribution % ranking. Correlated driver detection. Enterprise signal overlay." },
                { I: TrendingUp, t: "Predictive Forecasting", d: "14-day multi-metric projection with confidence bands. WoW growth decomposition. Scenario modeling." },
                { I: PieChart, t: "Segmentation Analysis", d: "Revenue by region, category, channel, campaign. Cross-segment comparison. Concentration risk scoring." },
                { I: Lightbulb, t: "Decision Engine", d: "Priority-ranked recommendations with AI trust score. Expected revenue recovery. Implementation timeline." },
                { I: MessageSquare, t: "AI Chat Assistant", d: "Context-aware Q&A powered by Claude. Answers grounded in your uploaded data only. No hallucination risk." },
                { I: FileText, t: "Executive Briefing", d: "C-suite narrative. Confidence-scored. LLM-powered or deterministic fallback. Export-ready." },
                { I: Trash2, t: "Complete Data Deletion", d: "One-click deletion of all raw data, processed outputs, AI context, and session artifacts." },
              ].map((f, i) => (
                <motion.div key={i} variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }} transition={{ delay: Math.min(i * 0.05, 0.3) }}
                  className="p-7 rounded-3xl bg-white/3 border border-white/8 hover:border-cyan-500/30 hover:bg-cyan-500/3 transition-all duration-300 group">
                  <f.I className="w-7 h-7 text-violet-400 mb-5 group-hover:text-cyan-400 transition-colors" />
                  <h3 className="font-bold mb-3 text-white">{f.t}</h3>
                  <p className="text-sm text-gray-400 leading-relaxed">{f.d}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* ── PRIVACY ───────────────────────────────────────────────────────────── */}
        <section className="py-24 px-6 md:px-16" id="privacy">
          <div className="max-w-7xl mx-auto">
            <motion.div variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}>
              <div className="inline-block px-4 py-1.5 rounded-full border border-cyan-500/25 bg-cyan-500/8 text-cyan-400 text-[11px] font-bold tracking-widest uppercase mb-6">DATA PRIVACY</div>
              <h2 className="text-4xl md:text-5xl font-black mb-5 leading-tight">Your Data.<br /><span className="text-violet-400">Your Control.</span></h2>
              <p className="text-gray-400 text-lg max-w-2xl mb-16">We built privacy into the architecture, not as an afterthought. Here's exactly what happens to your data.</p>
            </motion.div>
            <div className="grid md:grid-cols-2 gap-7">
              {[
                { I: Lock, t: "Demo Mode: Zero Upload", d: "In demo mode, all analysis runs locally in your browser. No data is transmitted to any server. Your CSV never leaves your device." },
                { I: Shield, t: "Upload Mode: Encrypted Transit", d: "Uploaded files go directly to the secure backend API over HTTPS. Files are processed in isolated temp storage and never persisted without consent." },
                { I: Trash2, t: "Complete Hard Delete", d: "Clicking \"Delete Data\" triggers a full pipeline deletion: raw CSV, processed outputs, AI context, derived metrics, and all session artifacts. Nothing is retained." },
                { I: FileClock, t: "Audit Trail", d: "Every data access and deletion event is logged via structured JSON audit logs. You can request a deletion confirmation log at any time." },
              ].map((card, i) => (
                <motion.div key={i} variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }} transition={{ delay: i * 0.08 }}
                  className="p-8 rounded-3xl bg-white/3 border border-white/8 flex gap-6 items-start hover:border-cyan-500/25 transition-all duration-300">
                  <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center shrink-0">
                    <card.I className="text-cyan-400" size={20} />
                  </div>
                  <div>
                    <h3 className="font-bold mb-2 text-white">{card.t}</h3>
                    <p className="text-sm text-gray-400 leading-relaxed">{card.d}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* ── CTA ───────────────────────────────────────────────────────────────── */}
        <section className="py-32 px-6 md:px-16 text-center">
          <div className="max-w-3xl mx-auto">
            <motion.div variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}>
              <h2 className="text-4xl md:text-6xl font-black mb-8 leading-tight">
                <span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">Ready to See Your Data</span>
                <br /><span className="text-white">Come Alive?</span>
              </h2>
              <p className="text-gray-400 text-lg mb-10">Join enterprises that have replaced static dashboards with autonomous intelligence.</p>
              <Link href="/upload"
                className="inline-flex items-center gap-3 px-10 py-5 rounded-2xl bg-gradient-to-r from-violet-600 to-violet-500 text-white font-bold text-lg shadow-[0_4px_40px_rgba(124,58,237,0.4)] hover:-translate-y-1 hover:shadow-[0_10px_50px_rgba(124,58,237,0.5)] transition-all duration-300">
                Start Analyzing for Free <ArrowRight size={20} />
              </Link>
              <p className="text-xs text-gray-600 mt-6">🔒 Demo runs entirely in your browser. Upload mode: data deleted on session end.</p>
            </motion.div>
          </div>
        </section>

      </main>

      {/* ── FOOTER ────────────────────────────────────────────────────────────── */}
      <footer className="border-t border-white/8 py-10 px-6 md:px-16">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5 font-bold text-sm">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-violet-600 to-cyan-400 flex items-center justify-center text-xs">✦</div>
            <div className="flex flex-col">
              <span className="text-gray-300 leading-none">Cosmos Intelligence</span>
              <span className="text-[9px] text-cyan-500/70 font-bold tracking-[0.1em] mt-1 pt-0.5">ARCHITECTED BY VIVEK KOMMAREDDY</span>
            </div>
          </div>
          <div className="text-xs text-gray-600">© 2026 Cosmos Intelligence. Enterprise AI Analytics. All rights reserved.</div>
        </div>
      </footer>

    </div>
  );
}
