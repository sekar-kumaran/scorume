import React from 'react';
import logoImg from '../assets/logo.png';

export default function Navbar({
  activeTab = 'benchmark-config',
  setActiveTab,
  hasEvaluations = false,
  healthInfo = null,
  onOpenHelp,
}) {
  const isHealthy = healthInfo?.status === 'healthy';

  const navItems = [
    {
      id: 'benchmark-config',
      label: '1. Job & Resumes',
      icon: 'description',
    },
    {
      id: 'candidate-rankings',
      label: '2. Candidate Rankings',
      icon: 'leaderboard',
      hasBadge: hasEvaluations,
    },
    {
      id: 'role-matcher-finder',
      label: '3. Scorume (evaluation engine)',
      icon: 'person_search',
    },
    {
      id: 'evaluation-history',
      label: '4. Hiring History',
      icon: 'history',
    },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 glass-nav shadow-xs">
      <div className="max-w-[1400px] mx-auto h-full px-6 flex items-center justify-between gap-4">
        {/* Brand / Logo */}
        <div className="flex items-center gap-3 shrink-0">
          <div
            onClick={() => setActiveTab('benchmark-config')}
            className="flex items-center gap-2.5 cursor-pointer select-none group"
          >
            <div className="relative w-10 h-10 rounded-full flex items-center justify-center shrink-0 group-hover:scale-105 transition-all duration-200">
              <img
                src={logoImg || '/logo.png'}
                alt="Scorume Logo"
                className="w-10 h-10 rounded-full object-cover shadow-md shadow-emerald-950/20 ring-2 ring-emerald-500/30 group-hover:ring-emerald-500/60 transition-all duration-200 bg-slate-900"
                onError={(e) => {
                  e.currentTarget.onerror = null;
                  e.currentTarget.src = '/logo.png';
                }}
              />
              <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-white"></span>
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-1.5 leading-none">
                <span className="font-headline-sm text-base text-slate-900 font-bold tracking-tight">
                  Scorume
                </span>
                <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200/60 font-mono">
                  evaluation engine
                </span>
              </div>
              <span className="text-[11px] text-slate-500 font-medium tracking-tight mt-0.5 hidden sm:inline">
                Technical Candidate Evaluation &amp; Ranking Engine
              </span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1.5 bg-slate-100/80 p-1 rounded-xl border border-slate-200/60 overflow-x-auto shadow-inner">
          {navItems.map((item, idx) => {
            const isActive = activeTab === item.id;
            return (
              <React.Fragment key={item.id}>
                {idx === 2 && (
                  <div className="h-4 w-px bg-slate-300 mx-1 hidden md:block"></div>
                )}
                <button
                  type="button"
                  onClick={() => setActiveTab(item.id)}
                  className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs md:text-sm font-medium transition-all duration-200 whitespace-nowrap cursor-pointer btn-press ${
                    isActive
                      ? 'bg-white text-blue-700 shadow-sm font-semibold border border-blue-100'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
                  }`}
                >
                  <span
                    className={`material-symbols-outlined text-[16px] ${
                      isActive ? 'text-blue-600' : 'text-slate-400'
                    }`}
                  >
                    {item.icon}
                  </span>
                  <span>{item.label}</span>
                  {item.hasBadge && (
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                  )}
                </button>
              </React.Fragment>
            );
          })}
        </nav>

        {/* Right Status Indicators & User Profile */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="hidden lg:flex items-center gap-3">
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200/60 font-mono text-[11px] text-emerald-800 shadow-2xs">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="font-semibold">Bengaluru Hub</span>
              <span className="text-emerald-400">•</span>
              <span>{isHealthy ? 'Local AI Ready' : 'Connecting'}</span>
            </div>

            <button
              type="button"
              onClick={onOpenHelp}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px] text-slate-400">help</span>
              <span>Docs</span>
            </button>
          </div>

          {/* User Profile Pill */}
          <div
            className="flex items-center gap-2 pl-2 border-l border-slate-200"
            title="Logged in as Indian Technical Recruiter / HR Admin"
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-slate-800 to-slate-900 text-white flex items-center justify-center font-semibold text-xs shadow-xs hover:scale-105 transition-transform cursor-pointer">
              HR
            </div>
            <div className="hidden xl:flex flex-col text-left">
              <span className="text-xs font-semibold text-slate-800 leading-tight">HR Recruiter</span>
              <span className="text-[10px] text-slate-500 leading-tight">Talent Acquisition</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
