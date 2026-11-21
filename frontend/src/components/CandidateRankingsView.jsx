import React, { useState, useMemo } from 'react';
import { getExportCsvUrl } from '../api/client';

export default function CandidateRankingsView({
  activeJd,
  candidates = [],
  onSelectCandidate,
  onNavigateToSetup,
}) {
  // Scoring formula weights (default 50% / 30% / 20%)
  const [weights, setWeights] = useState({
    skills: 50,
    semantic: 30,
    experience: 20,
  });

  const [searchTerm, setSearchTerm] = useState('');
  const [tierFilter, setTierFilter] = useState('all'); // 'all' | 'top' | 'moderate' | 'low'

  const handleWeightChange = (key, val) => {
    const num = Math.max(5, Math.min(85, parseInt(val, 10) || 0));
    setWeights((prev) => ({ ...prev, [key]: num }));
  };

  const resetWeights = () => {
    setWeights({ skills: 50, semantic: 30, experience: 20 });
  };

  const reqYears = activeJd?.min_experience_years || 4.0;
  const reqSkillsCount = activeJd?.required_skills?.length || 12;
  const roleTitle = activeJd?.title || 'Senior Full-Stack AI Engineer';

  // Dynamic real-time rescoring and sorting based on weights
  const scoredCandidates = useMemo(() => {
    const totalWeight = (weights.skills + weights.semantic + weights.experience) || 100;
    const wSk = weights.skills / totalWeight;
    const wSem = weights.semantic / totalWeight;
    const wExp = weights.experience / totalWeight;

    return candidates.map((cand) => {
      const sk = cand.skill_score ?? 80;
      const sem = cand.semantic_score ?? 75;
      const exp = cand.experience_score ?? 85;
      const composite = Math.round((wSk * sk + wSem * sem + wExp * exp) * 10) / 10;

      return {
        ...cand,
        recomputedScore: composite,
      };
    });
  }, [candidates, weights]);

  // Sort descending by recomputed score
  const sortedCandidates = useMemo(() => {
    const sorted = [...scoredCandidates].sort(
      (a, b) => (b.recomputedScore ?? b.overall_score) - (a.recomputedScore ?? a.overall_score)
    );

    return sorted.map((cand, idx) => ({
      ...cand,
      dynamicRank: idx + 1,
    }));
  }, [scoredCandidates]);

  // Filter by search and match tier
  const filteredCandidates = useMemo(() => {
    return sortedCandidates.filter((cand) => {
      const score = cand.recomputedScore ?? cand.overall_score ?? 0;
      if (tierFilter === 'top' && score < 80) return false;
      if (tierFilter === 'moderate' && (score < 65 || score >= 80)) return false;
      if (tierFilter === 'low' && score >= 65) return false;

      if (searchTerm.trim()) {
        const term = searchTerm.toLowerCase();
        const nameMatch = cand.candidate_name?.toLowerCase().includes(term);
        const emailMatch = cand.email?.toLowerCase().includes(term);
        const skillMatch = cand.matched_skills?.some((s) => s.toLowerCase().includes(term));
        return nameMatch || emailMatch || skillMatch;
      }
      return true;
    });
  }, [sortedCandidates, searchTerm, tierFilter]);

  const handleExportCsv = () => {
    if (activeJd?.id) {
      window.open(getExportCsvUrl(activeJd.id), '_blank');
    }
  };

  return (
    <div className="max-w-[1400px] w-full mx-auto py-8 px-6 flex flex-col gap-6 animate-fadeIn">
      {/* Top Context Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-700">
            <span>RECRUITMENT LEADERBOARD</span>
            <span className="text-slate-300">/</span>
            <span>CANDIDATE RANKING</span>
          </div>
          <div className="flex flex-wrap items-center gap-3 mt-1">
            <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
              {roleTitle}
            </h1>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-mono text-xs font-bold">
              {candidates.length} Candidates Screened
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-2 mt-1.5 text-xs text-slate-600">
            <span className="font-semibold text-slate-800">
              Req: {reqYears.toFixed(0)}+ Years YoE
            </span>
            <span className="text-slate-300">•</span>
            <span>{reqSkillsCount} Core Technical Skills</span>
            <span className="text-slate-300">•</span>
            <span className="text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              Deterministic Semantic Evaluation Active
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3 self-start sm:self-auto shrink-0">
          <button
            type="button"
            onClick={onNavigateToSetup}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white text-slate-700 font-semibold text-xs border border-slate-200 shadow-sm hover:bg-slate-50 hover:shadow transition-all cursor-pointer btn-press"
          >
            <span className="material-symbols-outlined text-[16px] text-slate-400">arrow_back</span>
            <span>Job Setup / Upload More</span>
          </button>
          <button
            type="button"
            onClick={handleExportCsv}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-md hover:shadow-lg hover:shadow-blue-500/20 transition-all cursor-pointer btn-press"
          >
            <span className="material-symbols-outlined text-[16px]">download</span>
            <span>Download Excel / CSV</span>
          </button>
        </div>
      </div>

      {/* Weight Calibration Strip */}
      <div className="bg-white rounded-2xl p-5 px-6 flex flex-col lg:flex-row lg:items-center justify-between gap-5 border border-slate-200/90 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.06)] hover:shadow-[0_8px_30px_-6px_rgba(0,0,0,0.08)] transition-all">
        <div className="flex items-center gap-3 shrink-0">
          <div className="w-9 h-9 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center border border-indigo-100 shadow-2xs">
            <span className="material-symbols-outlined text-[20px]">tune</span>
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-900 block">
              Scoring Weightage Calibration (%)
            </span>
            <span className="text-[11px] text-slate-500">
              Recalculates candidate ranking instantly in real-time
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 flex-1 max-w-4xl lg:px-6">
          {/* Slider 1: Skills */}
          <div className="flex flex-col gap-1.5 bg-slate-50/70 p-3 rounded-xl border border-slate-200/60 shadow-2xs">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-700 font-semibold">
                Technical Skills Match
              </span>
              <span className="font-mono text-xs font-extrabold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                {weights.skills}%
              </span>
            </div>
            <input
              type="range"
              min="10"
              max="80"
              value={weights.skills}
              onChange={(e) => handleWeightChange('skills', e.target.value)}
              className="weight-slider w-full cursor-pointer accent-blue-600 mt-1"
            />
          </div>

          {/* Slider 2: Semantic */}
          <div className="flex flex-col gap-1.5 bg-slate-50/70 p-3 rounded-xl border border-slate-200/60 shadow-2xs">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-700 font-semibold">
                Project &amp; Role Relevance
              </span>
              <span className="font-mono text-xs font-extrabold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                {weights.semantic}%
              </span>
            </div>
            <input
              type="range"
              min="10"
              max="80"
              value={weights.semantic}
              onChange={(e) => handleWeightChange('semantic', e.target.value)}
              className="weight-slider w-full cursor-pointer accent-indigo-600 mt-1"
            />
          </div>

          {/* Slider 3: Experience */}
          <div className="flex flex-col gap-1.5 bg-slate-50/70 p-3 rounded-xl border border-slate-200/60 shadow-2xs">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-700 font-semibold">
                Tenure / YoE Match
              </span>
              <span className="font-mono text-xs font-extrabold text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                {weights.experience}%
              </span>
            </div>
            <input
              type="range"
              min="10"
              max="80"
              value={weights.experience}
              onChange={(e) => handleWeightChange('experience', e.target.value)}
              className="weight-slider w-full cursor-pointer accent-teal-600 mt-1"
            />
          </div>
        </div>

        <div className="shrink-0 flex items-center justify-end">
          <button
            type="button"
            onClick={resetWeights}
            className="text-xs font-semibold text-slate-500 hover:text-blue-700 transition-colors cursor-pointer flex items-center gap-1"
          >
            <span className="material-symbols-outlined text-[14px]">restart_alt</span>
            <span>Reset Defaults</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white p-3 rounded-2xl border border-slate-200/80 shadow-xs">
        <div className="flex items-center gap-2 overflow-x-auto">
          <button
            type="button"
            onClick={() => setTierFilter('all')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer btn-press ${
              tierFilter === 'all'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:text-slate-900 hover:bg-slate-200'
            }`}
          >
            All Candidates ({sortedCandidates.length})
          </button>
          <button
            type="button"
            onClick={() => setTierFilter('top')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer btn-press ${
              tierFilter === 'top'
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'bg-emerald-50 text-emerald-800 hover:bg-emerald-100 border border-emerald-200/60'
            }`}
          >
            ⭐ Top Tier (≥80%)
          </button>
          <button
            type="button"
            onClick={() => setTierFilter('moderate')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer btn-press ${
              tierFilter === 'moderate'
                ? 'bg-amber-600 text-white shadow-xs'
                : 'bg-amber-50 text-amber-900 hover:bg-amber-100 border border-amber-200/60'
            }`}
          >
            👍 Moderate (65–79%)
          </button>
          <button
            type="button"
            onClick={() => setTierFilter('low')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer btn-press ${
              tierFilter === 'low'
                ? 'bg-red-600 text-white shadow-xs'
                : 'bg-red-50 text-red-800 hover:bg-red-100 border border-red-200/60'
            }`}
          >
            ⚠️ Low Match (&lt;65%)
          </button>
        </div>

        <div className="relative w-full sm:w-72">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[18px] text-slate-400">
            search
          </span>
          <input
            type="text"
            placeholder="Search candidate name, email, or skill..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full h-9 pl-9 pr-3 text-xs bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 text-slate-900 transition-all placeholder:text-slate-400"
          />
        </div>
      </div>

      {/* Main Candidate Ranking Table Card */}
      <div className="bg-white rounded-2xl shadow-[0_4px_20px_-4px_rgba(0,0,0,0.06)] overflow-hidden flex flex-col border border-slate-200/90">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[1080px]">
            {/* Table Header */}
            <thead>
              <tr className="bg-slate-50 text-slate-600 text-[11px] uppercase tracking-wider font-bold border-b border-slate-200">
                <th className="py-3.5 px-4 w-[70px]" scope="col">
                  Rank
                </th>
                <th className="py-3.5 px-4 w-[250px]" scope="col">
                  Candidate
                </th>
                <th className="py-3.5 px-4 w-[160px]" scope="col">
                  Experience (YoE)
                </th>
                <th className="py-3.5 px-4 w-[150px]" scope="col">
                  Match Score
                </th>
                <th className="py-3.5 px-4 w-[360px]" scope="col">
                  Matched Skills
                </th>
                <th className="py-3.5 px-4 w-[190px]" scope="col">
                  Skill Gaps
                </th>
                <th className="py-3.5 px-4 w-[120px] text-right" scope="col">
                  Action
                </th>
              </tr>
            </thead>

            {/* Table Body */}
            <tbody className="divide-y divide-slate-100 text-xs">
              {filteredCandidates.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-14 text-center text-slate-500">
                    No candidates match the selected filter criteria.
                  </td>
                </tr>
              ) : (
                filteredCandidates.map((cand) => {
                  const score = cand.recomputedScore ?? cand.overall_score ?? 0;
                  const expYrs = cand.experience_years ?? 0;
                  const diffYrs = expYrs - reqYears;
                  const isTop = score >= 80;
                  const isModerate = score >= 65 && score < 80;

                  return (
                    <tr
                      key={cand.id}
                      className="hover:bg-blue-50/30 transition-all duration-150 group"
                    >
                      {/* Rank */}
                      <td className="py-4 px-4 font-mono font-bold text-sm">
                        <span
                          className={`inline-flex items-center justify-center w-7 h-7 rounded-lg ${
                            cand.dynamicRank === 1
                              ? 'bg-amber-100 text-amber-800 font-extrabold border border-amber-300'
                              : cand.dynamicRank === 2
                              ? 'bg-slate-200 text-slate-800 font-bold'
                              : cand.dynamicRank === 3
                              ? 'bg-amber-50 text-amber-900 border border-amber-200'
                              : 'text-slate-500 bg-slate-100'
                          }`}
                        >
                          #{String(cand.dynamicRank).padStart(2, '0')}
                        </span>
                      </td>

                      {/* Candidate Name & Email */}
                      <td className="py-4 px-4">
                        <div className="flex flex-col">
                          <span className="text-sm font-bold text-slate-900 leading-snug group-hover:text-blue-700 transition-colors">
                            {cand.candidate_name || 'Candidate'}
                          </span>
                          <span className="font-mono text-[11px] text-slate-500 mt-0.5">
                            {cand.email || 'not_provided@local'}
                          </span>
                        </div>
                      </td>

                      {/* Experience */}
                      <td className="py-4 px-4">
                        <div className="flex flex-col gap-1">
                          <span className="font-mono font-bold text-slate-900 text-xs">
                            {expYrs.toFixed(1)} yrs YoE
                          </span>
                          <span
                            className={`inline-flex items-center w-fit px-2 py-0.5 rounded-full font-mono text-[10px] font-bold ${
                              diffYrs >= 0
                                ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                                : 'bg-slate-100 text-slate-600'
                            }`}
                          >
                            {diffYrs >= 0
                              ? `+${diffYrs.toFixed(1)} yrs vs req`
                              : `${diffYrs.toFixed(1)} yrs vs req`}
                          </span>
                        </div>
                      </td>

                      {/* Match Score */}
                      <td className="py-4 px-4">
                        <div className="flex flex-col gap-1.5 w-28">
                          <div
                            className={`inline-flex items-center justify-between px-2.5 py-0.5 rounded-lg border font-mono ${
                              isTop
                                ? 'bg-emerald-50 text-emerald-800 border-emerald-300 font-extrabold'
                                : isModerate
                                ? 'bg-amber-50 text-amber-900 border-amber-200 font-bold'
                                : 'bg-red-50 text-red-800 border-red-200 font-semibold'
                            }`}
                          >
                            <span className="text-sm">
                              {Math.round(score)}%
                            </span>
                            <span className="text-[10px] uppercase font-bold tracking-wider">
                              {isTop ? 'TOP' : isModerate ? 'FIT' : 'LOW'}
                            </span>
                          </div>
                          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all duration-500 ${
                                isTop
                                  ? 'bg-emerald-500'
                                  : isModerate
                                  ? 'bg-amber-500'
                                  : 'bg-red-500'
                              }`}
                              style={{ width: `${Math.min(100, Math.max(5, score))}%` }}
                            ></div>
                          </div>
                        </div>
                      </td>

                      {/* Matched Skills */}
                      <td className="py-4 px-4">
                        <div className="flex flex-wrap items-center gap-1.5 max-w-[360px]">
                          {(cand.matched_skills || []).slice(0, 5).map((skill) => (
                            <span
                              key={skill}
                              className="px-2.5 py-0.5 rounded-md bg-blue-50 text-blue-800 font-medium text-[11px] border border-blue-100"
                            >
                              {skill}
                            </span>
                          ))}
                          {(cand.matched_skills?.length || 0) > 5 && (
                            <span className="font-mono text-[10px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded font-bold">
                              +{cand.matched_skills.length - 5} more
                            </span>
                          )}
                          {(!cand.matched_skills || cand.matched_skills.length === 0) && (
                            <span className="text-slate-400 text-xs italic">
                              No exact matches
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Skill Gaps */}
                      <td className="py-4 px-4">
                        <div className="flex flex-wrap gap-1">
                          {(cand.missing_skills || []).slice(0, 2).map((skill) => (
                            <span
                              key={skill}
                              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-amber-50 text-amber-800 border border-amber-200 text-[11px] font-medium"
                            >
                              <span className="material-symbols-outlined text-[12px] text-amber-600">
                                warning
                              </span>
                              {skill}
                            </span>
                          ))}
                          {(!cand.missing_skills || cand.missing_skills.length === 0) && (
                            <span className="text-emerald-700 font-semibold text-xs flex items-center gap-1">
                              <span className="material-symbols-outlined text-[14px]">check</span>
                              All Core Skills Met
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Action */}
                      <td className="py-4 px-4 text-right">
                        <button
                          type="button"
                          onClick={() => onSelectCandidate(cand)}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-blue-600 text-white font-medium text-xs shadow-sm hover:shadow transition-all cursor-pointer btn-press"
                        >
                          <span>Inspect</span>
                          <span className="material-symbols-outlined text-[14px]">
                            arrow_forward
                          </span>
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
