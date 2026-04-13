export function generateDemoData() {
  const days = 365;
  const dates = [], rev = [], orders = [], aov = [];
  const base = new Date('2025-01-01');
  
  const seed = (n: number) => {
    let x = Math.sin(n * 9301 + 49297) * 233280;
    return x - Math.floor(x);
  };
  
  for (let i = 0; i < days; i++) {
    const d = new Date(base); 
    d.setDate(d.getDate() + i);
    dates.push(d.toISOString().split('T')[0]);
    
    const dow = d.getDay();
    const weekSeason = dow === 0 || dow === 6 ? 0.75 : 1.0;
    const trend = 1 + (i / days) * 0.15;
    const noise = 0.85 + seed(i) * 0.3;
    let mult = weekSeason * trend * noise;
    
    // Inject anomaly: days 320-334
    if (i >= 320 && i <= 334) mult *= 0.55;
    // Inject boost: days 200-214
    if (i >= 200 && i <= 214) mult *= 1.35;
    
    const r = Math.round(18000 * mult * 100) / 100;
    const o = Math.round(120 * mult + seed(i+1000) * 20);
    rev.push(r); 
    orders.push(o); 
    aov.push(+(r/o).toFixed(2));
  }
  
  // Predict Future
  const lastDate = new Date(dates[dates.length - 1]);
  const fDates = [], fVals = [], fLow = [], fHigh = [];
  const lastRev = rev.slice(-14).reduce((a,b)=>a+b,0)/14;
  
  for (let i = 1; i <= 14; i++) {
    const fd = new Date(lastDate); 
    fd.setDate(fd.getDate() + i);
    fDates.push(fd.toISOString().split('T')[0]);
    
    const v = lastRev * (1 - 0.008 * i + seed(i+500) * 0.04);
    fVals.push(+v.toFixed(2));
    fLow.push(+(v * 0.87).toFixed(2));
    fHigh.push(+(v * 1.13).toFixed(2));
  }
  
  const recentRevAvg = rev.slice(-14).reduce((a,b)=>a+b,0)/14;
  const priorRevAvg = rev.slice(-28,-14).reduce((a,b)=>a+b,0)/14;
  const changePct = +((recentRevAvg - priorRevAvg) / priorRevAvg * 100).toFixed(1);
  const recentOrdAvg = orders.slice(-14).reduce((a,b)=>a+b,0)/14;
  const priorOrdAvg = orders.slice(-28,-14).reduce((a,b)=>a+b,0)/14;
  const recentAovAvg = aov.slice(-14).reduce((a,b)=>a+b,0)/14;
  const priorAovAvg = aov.slice(-28,-14).reduce((a,b)=>a+b,0)/14;
  
  return {
    dates, 
    revenue: rev, 
    orders, 
    aov,
    severity: "CRITICAL",
    anomaly_detected: true,
    change_pct: changePct,
    change: changePct.toFixed(1) + "%",
    forecast_dates: fDates,
    forecast_values: fVals,
    forecast_confidence_lower: fLow,
    forecast_confidence_upper: fHigh,
    prediction: "Revenue projected to decline an additional 10-14% if no intervention taken in the next 14 days.",
    kpis: {
      revenue: { label: "Total Revenue", val: "$" + (recentRevAvg * 14 / 1000).toFixed(1) + "K", raw: recentRevAvg * 14, prior: priorRevAvg * 14, chg: changePct },
      orders: { label: "Total Orders", val: Math.round(recentOrdAvg * 14).toLocaleString(), raw: recentOrdAvg * 14, prior: priorOrdAvg * 14, chg: +((recentOrdAvg - priorOrdAvg)/priorOrdAvg*100).toFixed(1) },
      aov: { label: "Avg Order Value", val: "$" + recentAovAvg.toFixed(2), raw: recentAovAvg, prior: priorAovAvg, chg: +((recentAovAvg - priorAovAvg)/priorAovAvg*100).toFixed(1) },
      cvr: { label: "Conversion Rate", val: "3.42%", raw: 3.42, prior: 3.89, chg: -12.1 },
      health: { label: "Health Score", val: "34/100", raw: 34, prior: 78, chg: -56.4 }
    },
    root_cause: [
      { driver: "Campaign_A Paused", dimension: "campaign", group_value: "Campaign_A", contribution_pct: -62.1, delta: -11218 },
      { driver: "Electronics Stockout — West", dimension: "category/region", group_value: "Electronics/West", contribution_pct: -21.3, delta: -3854 },
      { driver: "Web Channel Friction", dimension: "channel", group_value: "Web", contribution_pct: -13.5, delta: -2443 },
      { driver: "Discount Band Reduction", dimension: "discount_band", group_value: "high→none", contribution_pct: -8.7, delta: -1574 },
      { driver: "Holiday Effect Faded", dimension: "holiday_flag", group_value: "0", contribution_pct: -4.2, delta: -760 }
    ],
    recommendation: [
      { action: "Reactivate Campaign_A immediately — increase budget by 25-30% to recover lost reach. Launch A/B creative refresh within 48 hours targeting electronics repeat buyers.", priority: "HIGH", expected_impact: "22–34% revenue recovery within 7 days", timeline: "Immediate (24–48 hours)", owner: "Growth & Performance Marketing", confidence: 0.88 },
      { action: "Emergency inventory replenishment for West region electronics. Activate substitute SKUs and place priority reorder with suppliers. Enable low-stock alerts.", priority: "HIGH", expected_impact: "12–18% revenue recovery within 10 days", timeline: "Immediate (48–72 hours)", owner: "Supply Chain & Operations", confidence: 0.84 },
      { action: "Run Web funnel audit — check payment success rates, load times, and checkout abandonment. A/B test checkout UX improvements targeting mobile drop-off.", priority: "MEDIUM", expected_impact: "8–12% conversion rate improvement", timeline: "Short-term (3–5 days)", owner: "Product & Engineering", confidence: 0.76 },
      { action: "Reintroduce high discount band for electronics category targeting lapsed customers (90+ days). Personalized offers via email and push notification.", priority: "MEDIUM", expected_impact: "6–10% repeat purchase rate improvement", timeline: "Short-term (5–7 days)", owner: "CRM & Retention Marketing", confidence: 0.72 },
      { action: "Launch win-back email sequence for inactive electronics buyers. 3-touch sequence with escalating offers (10% → 15% → 20% off).", priority: "LOW", expected_impact: "4–7% customer reactivation improvement", timeline: "Ongoing (7–14 days)", owner: "Email Marketing", confidence: 0.68 }
    ],
    explanation: "Revenue declined " + Math.abs(changePct).toFixed(1) + "% in the 14-day analysis window, driven by the simultaneous pause of Campaign_A (accounting for 62% of the shortfall) and a West-region electronics stockout that compounded channel-level friction on the web platform. Immediately reactivating Campaign_A at +25% budget and resolving the stockout issue are projected to recover 35–50% of lost revenue within 10 days, with full trajectory stabilization expected within 3 weeks.",
    confidence: 0.87,
    llm_powered: false
  };
}
