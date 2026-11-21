import React from 'react';

export default function Footer() {
  return (
    <footer className="w-full bg-white border-t border-slate-200/80 mt-auto py-4">
      <div className="max-w-[1400px] mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-3 font-mono text-[11px] text-slate-500">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-700">SCORUME</span>
          <span>•</span>
          <span className="text-blue-700 font-semibold">EVALUATION ENGINE</span>
          <span>•</span>
          <span className="text-slate-400">100% PRIVATE LOCAL PROCESSING (DPDP ACT READY)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>REGION: ASIA-SOUTH (MUMBAI &amp; BENGALURU) • LATENCY &lt; 35MS</span>
        </div>
      </div>
    </footer>
  );
}
