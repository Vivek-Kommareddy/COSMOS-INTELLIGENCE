"use client";

import dynamic from "next/dynamic";
import type { PlotParams } from "react-plotly.js";

const Plot = dynamic(() => import("react-plotly.js") as any, {
  ssr: false,
  loading: () => (
    <div className="w-full flex items-center justify-center text-gray-600 font-mono text-xs" style={{ height: "inherit", minHeight: "100px" }}>
      Loading chart...
    </div>
  ),
}) as React.ComponentType<any>;

export default Plot;
