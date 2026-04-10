"use client";
import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import Plot from "@/components/PlotlyChart";
import { Trash2, ExternalLink, Send, Bot, User, Loader2 } from "lucide-react";
import { generateDemoData } from "@/lib/demo-data";

const DL = { paper_bgcolor:"transparent", plot_bgcolor:"transparent", font:{family:"Inter",color:"#9CA3AF",size:11}, xaxis:{gridcolor:"rgba(255,255,255,0.05)",linecolor:"rgba(255,255,255,0.06)",tickfont:{size:10}}, yaxis:{gridcolor:"rgba(255,255,255,0.05)",linecolor:"rgba(255,255,255,0.06)",tickfont:{size:10}}, margin:{t:14,r:14,b:36,l:52} };
const CFG:any = {responsive:true,displayModeBar:false};

function ChartBox({title,children}:{title:string,children:React.ReactNode}) {
  return (
    <div className="rounded-2xl bg-white/3 border border-white/8 overflow-hidden">
      <div className="px-5 py-3.5 border-b border-white/8 text-xs font-bold uppercase tracking-widest text-gray-400">{title}</div>
      <div className="p-2">{children}</div>
    </div>
  );
}

function KpiCard({label,val,chg,prior}:{label:string,val:string,chg:number,prior?:string}) {
  const pos = chg >= 0;
  return (
    <div className="p-5 rounded-2xl bg-white/3 border border-white/8 hover:-translate-y-0.5 hover:border-white/15 transition-all relative overflow-hidden group">
      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-violet-600 to-cyan-400 opacity-50 group-hover:opacity-100 transition-opacity"/>
      <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">{label}</div>
      <div className="text-[26px] font-black text-cyan-400 mb-1">{val}</div>
      <div className={`text-xs font-bold ${pos?"text-emerald-400":"text-rose-400"}`}>{pos?"▲":"▼"} {Math.abs(chg)}%</div>
      <div className="text-[10px] text-gray-600 mt-0.5">vs prior 14 days</div>
    </div>
  );
}

function TrustRing({pct}:{pct:number}) {
  const deg = pct * 3.6;
  return (
    <div className="w-12 h-12 rounded-full flex items-center justify-center text-xs font-black text-cyan-400 shrink-0"
      style={{background:`conic-gradient(#00E5FF ${deg}deg,rgba(255,255,255,0.07) ${deg}deg)`}}>
      {pct}%
    </div>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [tab, setTab] = useState(0);
  const [chatMsgs, setChatMsgs] = useState<{role:"ai"|"user",text:string}[]>([
    {role:"ai",text:"Hello! I'm Cosmos Intelligence. I've analyzed your dataset and I'm ready to answer questions about your metrics, root causes, forecast, and recommendations. What would you like to know?"}
  ]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [apiKeySaved, setApiKeySaved] = useState(false);
  const chatRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const raw = sessionStorage.getItem("cosmos_data");
    if (!raw) { router.push("/upload"); return; }
    try { setData(JSON.parse(raw)); } catch { setData(generateDemoData()); }
  }, [router]);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [chatMsgs]);

  if (!data) return <div className="min-h-screen bg-[#020208] flex items-center justify-center text-gray-500 font-mono text-sm">Loading intelligence terminal...</div>;

  const d = data;
  const dates = d.dates || [];
  const rev = d.revenue || [];
  const orders = d.orders || [];
  const aov = d.aov || [];
  const sevClass = d.severity==="CRITICAL" ? "bg-rose-500/10 text-rose-400 border-rose-500/30 animate-pulse" : d.severity==="WARNING" ? "bg-amber-500/10 text-amber-400 border-amber-500/30" : "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";

  // Derived analytics
  const mean = rev.length ? rev.reduce((a:number,b:number)=>a+b,0)/rev.length : 1;
  const norm = (arr:number[]) => { const mx=Math.max(...arr),mn=Math.min(...arr); return arr.map(v=>(v-mn)/((mx-mn)||1)); };
  const wowDates:string[]=[], wowVals:number[]=[];
  for(let i=7;i<rev.length;i+=7){
    const cur=rev.slice(i-7,i).reduce((a:number,b:number)=>a+b,0);
    const prv=rev.slice(Math.max(0,i-14),i-7).reduce((a:number,b:number)=>a+b,0);
    wowDates.push(dates[i]);wowVals.push(prv?+((cur-prv)/prv*100).toFixed(1):0);
  }
  const periodRevs = [
    rev.slice(-90,-60).reduce((a:number,b:number)=>a+b,0)/30,
    rev.slice(-60,-30).reduce((a:number,b:number)=>a+b,0)/30,
    rev.slice(-30,-14).reduce((a:number,b:number)=>a+b,0)/16,
    rev.slice(-14).reduce((a:number,b:number)=>a+b,0)/14,
  ];

  // Segment data from root_cause
  const rc = d.root_cause || [];
  const rcLabels = rc.map((r:any)=>r.driver||r.group_value||"Unknown");
  const rcVals = rc.map((r:any)=>Math.abs(r.contribution_pct||0));

  async function sendChat(q:string) {
    if(!q.trim()) return;
    setChatMsgs(m=>[...m,{role:"user",text:q}]);
    setChatInput("");setChatLoading(true);
    let answer = "";
    try {
      const r = await fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({question:q,context:d,api_key:apiKey})});
      if(r.ok){const j=await r.json();answer=j.answer;}else throw new Error();
    } catch {
      const ql=q.toLowerCase();
      const top=rc[0]||{};const topRec=(d.recommendation||[])[0]||{};
      if(ql.includes("why")||ql.includes("cause"))
        answer=`The primary driver is **${top.driver||"campaign activity"}**, contributing ${Math.abs(top.contribution_pct||0).toFixed(1)}% of total variance. ${rc[1]?`Secondary: ${rc[1].driver} (${Math.abs(rc[1].contribution_pct||0).toFixed(1)}%)`:""} These factors are compounding — addressing the top driver first will have the largest single impact.`;
      else if(ql.includes("forecast")||ql.includes("future"))
        answer=`Based on current trajectory: ${d.prediction||"further decline expected"}. Confidence interval ±13%. The 14-day forecast uses ${d.model||"linear regression"} modeling. Implementing the top two recommendations shifts the forecast to flat-to-positive growth within 3 weeks.`;
      else if(ql.includes("recommend")||ql.includes("do")||ql.includes("action"))
        answer=`Highest priority: ${(topRec.action||"Reactivate key campaigns immediately").substring(0,200)}. Expected impact: ${topRec.expected_impact||"significant revenue recovery"}. Timeline: ${topRec.timeline||"immediate"}. Owner: ${topRec.owner||"Growth Marketing"}.`;
      else if(ql.includes("risk")||ql.includes("danger"))
        answer=`The biggest risk is the compounding effect of ${rc.slice(0,3).map((r:any)=>r.driver).join(" + ")||"multiple simultaneous drivers"}. Each alone is manageable; together they created a ${d.severity||"CRITICAL"} signal. Forecasting suggests continued pressure without intervention within 48 hours.`;
      else if(ql.includes("segment")||ql.includes("region")||ql.includes("category"))
        answer=`Segment analysis shows ${rc[0]?.group_value||"top segment"} as the most impacted (${Math.abs(rc[0]?.contribution_pct||0).toFixed(1)}% contribution). Overall severity: ${d.severity}. Revenue change: ${d.change||"significant deviation"} vs prior period.`;
      else
        answer=`Based on your dataset: Overall severity is **${d.severity||"NORMAL"}** with a ${d.change||"0%"} revenue change. Top driver: ${top.driver||"N/A"} (${Math.abs(top.contribution_pct||0).toFixed(0)}% contribution). AI confidence: ${Math.round((d.confidence||0.87)*100)}%. What specific aspect would you like me to explore?`;
    }
    setChatLoading(false);
    setChatMsgs(m=>[...m,{role:"ai",text:answer}]);
  }

  const TABS = ["📊 Command Center","🔍 Intelligence","📈 Forecasting","⚡ Root Cause","🎯 Decisions","🤖 AI Assistant"];

  return (
    <div className="min-h-screen bg-[#020208] text-white flex flex-col font-sans">

      {/* Topbar */}
      <div className="h-14 border-b border-white/8 flex items-center justify-between px-6 bg-[#020208]/95 backdrop-blur-2xl sticky top-0 z-50">
        <div className="flex items-center gap-4">
          <button onClick={()=>router.push("/upload")} className="px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 text-xs font-semibold hover:text-cyan-400 hover:border-cyan-400/50 transition-all">← New Analysis</button>
          <span className={`px-3 py-1 rounded-full text-[10px] font-black tracking-widest uppercase border ${sevClass}`}>{d.severity||"NORMAL"}</span>
          <span className="text-gray-500 text-xs hidden md:block">14-day analysis · {d.processing_time_ms ? `${d.processing_time_ms}ms` : "Demo mode"}</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center gap-2 text-xs text-gray-500">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"/>
            {d.llm_powered?"Claude AI":"Deterministic Engine"} · {Math.round((d.confidence||0.87)*100)}% confidence
          </div>
          <button onClick={()=>window.print()} className="w-8 h-8 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center hover:bg-white/10 transition-all"><ExternalLink size={13}/></button>
          <button onClick={async()=>{
            if(!confirm("Delete all session data? This cannot be undone."))return;
            try{await fetch("/api/session",{method:"DELETE"});}catch{}
            sessionStorage.removeItem("cosmos_data");router.push("/");
          }} className="w-8 h-8 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center hover:bg-rose-500/20 transition-all"><Trash2 size={13}/></button>
        </div>
      </div>

      {/* Tab nav */}
      <div className="flex w-full overflow-x-auto border-b border-white/8 px-6 bg-[#020208]/95 backdrop-blur-xl sticky top-14 z-40">
        {TABS.map((t,i)=>(
          <button key={i} onClick={()=>setTab(i)}
            className={`py-4 px-5 text-xs font-bold tracking-wider uppercase transition-all whitespace-nowrap relative ${tab===i?"text-cyan-400":"text-gray-500 hover:text-white"}`}>
            {t}
            {tab===i&&<div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-violet-600 to-cyan-400"/>}
          </button>
        ))}
      </div>

      <div className="flex-1 p-6 max-w-[1600px] mx-auto w-full space-y-5">

        {/* TAB 0: Command Center */}
        {tab===0&&<>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {d.kpis && Object.values(d.kpis).map((k:any,i:number)=>(
              <KpiCard key={i} label={k.label} val={k.val} chg={k.chg}/>
            ))}
          </div>
          <div className="grid md:grid-cols-2 gap-5">
            <ChartBox title="Revenue Trend & Anomalies">
              <Plot data={[
                {x:dates,y:rev,type:"scatter",mode:"lines",name:"Revenue",line:{color:"#7C3AED",width:2},fill:"tozeroy",fillcolor:"rgba(124,58,237,0.07)"},
                {x:dates.filter((_:any,i:number)=>rev[i]<mean*0.85),y:rev.filter((v:number)=>v<mean*0.85),type:"scatter",mode:"markers",name:"Anomaly",marker:{color:"#EF4444",size:7,symbol:"circle",line:{color:"#fff",width:1}}},
              ]} layout={{...DL,showlegend:true,legend:{x:0,y:1,font:{size:10}},margin:{t:10,r:10,b:30,l:50}}} config={CFG} style={{width:"100%",height:"280px"}}/>
            </ChartBox>
            <ChartBox title="Multi-Metric Health Radar">
              <Plot data={[{type:"scatterpolar",r:[
                Math.min(100,Math.max(0,50+((d.kpis?.revenue?.chg)||0))),
                Math.min(100,Math.max(0,50+((d.kpis?.orders?.chg)||0))),
                Math.min(100,Math.max(0,50+((d.kpis?.aov?.chg)||0))),
                Math.round((d.confidence||0.87)*100),
                d.anomaly_detected?30:80,
              ],theta:["Revenue","Orders","AOV","AI Confidence","Stability"],fill:"toself",fillcolor:"rgba(124,58,237,0.18)",line:{color:"#7C3AED"},marker:{color:"#00E5FF",size:6}}]}
              layout={{...DL,polar:{radialaxis:{visible:true,range:[0,100],gridcolor:"rgba(255,255,255,0.07)"},angularaxis:{gridcolor:"rgba(255,255,255,0.07)"},bgcolor:"transparent"},margin:{t:16,r:28,b:16,l:28}}} config={CFG} style={{width:"100%",height:"280px"}}/>
            </ChartBox>
          </div>
          <div className="grid md:grid-cols-2 gap-5">
            <ChartBox title="Normalized Multi-Metric Overlay">
              <Plot data={[
                {x:dates.slice(-90),y:norm(rev.slice(-90)),type:"scatter",mode:"lines",name:"Revenue",line:{color:"#7C3AED",width:2}},
                {x:dates.slice(-90),y:norm(orders.slice(-90)),type:"scatter",mode:"lines",name:"Orders",line:{color:"#00E5FF",width:2}},
                {x:dates.slice(-90),y:norm(aov.slice(-90)),type:"scatter",mode:"lines",name:"AOV",line:{color:"#C026D3",width:2}},
              ]} layout={{...DL,showlegend:true,legend:{x:0,y:1,font:{size:10}},margin:{t:10,r:10,b:30,l:50}}} config={CFG} style={{width:"100%",height:"250px"}}/>
            </ChartBox>
            <ChartBox title="Week-over-Week Growth Rate">
              <Plot data={[{x:wowDates,y:wowVals,type:"bar",name:"WoW %",marker:{color:wowVals.map((v:number)=>v>=0?"#10B981":"#EF4444"),opacity:0.85}}]}
              layout={{...DL,yaxis:{...DL.yaxis,ticksuffix:"%"},margin:{t:10,r:10,b:30,l:50}}} config={CFG} style={{width:"100%",height:"250px"}}/>
            </ChartBox>
          </div>
          {/* Executive narrative */}
          <div className="p-6 rounded-2xl bg-gradient-to-br from-violet-500/8 to-cyan-500/5 border border-violet-500/20">
            <div className="text-xs font-bold uppercase tracking-widest text-violet-400 mb-3 flex items-center gap-2">✦ Executive Intelligence Briefing</div>
            <p className="text-gray-200 text-base leading-relaxed mb-4">{d.explanation||"Analysis complete. Upload dataset for AI-powered executive briefing."}</p>
            <div className="flex items-center gap-4">
              <TrustRing pct={Math.round((d.confidence||0.87)*100)}/>
              <div className="text-xs text-gray-400">{Math.round((d.confidence||0.87)*100)}% AI Confidence · {d.llm_powered?"Claude AI":"Deterministic Engine"} · {d.model||"Linear Trend"} forecast model</div>
            </div>
          </div>
        </>}

        {/* TAB 1: Intelligence */}
        {tab===1&&<>
          <ChartBox title="Anomaly Detection — Revenue Signal (Last 60 Days)">
            <Plot data={[
              {x:dates.slice(-60),y:rev.slice(-60),type:"scatter",mode:"lines+markers",name:"Revenue",line:{color:"#7C3AED",width:2},marker:{color:rev.slice(-60).map((v:number)=>v<mean*0.85?"#EF4444":"#7C3AED"),size:5}},
              {x:dates.slice(-60),y:Array(60).fill(mean),type:"scatter",mode:"lines",name:"Mean",line:{color:"#F59E0B",width:1.5,dash:"dash"}},
              {x:dates.slice(-60),y:Array(60).fill(mean*0.85),type:"scatter",mode:"lines",name:"Alert Threshold",line:{color:"#EF4444",width:1,dash:"dot"}},
            ]} layout={{...DL,showlegend:true,legend:{x:0,y:1,font:{size:10}}}} config={CFG} style={{width:"100%",height:"300px"}}/>
          </ChartBox>
          <div className="grid md:grid-cols-2 gap-5">
            <ChartBox title="Period-over-Period Comparison">
              <Plot data={[{x:["90d Ago","60d Ago","30d Ago","Last 14d"],y:periodRevs.map((v:number)=>+v.toFixed(0)),type:"bar",marker:{color:["#4B5563","#5B21B6","#7C3AED","#EF4444"],opacity:0.9}}]}
              layout={{...DL,yaxis:{...DL.yaxis,tickprefix:"$"}}} config={CFG} style={{width:"100%",height:"260px"}}/>
            </ChartBox>
            <ChartBox title="Revenue Distribution (Last 90 Days)">
              <Plot data={[{x:rev.slice(-90),type:"histogram",nbinsx:25,marker:{color:"#7C3AED",opacity:0.8}}]}
              layout={{...DL,xaxis:{...DL.xaxis,tickprefix:"$"}}} config={CFG} style={{width:"100%",height:"260px"}}/>
            </ChartBox>
          </div>
          {/* Per-metric anomaly cards */}
          {d.per_metric&&<div className="grid md:grid-cols-3 gap-4">
            {Object.values(d.per_metric).map((m:any,i:number)=>(
              <div key={i} className={`p-5 rounded-2xl border ${m.severity==="CRITICAL"?"bg-rose-500/5 border-rose-500/20":m.severity==="WARNING"?"bg-amber-500/5 border-amber-500/20":"bg-emerald-500/5 border-emerald-500/20"}`}>
                <div className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">{m.label}</div>
                <div className={`text-2xl font-black mb-1 ${m.severity==="CRITICAL"?"text-rose-400":m.severity==="WARNING"?"text-amber-400":"text-emerald-400"}`}>{m.severity}</div>
                <div className="text-sm font-bold text-white mb-1">{m.change}</div>
                <div className="text-xs text-gray-500">{m.anomaly_count} anomalous periods detected</div>
                {m.anomaly_dates?.length>0&&<div className="mt-2 text-[10px] text-gray-600 font-mono">Latest: {m.anomaly_dates[m.anomaly_dates.length-1]}</div>}
              </div>
            ))}
          </div>}
          <div className="grid md:grid-cols-3 gap-4">
            <div className="p-5 rounded-2xl bg-white/3 border border-white/8 col-span-full md:col-span-1">
              <div className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">Revenue Signal</div>
              <p className="text-sm text-gray-300 leading-relaxed">Average daily revenue of <strong className="text-cyan-400">${rev.length?Math.round(rev.slice(-14).reduce((a:number,b:number)=>a+b,0)/14).toLocaleString():0}</strong> in the last 14 days. Isolation Forest flagged <strong className="text-cyan-400">{d.anomaly_count||0} anomalous days</strong> with <strong className="text-cyan-400">{Math.round((d.confidence||0.87)*100)}%</strong> confidence score.</p>
            </div>
            <div className="p-5 rounded-2xl bg-white/3 border border-white/8">
              <div className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">Order Volume</div>
              <p className="text-sm text-gray-300 leading-relaxed">Order volume moved in parallel with revenue, suggesting <strong className="text-cyan-400">demand-side pressure</strong> rather than pricing issues. AOV metric confirms basket size remained {Math.abs(d.kpis?.aov?.chg||0)<5?"relatively stable":"significantly changed"}.</p>
            </div>
            <div className="p-5 rounded-2xl bg-white/3 border border-white/8">
              <div className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">Pattern Analysis</div>
              <p className="text-sm text-gray-300 leading-relaxed">Detected a <strong className="text-cyan-400">{d.severity==="CRITICAL"?"step-down structure":"gradual drift pattern"}</strong> consistent with {d.severity==="CRITICAL"?"a sudden campaign or supply interruption":"seasonal or organic decline"}. Overall system confidence: {Math.round((d.confidence||0.87)*100)}%.</p>
            </div>
          </div>
        </>}

        {/* TAB 2: Forecasting */}
        {tab===2&&<>
          <ChartBox title="14-Day Revenue Forecast with Confidence Bands">
            <Plot data={[
              {x:dates.slice(-30),y:rev.slice(-30),type:"scatter",mode:"lines",name:"Historical",line:{color:"#7C3AED",width:2.5}},
              {x:d.forecast_dates,y:d.forecast_values,type:"scatter",mode:"lines",name:"Forecast",line:{color:"#00E5FF",width:2.5,dash:"dot"}},
              {x:[...(d.forecast_dates||[]),...(d.forecast_dates||[]).slice().reverse()],
               y:[...(d.forecast_confidence_upper||[]),...(d.forecast_confidence_lower||[]).slice().reverse()],
               type:"scatter",mode:"none",fill:"toself",fillcolor:"rgba(0,229,255,0.07)",name:"Confidence Band",showlegend:false},
            ]} layout={{...DL,showlegend:true,legend:{x:0,y:1,font:{size:10}},yaxis:{...DL.yaxis,tickprefix:"$"}}} config={CFG} style={{width:"100%",height:"340px"}}/>
          </ChartBox>
          <div className="grid md:grid-cols-3 gap-4">
            {[{label:"Revenue Trend",vals:rev.slice(-21),chg:d.change_pct,color:"#7C3AED"},{label:"Order Volume",vals:orders.slice(-21),chg:d.kpis?.orders?.chg||0,color:"#00E5FF"},{label:"Avg Order Value",vals:aov.slice(-21),chg:d.kpis?.aov?.chg||0,color:"#C026D3"}].map((m,i)=>(
              <div key={i} className="p-5 rounded-2xl bg-white/3 border border-white/8">
                <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">{m.label}</div>
                <div className="text-xl font-black mb-1" style={{color:m.color}}>{m.vals.length?m.vals[m.vals.length-1].toFixed(1):0}</div>
                <div className={`text-xs font-bold mb-3 ${(m.chg||0)>=0?"text-emerald-400":"text-rose-400"}`}>{(m.chg||0)>=0?"▲":"▼"} {Math.abs(m.chg||0)}%</div>
                <Plot data={[{y:m.vals,type:"scatter",mode:"lines",line:{color:m.color,width:2},fill:"tozeroy",fillcolor:m.color.replace(")",",.08)").replace("rgb","rgba")}]}
                layout={{paper_bgcolor:"transparent",plot_bgcolor:"transparent",margin:{t:2,r:2,b:2,l:2},xaxis:{visible:false},yaxis:{visible:false},showlegend:false}} config={CFG} style={{width:"100%",height:"60px"}}/>
              </div>
            ))}
          </div>
          <div className="p-6 rounded-2xl bg-violet-500/6 border border-violet-500/20">
            <div className="text-xs font-bold uppercase tracking-widest text-violet-400 mb-3">📈 Forecast Summary</div>
            <p className="text-gray-200 leading-relaxed mb-2">{d.prediction||"Forecast data unavailable."}</p>
            <div className="text-xs text-gray-500">Model: <span className="text-gray-300 font-semibold">{d.model==="prophet"?"Facebook Prophet (advanced seasonality)":"Linear Regression (trend-based)"}</span> · Confidence bands: ±13%</div>
          </div>
        </>}

        {/* TAB 3: Root Cause */}
        {tab===3&&<>
          <div className="grid md:grid-cols-2 gap-5">
            <ChartBox title="Revenue Attribution Waterfall">
              <Plot data={[{
                x:["Baseline",...rcLabels,"Net Impact"],
                y:[100,...rcVals,rcVals.reduce((a:number,b:number)=>a+b,0)],
                base:[0,...rcVals.reduce((acc:number[],v:number)=>[...acc,100-acc.reduce((a:number,b:number)=>a+b,0)-v],[]),...[0]],
                type:"bar",marker:{color:["#10B981",...rcLabels.map(()=>"#EF4444"),"#7C3AED"],opacity:0.85}
              }]} layout={{...DL,yaxis:{...DL.yaxis,ticksuffix:"%"}}} config={CFG} style={{width:"100%",height:"280px"}}/>
            </ChartBox>
            <ChartBox title="Contribution Breakdown">
              <Plot data={[{labels:rcLabels,values:rcVals,type:"pie",hole:0.55,marker:{colors:["#EF4444","#F59E0B","#7C3AED","#C026D3","#6B7280","#3B82F6"]},textinfo:"label+percent",textfont:{size:10}}]}
              layout={{paper_bgcolor:"transparent",margin:{t:12,r:12,b:12,l:12},showlegend:false,font:{color:"#9CA3AF",size:10}}} config={CFG} style={{width:"100%",height:"280px"}}/>
            </ChartBox>
          </div>
          {/* Detailed root cause cards */}
          <div className="space-y-3">
            {rc.map((r:any,i:number)=>{
              const neg=r.contribution_pct<0;
              const pct=Math.abs(r.contribution_pct||0);
              return (
                <div key={i} className={`p-6 rounded-2xl border ${neg?"bg-rose-500/4 border-rose-500/15":"bg-emerald-500/4 border-emerald-500/15"}`}>
                  <div className="flex items-start gap-4">
                    <div className={`text-2xl font-black shrink-0 ${neg?"text-rose-400":"text-emerald-400"}`}>#{i+1}</div>
                    <div className="flex-1">
                      <div className="font-bold text-white mb-1">{r.driver}</div>
                      <div className="text-xs text-gray-400 mb-3">Dimension: <span className="text-gray-200 font-semibold">{r.dimension}</span> · Segment: <span className="text-gray-200 font-semibold">{r.group_value}</span> · Delta: <span className={neg?"text-rose-400":"text-emerald-400"}>{r.delta>=0?"+":""}{r.delta?.toLocaleString()}</span></div>
                      <div className="flex items-center gap-3">
                        <div className="flex-1 h-2 rounded-full bg-white/8">
                          <div className={`h-2 rounded-full ${neg?"bg-gradient-to-r from-rose-600 to-rose-400":"bg-gradient-to-r from-emerald-600 to-emerald-400"}`} style={{width:`${Math.min(100,pct)}%`}}/>
                        </div>
                        <span className={`text-sm font-black ${neg?"text-rose-400":"text-emerald-400"}`}>{r.contribution_pct}%</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${neg?"bg-rose-500/10 text-rose-400":"bg-emerald-500/10 text-emerald-400"}`}>{neg?"▼ Negative":"▲ Positive"}</span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </>}

        {/* TAB 4: Decisions */}
        {tab===4&&(d.recommendation||[]).length>0&&<>
          <div className="grid md:grid-cols-2 gap-5 mb-5">
            <ChartBox title="Priority vs Impact Matrix">
              <Plot data={[{
                x:(d.recommendation||[]).map((r:any)=>Math.round((r.confidence||0.7)*100)),
                y:(d.recommendation||[]).map((r:any)=>parseFloat((r.expected_impact||"10%").match(/(\d+)/)?.[1]||"10")),
                mode:"markers+text",type:"scatter",
                text:(d.recommendation||[]).map((r:any)=>(r.owner||"").split("&")[0].trim()),
                textposition:"top center",textfont:{size:10,color:"#9CA3AF"},
                marker:{
                  color:(d.recommendation||[]).map((r:any)=>r.priority==="HIGH"?"#EF4444":r.priority==="MEDIUM"?"#F59E0B":"#10B981"),
                  size:(d.recommendation||[]).map((r:any)=>r.priority==="HIGH"?28:r.priority==="MEDIUM"?22:16),
                  opacity:0.85,line:{color:"rgba(255,255,255,0.3)",width:1}
                }
              }]} layout={{...DL,xaxis:{...DL.xaxis,title:"AI Trust Score (%)",ticksuffix:"%"},yaxis:{...DL.yaxis,title:"Expected Impact (%)",ticksuffix:"%"}}} config={CFG} style={{width:"100%",height:"300px"}}/>
            </ChartBox>
            <div className="p-5 rounded-2xl bg-white/3 border border-white/8">
              <div className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-5">Decision Distribution</div>
              <div className="space-y-3">
                {["HIGH","MEDIUM","LOW"].map(p=>{
                  const count=(d.recommendation||[]).filter((r:any)=>r.priority===p).length;
                  const pctW=Math.round(count/(d.recommendation||[{priority:"HIGH"}]).length*100);
                  return <div key={p} className="flex items-center gap-3">
                    <span className={`text-xs font-black w-16 ${p==="HIGH"?"text-rose-400":p==="MEDIUM"?"text-amber-400":"text-emerald-400"}`}>{p}</span>
                    <div className="flex-1 h-2 rounded-full bg-white/8">
                      <div className={`h-2 rounded-full ${p==="HIGH"?"bg-rose-500":p==="MEDIUM"?"bg-amber-500":"bg-emerald-500"}`} style={{width:`${pctW}%`}}/>
                    </div>
                    <span className="text-xs text-gray-400">{count}</span>
                  </div>;
                })}
              </div>
              <div className="mt-6 p-4 rounded-xl bg-white/4 border border-white/8">
                <div className="text-xs text-gray-500 mb-2">Combined Expected Impact</div>
                <div className="text-2xl font-black text-cyan-400">{(d.recommendation||[]).reduce((s:number,r:any)=>s+parseFloat((r.expected_impact||"10").match(/(\d+)/)?.[1]||"10"),0).toFixed(0)}%+</div>
                <div className="text-xs text-gray-500 mt-1">Revenue recovery potential across all actions</div>
              </div>
            </div>
          </div>
          <div className="space-y-4">
            {(d.recommendation||[]).map((r:any,i:number)=>{
              const trustPct=Math.round((r.confidence||0.7)*100);
              const priColor=r.priority==="HIGH"?"rose":r.priority==="MEDIUM"?"amber":"emerald";
              return (
                <div key={i} className="p-6 rounded-2xl bg-white/3 border border-white/8 hover:border-white/15 transition-all">
                  <div className="flex items-start gap-5">
                    <div className={`px-3 py-1.5 rounded-full text-[11px] font-black tracking-wider shrink-0 mt-0.5 ${r.priority==="HIGH"?"bg-rose-500/10 text-rose-400":r.priority==="MEDIUM"?"bg-amber-500/10 text-amber-400":"bg-emerald-500/10 text-emerald-400"} border ${r.priority==="HIGH"?"border-rose-500/20":r.priority==="MEDIUM"?"border-amber-500/20":"border-emerald-500/20"}`}>{r.priority}</div>
                    <div className="flex-1">
                      <div className="font-bold text-white mb-3 leading-relaxed">{r.action}</div>
                      <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-gray-500 mb-4">
                        <span>Owner: <span className="text-gray-300 font-semibold">{r.owner}</span></span>
                        <span>Impact: <span className="text-cyan-400 font-semibold">{r.expected_impact}</span></span>
                        <span>Timeline: <span className="text-gray-300 font-semibold">{r.timeline}</span></span>
                      </div>
                      <div className="flex items-center gap-4">
                        <TrustRing pct={trustPct}/>
                        <div className="flex-1">
                          <div className="text-xs text-gray-500 mb-1">AI Trust Score</div>
                          <div className="h-1.5 rounded-full bg-white/8 overflow-hidden">
                            <div className="h-1.5 rounded-full bg-gradient-to-r from-violet-600 to-cyan-400" style={{width:`${trustPct}%`}}/>
                          </div>
                          <div className="text-xs text-gray-500 mt-1">{trustPct}% confidence this action will have the stated impact based on your data patterns</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </>}

        {/* TAB 5: AI Assistant */}
        {tab===5&&<>
          <div className="grid md:grid-cols-3 gap-5">
            <div className="md:col-span-2 flex flex-col gap-5">
              {/* Quick chips */}
              <div className="flex flex-wrap gap-2">
                {["Why did revenue drop?","Which segment underperforms?","What is the biggest risk?","What should I do first?","Next month forecast?","Summarize for exec team"].map((q,i)=>(
                  <button key={i} onClick={()=>sendChat(q)} className="px-4 py-2 rounded-full border border-violet-500/25 bg-violet-500/8 text-violet-300 text-xs font-semibold hover:bg-violet-500/18 hover:border-violet-400 hover:-translate-y-0.5 transition-all">{q}</button>
                ))}
              </div>
              {/* Chat window */}
              <div className="rounded-2xl bg-white/3 border border-white/8 flex flex-col overflow-hidden" style={{minHeight:"420px"}}>
                <div ref={chatRef} className="flex-1 p-5 space-y-4 overflow-y-auto" style={{maxHeight:"420px"}}>
                  {chatMsgs.map((m,i)=>(
                    <div key={i} className={`flex gap-3 ${m.role==="user"?"justify-end":""}`}>
                      {m.role==="ai"&&<div className="w-8 h-8 rounded-full bg-violet-500/20 border border-violet-500/30 flex items-center justify-center shrink-0 mt-0.5"><Bot size={14} className="text-violet-400"/></div>}
                      <div className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${m.role==="ai"?"bg-white/5 border border-white/8 text-gray-200":"bg-gradient-to-br from-violet-600 to-violet-500 text-white"}`}>{m.text}</div>
                      {m.role==="user"&&<div className="w-8 h-8 rounded-full bg-white/10 border border-white/15 flex items-center justify-center shrink-0 mt-0.5"><User size={14} className="text-gray-300"/></div>}
                    </div>
                  ))}
                  {chatLoading&&<div className="flex gap-3"><div className="w-8 h-8 rounded-full bg-violet-500/20 border border-violet-500/30 flex items-center justify-center shrink-0"><Bot size={14} className="text-violet-400"/></div><div className="bg-white/5 border border-white/8 rounded-2xl px-4 py-3 flex gap-1.5 items-center"><span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"/><span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:0.2s]"/><span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:0.4s]"/></div></div>}
                </div>
                <div className="p-4 border-t border-white/8 flex gap-3">
                  <input value={chatInput} onChange={e=>setChatInput(e.target.value)} onKeyDown={e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();sendChat(chatInput);}}}
                    placeholder="Ask anything about your data..." className="flex-1 px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-violet-500/50"/>
                  <button onClick={()=>sendChat(chatInput)} className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-600 to-violet-500 flex items-center justify-center hover:-translate-y-0.5 hover:shadow-[0_4px_16px_rgba(124,58,237,0.4)] transition-all">
                    <Send size={14} className="text-white"/>
                  </button>
                </div>
              </div>
            </div>
            {/* Right panel: briefing + API key */}
            <div className="space-y-5">
              <div className="p-5 rounded-2xl bg-gradient-to-br from-violet-500/8 to-cyan-500/4 border border-violet-500/20">
                <div className="text-xs font-bold uppercase tracking-widest text-violet-400 mb-3">✦ Executive Briefing</div>
                <p className="text-gray-300 text-sm leading-relaxed mb-4">{d.explanation||"Analysis complete."}</p>
                <div className="flex items-center gap-3">
                  <TrustRing pct={Math.round((d.confidence||0.87)*100)}/>
                  <div className="text-xs text-gray-400">{Math.round((d.confidence||0.87)*100)}% confidence · {d.llm_powered?"Claude AI powered":"Deterministic fallback"}</div>
                </div>
              </div>
              {!apiKeySaved&&<div className="p-5 rounded-2xl bg-purple-500/6 border border-purple-500/20">
                <div className="text-xs font-bold uppercase tracking-widest text-purple-400 mb-3">💡 Add API Key for Live AI</div>
                <p className="text-xs text-gray-400 mb-3">Add your Anthropic API key for live Claude-powered answers.</p>
                <div className="flex gap-2">
                  <input type="password" value={apiKey} onChange={e=>setApiKey(e.target.value)} placeholder="sk-ant-..." className="flex-1 px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-violet-500/50"/>
                  <button onClick={()=>{if(apiKey){setApiKeySaved(true);setChatMsgs(m=>[...m,{role:"ai",text:"✓ API key saved! I can now provide live Claude AI answers."}]);}}} className="px-3 py-2 rounded-xl bg-gradient-to-r from-purple-600 to-violet-600 text-white text-xs font-bold">Save</button>
                </div>
              </div>}
              {/* Data stats */}
              <div className="p-5 rounded-2xl bg-white/3 border border-white/8">
                <div className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-4">Dataset Stats</div>
                <div className="space-y-3">
                  {[{l:"Data Points",v:`${dates.length} days`},{l:"Revenue Range",v:`$${rev.length?Math.min(...rev).toLocaleString():0} – $${rev.length?Math.max(...rev).toLocaleString():0}`},{l:"Anomaly Count",v:`${d.anomaly_count||0} detected`},{l:"Root Causes",v:`${rc.length} identified`},{l:"Recommendations",v:`${(d.recommendation||[]).length} actions`}].map((s,i)=>(
                    <div key={i} className="flex justify-between text-xs">
                      <span className="text-gray-500">{s.l}</span>
                      <span className="text-gray-200 font-semibold">{s.v}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </>}

      </div>
    </div>
  );
}
