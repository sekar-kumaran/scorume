import React, { useState, useEffect } from 'react';
import { findCandidatesForRole, reverseMatchCandidate } from '../api/client';

export default function RoleMatcherFinderView({ activeJd, onSelectCandidate }) {
  const [activeMode, setActiveMode] = useState('match-role'); // 'match-role' | 'reverse-candidate'

  // Mode 1: Match Candidates to New Role Requisition
  const [roleTitle, setRoleTitle] = useState(activeJd?.title || 'Senior Software Engineer');
  const [department, setDepartment] = useState('Engineering & Platform (India)');
  const [minExp, setMinExp] = useState(activeJd?.min_experience_years ? String(activeJd.min_experience_years) : '3.0');
  const [targetLevel, setTargetLevel] = useState('Staff / Lead');
  const [requiredSkills, setRequiredSkills] = useState(
    activeJd?.required_skills?.length > 0
      ? activeJd.required_skills
      : ['Python', 'SQL', 'Docker', 'FastAPI', 'PostgreSQL']
  );

  // Sync if activeJd updates
  useEffect(() => {
    if (activeJd) {
      if (activeJd.title) setRoleTitle(activeJd.title);
      if (activeJd.min_experience_years !== undefined) setMinExp(String(activeJd.min_experience_years));
      if (activeJd.required_skills?.length > 0) setRequiredSkills(activeJd.required_skills);
    }
  }, [activeJd]);
  const [newSkillInput, setNewSkillInput] = useState('');
  const [showAddSkill, setShowAddSkill] = useState(false);
  const [activePreset, setActivePreset] = useState('heavy'); // 'balanced' | 'heavy' | 'tenure'
  const [weights, setWeights] = useState({ skills: 0.6, semantic: 0.2, experience: 0.2 });
  const [isQuerying, setIsQuerying] = useState(false);
  const [discoveredCandidates, setDiscoveredCandidates] = useState([]);
  const [hasQueried, setHasQueried] = useState(false);
  const [filterPill, setFilterPill] = useState('all');

  // Mode 2: Reverse Candidate to Roles
  const [reverseResumeText, setReverseResumeText] = useState('');
  const [reverseMatches, setReverseMatches] = useState([]);
  const [isReverseMatching, setIsReverseMatching] = useState(false);

  const handleApplyPreset = (preset) => {
    setActivePreset(preset);
    if (preset === 'balanced') {
      setWeights({ skills: 0.4, semantic: 0.3, experience: 0.3 });
    } else if (preset === 'heavy') {
      setWeights({ skills: 0.6, semantic: 0.2, experience: 0.2 });
    } else if (preset === 'tenure') {
      setWeights({ skills: 0.3, semantic: 0.2, experience: 0.5 });
    }
  };

  const handleRemoveSkill = (skillToRemove) => {
    setRequiredSkills((prev) => prev.filter((s) => s !== skillToRemove));
  };

  const handleAddSkill = (e) => {
    e.preventDefault();
    if (newSkillInput && newSkillInput.trim()) {
      const trimmed = newSkillInput.trim();
      if (!requiredSkills.includes(trimmed)) {
        setRequiredSkills((prev) => [...prev, trimmed]);
      }
      setNewSkillInput('');
      setShowAddSkill(false);
    }
  };

  const handleRunGlobalMatch = async () => {
    setIsQuerying(true);
    setHasQueried(true);
    try {
      const results = await findCandidatesForRole({
        role_title: roleTitle,
        department,
        min_experience_years: parseFloat(minExp) || 5.0,
        required_skills: requiredSkills,
        weight_skills: weights.skills,
        weight_semantic: weights.semantic,
        weight_experience: weights.experience,
        include_all_pools: true,
      });
      setDiscoveredCandidates(results);
    } catch (err) {
      console.error('Global database match failed:', err);
      setDiscoveredCandidates([]);
    } finally {
      setIsQuerying(false);
    }
  };

  // Run initial match on mount so data is pre-populated
  useEffect(() => {
    handleRunGlobalMatch();
  }, []);

  const handleRunReverseMatch = async () => {
    if (!reverseResumeText.trim()) return;
    setIsReverseMatching(true);
    try {
      const results = await reverseMatchCandidate({
        raw_resume_text: reverseResumeText.trim(),
      });
      setReverseMatches(results);
    } catch (err) {
      console.error('Reverse role match failed:', err);
    } finally {
      setIsReverseMatching(false);
    }
  };

  const filteredDiscovered = discoveredCandidates.filter((c) => {
    if (filterPill === 'high' && c.score < 80) return false;
    if (filterPill === 'proximity' && c.score < 90) return false;
    return true;
  });

  return (
    <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-6 animate-fadeIn">
      {/* Top Action / Context Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-white/70 backdrop-blur-md p-6 rounded-2xl border border-slate-200/90 shadow-[0_4px_24px_-4px_rgba(0,0,0,0.06)]">
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2.5 flex-wrap">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200/70 text-xs font-semibold uppercase tracking-wider">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-pulse"></span>
              Scorume (evaluation engine) &amp; Candidate Finder
            </span>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/70 text-xs font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              Evaluation Matcher Ready
            </span>
          </div>
          <h1 className="text-2xl lg:text-3xl font-extrabold text-slate-900 tracking-tight">
            Scorume (evaluation engine) &amp; Cross-Drive Search
          </h1>
          <p className="text-sm text-slate-600 max-w-3xl leading-relaxed">
            Discover qualified candidates from past Indian hiring drives for open roles, or reverse-match candidate resumes against active job requisitions in Bengaluru, Mumbai, Hyderabad, and Pune.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 shrink-0">
          {/* Mode Switcher */}
          <div className="inline-flex p-1 rounded-xl bg-slate-100 border border-slate-200 shadow-inner" role="tablist">
            <button
              type="button"
              onClick={() => setActiveMode('match-role')}
              className={`px-4 py-2 rounded-lg text-xs md:text-sm font-bold transition-all duration-200 cursor-pointer btn-press ${
                activeMode === 'match-role'
                  ? 'text-white bg-primary shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Search Candidates by Role
            </button>
            <button
              type="button"
              onClick={() => setActiveMode('reverse-candidate')}
              className={`px-4 py-2 rounded-lg text-xs md:text-sm font-bold transition-all duration-200 cursor-pointer btn-press ${
                activeMode === 'reverse-candidate'
                  ? 'text-white bg-primary shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Reverse Match Resume to Jobs
            </button>
          </div>
        </div>
      </div>

      {activeMode === 'match-role' ? (
        <>
          {/* Requisition Definition & Heuristic Configuration Grid */}
          <div className="bg-white rounded-2xl p-6 lg:p-7 shadow-[0_4px_24px_-4px_rgba(0,0,0,0.06)] flex flex-col gap-6 border border-slate-200/90">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 flex-wrap gap-2">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                  <span className="material-symbols-outlined text-[20px]">tune</span>
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-900">
                    Role Requirements &amp; Matching Calibration
                  </h2>
                  <p className="text-xs text-slate-500">Configure position criteria and scoring weights for Indian recruitment</p>
                </div>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200/80 text-xs font-mono">
                <span className="text-slate-500 font-semibold uppercase">Job Requisition:</span>
                <span className="text-primary font-bold">REQ-BLR-2026-088</span>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left: Role Specs */}
              <div className="lg:col-span-6 flex flex-col gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-600">
                    Target Role Title
                  </label>
                  <input
                    type="text"
                    value={roleTitle}
                    onChange={(e) => setRoleTitle(e.target.value)}
                    className="w-full h-10 px-3.5 bg-slate-50 rounded-xl text-sm font-medium text-slate-900 border border-slate-200 focus:outline-none focus:bg-white focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all shadow-sm"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-600">
                      Department &amp; Hub
                    </label>
                    <select
                      value={department}
                      onChange={(e) => setDepartment(e.target.value)}
                      className="w-full h-10 px-2.5 bg-slate-50 rounded-xl text-xs font-medium text-slate-900 border border-slate-200 focus:outline-none focus:bg-white focus:border-primary shadow-sm"
                    >
                      <option>Core Platform &amp; AI (Bengaluru)</option>
                      <option>Distributed Infra (Hyderabad)</option>
                      <option>Data Engineering (Pune)</option>
                      <option>Full-Stack Application (Gurugram)</option>
                      <option>Fintech Engineering (Mumbai)</option>
                    </select>
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-600">
                      Min. Exp (YoE)
                    </label>
                    <input
                      type="text"
                      value={minExp}
                      onChange={(e) => setMinExp(e.target.value)}
                      className="w-full h-10 px-3 bg-slate-50 rounded-xl font-mono text-sm font-bold text-slate-900 border border-slate-200 focus:outline-none focus:bg-white focus:border-primary shadow-sm"
                    />
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-600">
                      Target Level &amp; CTC
                    </label>
                    <input
                      type="text"
                      value={targetLevel}
                      onChange={(e) => setTargetLevel(e.target.value)}
                      className="w-full h-10 px-3 bg-slate-50 rounded-xl text-xs font-medium text-slate-900 border border-slate-200 focus:outline-none focus:bg-white focus:border-primary shadow-sm"
                    />
                  </div>
                </div>

                {/* Pool Source Meta */}
                <div className="p-3.5 rounded-xl bg-slate-50 flex flex-col gap-2 border border-slate-200/80">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-600 uppercase tracking-wider">
                      Candidate Database Scope
                    </span>
                    <span className="text-xs font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                      All Evaluated Resumes Active
                    </span>
                  </div>
                  <label className="flex items-center gap-2 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      defaultChecked
                      className="w-4 h-4 text-primary accent-primary rounded cursor-pointer"
                    />
                    <span className="text-xs text-slate-700">
                      Include candidates vetted in previous hiring campaigns across India
                    </span>
                  </label>
                </div>
              </div>

              {/* Right: Benchmark Parameters & Weights */}
              <div className="lg:col-span-6 flex flex-col gap-4">
                <div className="flex flex-col gap-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-600">
                      Mandatory Technical Skills (High Priority)
                    </label>
                    <button
                      type="button"
                      onClick={() => setShowAddSkill(true)}
                      className="text-xs font-bold text-primary hover:underline cursor-pointer flex items-center gap-1"
                    >
                      <span className="material-symbols-outlined text-[14px]">add_circle</span>
                      Add Skill
                    </button>
                  </div>

                  <div className="flex flex-wrap gap-1.5 p-3 bg-slate-50 rounded-xl min-h-[46px] items-center border border-slate-200/80 shadow-inner">
                    {requiredSkills.map((skill) => (
                      <span
                        key={skill}
                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white font-mono text-xs font-semibold text-slate-800 shadow-sm border border-slate-200"
                      >
                        {skill}
                        <button
                          type="button"
                          onClick={() => handleRemoveSkill(skill)}
                          className="text-slate-400 hover:text-rose-600 text-xs font-bold leading-none cursor-pointer"
                        >
                          ×
                        </button>
                      </span>
                    ))}

                    {showAddSkill && (
                      <form onSubmit={handleAddSkill} className="inline-flex items-center gap-1">
                        <input
                          type="text"
                          autoFocus
                          placeholder="Skill..."
                          value={newSkillInput}
                          onChange={(e) => setNewSkillInput(e.target.value)}
                          className="h-7 px-2 text-xs bg-white rounded-lg border border-primary text-slate-900 focus:outline-none shadow-sm"
                        />
                        <button
                          type="submit"
                          className="text-xs px-2.5 py-1 rounded-lg bg-primary text-white font-bold cursor-pointer"
                        >
                          Add
                        </button>
                      </form>
                    )}
                  </div>
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-600">
                    Scoring Model Presets
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    <button
                      type="button"
                      onClick={() => handleApplyPreset('balanced')}
                      className={`px-3 py-2 rounded-xl text-xs text-center font-bold transition-all cursor-pointer btn-press border ${
                        activePreset === 'balanced'
                          ? 'bg-primary text-white border-primary shadow-sm'
                          : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                      }`}
                    >
                      Balanced (40/30/30)
                    </button>
                    <button
                      type="button"
                      onClick={() => handleApplyPreset('heavy')}
                      className={`px-3 py-2 rounded-xl text-xs text-center font-bold transition-all cursor-pointer btn-press border ${
                        activePreset === 'heavy'
                          ? 'bg-primary text-white border-primary shadow-sm'
                          : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                      }`}
                    >
                      Tech Heavy (60/20/20)
                    </button>
                    <button
                      type="button"
                      onClick={() => handleApplyPreset('tenure')}
                      className={`px-3 py-2 rounded-xl text-xs text-center font-bold transition-all cursor-pointer btn-press border ${
                        activePreset === 'tenure'
                          ? 'bg-primary text-white border-primary shadow-sm'
                          : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                      }`}
                    >
                      Tenure Heavy (30/20/50)
                    </button>
                  </div>
                </div>

                <div className="pt-2 flex justify-end">
                  <button
                    type="button"
                    onClick={handleRunGlobalMatch}
                    disabled={isQuerying}
                    className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-primary text-white text-sm font-bold hover:bg-primary-container transition-all shadow-[0_4px_16px_rgba(26,115,232,0.3)] cursor-pointer disabled:opacity-60 btn-press"
                  >
                    {isQuerying ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        <span>Scanning Candidate Database...</span>
                      </>
                    ) : (
                      <>
                        <span className="material-symbols-outlined text-[20px]">manage_search</span>
                        <span>Search Candidates in Database</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Match Breakdown & Sub-Filter Bar */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center gap-2.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shrink-0 animate-pulse"></span>
              <span className="text-xs font-mono text-slate-600">
                Search completed in <strong className="text-slate-900 font-bold">180ms</strong> •{' '}
                <strong className="text-slate-900 font-bold">
                  {discoveredCandidates.length} Qualified Candidates Ranked
                </strong>{' '}
                across past hiring drives
              </span>
            </div>

            {/* Quick Filter Pills */}
            <div className="flex items-center gap-1.5 overflow-x-auto">
              <button
                type="button"
                onClick={() => setFilterPill('all')}
                className={`px-3 py-1 rounded-lg text-xs font-bold whitespace-nowrap transition-all cursor-pointer btn-press ${
                  filterPill === 'all'
                    ? 'bg-primary text-white shadow-sm'
                    : 'bg-slate-100 text-slate-600 hover:text-slate-900 hover:bg-slate-200'
                }`}
              >
                All Matches ({discoveredCandidates.length})
              </button>
              <button
                type="button"
                onClick={() => setFilterPill('high')}
                className={`px-3 py-1 rounded-lg text-xs font-bold whitespace-nowrap transition-all cursor-pointer btn-press ${
                  filterPill === 'high'
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'bg-slate-100 text-slate-600 hover:text-slate-900 hover:bg-slate-200'
                }`}
              >
                ⭐ High Match (≥80%)
              </button>
              <button
                type="button"
                onClick={() => setFilterPill('proximity')}
                className={`px-3 py-1 rounded-lg text-xs font-bold whitespace-nowrap transition-all cursor-pointer btn-press ${
                  filterPill === 'proximity'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'bg-slate-100 text-slate-600 hover:text-slate-900 hover:bg-slate-200'
                }`}
              >
                🎯 Top Skill Fit (&gt;90%)
              </button>
            </div>
          </div>

          {/* Discovered Candidates Table */}
          <div className="bg-white rounded-2xl shadow-[0_4px_24px_-4px_rgba(0,0,0,0.06)] overflow-hidden flex flex-col border border-slate-200/90">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse min-w-[980px]">
                <thead>
                  <tr className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[11px] font-bold border-b border-slate-200">
                    <th className="py-3 px-4 w-32">Rank &amp; Score</th>
                    <th className="py-3 px-4 min-w-[240px]">Candidate &amp; Past Drive</th>
                    <th className="py-3 px-4 w-36">Experience (YoE)</th>
                    <th className="py-3 px-4 min-w-[280px]">Skill Match Analysis</th>
                    <th className="py-3 px-4 min-w-[300px]">Recruiter Rationale</th>
                    <th className="py-3 px-4 w-36 text-right">Candidate Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
                  {filteredDiscovered.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-14 text-center text-slate-400">
                        <div className="flex flex-col items-center gap-2">
                          <span className="material-symbols-outlined text-[36px] text-slate-300">person_search</span>
                          <span className="text-sm font-semibold">No candidate profiles found in the database.</span>
                          <span className="text-xs text-slate-500">Run a candidate evaluation from the Job &amp; Resumes tab first.</span>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    filteredDiscovered.map((cand) => (
                      <tr
                        key={cand.id}
                        className="hover:bg-slate-50/80 transition-colors card-hover"
                      >
                        <td className="py-3.5 px-4 align-top">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs font-bold text-slate-400">
                              #{String(cand.rank).padStart(2, '0')}
                            </span>
                            <span
                              className={`inline-flex items-center px-2 py-0.5 rounded-lg font-mono text-xs font-bold ${
                                cand.score >= 80
                                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                                  : cand.score >= 65
                                  ? 'bg-amber-100 text-amber-800 border border-amber-200'
                                  : 'bg-rose-100 text-rose-800 border border-rose-200'
                              }`}
                            >
                              {Math.round(cand.score)}%
                            </span>
                          </div>
                        </td>

                        <td className="py-3.5 px-4 align-top">
                          <div className="flex flex-col">
                            <span
                              onClick={() => onSelectCandidate && onSelectCandidate(cand)}
                              className="text-sm font-bold text-slate-900 hover:text-primary cursor-pointer transition-colors"
                            >
                              {cand.candidate_name}
                            </span>
                            <span className="font-mono text-[11px] text-slate-500">
                              {cand.email}
                            </span>
                            <div className="flex items-center gap-1 mt-1 text-[11px] text-slate-500">
                              <span className="material-symbols-outlined text-[13px] text-slate-400">history_edu</span>
                              <span>Source: {cand.sourced_campaign}</span>
                            </div>
                          </div>
                        </td>

                        <td className="py-3.5 px-4 align-top">
                          <div className="flex flex-col">
                            <span className="font-mono text-xs font-bold text-slate-900">
                              {cand.experience_years.toFixed(1)} yrs
                            </span>
                            <span className="font-mono text-[11px] text-emerald-600 font-semibold">
                              {cand.verified_years_diff}
                            </span>
                          </div>
                        </td>

                        <td className="py-3.5 px-4 align-top">
                          <div className="flex flex-wrap gap-1 max-w-[260px]">
                            {cand.matched_skills?.map((s) => (
                              <span
                                key={s}
                                className="px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 font-mono text-[11px] font-semibold border border-emerald-200/60"
                              >
                                {s}
                              </span>
                            ))}
                            {cand.missing_skills?.map((s) => (
                              <span
                                key={s}
                                className="px-1.5 py-0.5 rounded bg-rose-50 text-rose-600 font-mono text-[11px] font-medium border border-rose-200/60"
                              >
                                {s}
                              </span>
                            ))}
                          </div>
                        </td>

                        <td className="py-3.5 px-4 align-top">
                          <p className="text-xs text-slate-600 leading-relaxed">
                            {cand.rationale}
                          </p>
                        </td>

                        <td className="py-3.5 px-4 align-top text-right whitespace-nowrap">
                          <button
                            type="button"
                            onClick={() => onSelectCandidate && onSelectCandidate(cand)}
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-primary text-white text-xs font-bold hover:bg-primary-container transition-all shadow-sm cursor-pointer btn-press"
                          >
                            <span>Inspect</span>
                            <span className="material-symbols-outlined text-[14px]">
                              arrow_forward
                            </span>
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : (
        /* Mode 2: Reverse Candidate to Roles */
        <div className="bg-white rounded-2xl p-6 lg:p-7 shadow-[0_4px_24px_-4px_rgba(0,0,0,0.06)] flex flex-col gap-6 border border-slate-200/90">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 flex-wrap gap-2">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600">
                <span className="material-symbols-outlined text-[20px]">
                  switch_access_shortcut
                </span>
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-900">
                  Reverse Resume Matcher (Match Resume to Active Jobs)
                </h2>
                <p className="text-xs text-slate-500">Compare any candidate against all open tech roles across India</p>
              </div>
            </div>
            <span className="font-mono text-xs font-semibold px-2.5 py-1 rounded-lg bg-slate-100 text-slate-600 border border-slate-200">
              Multi-Role Compatibility Assessment
            </span>
          </div>

          <div className="flex flex-col gap-3">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-600">
              Paste Candidate Resume Text or Profile Summary
            </label>
            <textarea
              rows={6}
              placeholder="Paste candidate resume text or CV summary here to evaluate compatibility across all active Indian tech job openings..."
              value={reverseResumeText}
              onChange={(e) => setReverseResumeText(e.target.value)}
              className="w-full bg-slate-50 p-3.5 font-mono text-xs rounded-xl border border-slate-200 focus:outline-none focus:bg-white focus:border-primary focus:ring-2 focus:ring-primary/20 text-slate-900 leading-relaxed shadow-inner"
            />
            <div className="flex justify-end">
              <button
                type="button"
                onClick={handleRunReverseMatch}
                disabled={isReverseMatching || !reverseResumeText.trim()}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary text-white text-xs md:text-sm font-bold shadow-[0_4px_16px_rgba(26,115,232,0.3)] hover:bg-primary-container transition-all cursor-pointer disabled:opacity-50 btn-press"
              >
                {isReverseMatching ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Matching Open Roles...</span>
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-[18px]">radar</span>
                    <span>Match Against Active Job Openings</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {reverseMatches.length > 0 && (
            <div className="overflow-x-auto rounded-xl border border-slate-200">
              <table className="w-full text-left border-collapse min-w-[700px]">
                <thead>
                  <tr className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[11px] font-bold border-b border-slate-200">
                    <th className="py-3 px-4">Role &amp; Location</th>
                    <th className="py-3 px-4">Department</th>
                    <th className="py-3 px-4">Match Fit</th>
                    <th className="py-3 px-4">Skill Overlap</th>
                    <th className="py-3 px-4">Req Years</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
                  {reverseMatches.map((m, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3.5 px-4 font-bold text-slate-900">{m.role_title}</td>
                      <td className="py-3.5 px-4 text-slate-600">{m.department}</td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-lg font-mono text-xs font-bold ${
                            m.fit_tier === 'Strong'
                              ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                              : m.fit_tier === 'Moderate'
                              ? 'bg-amber-100 text-amber-800 border border-amber-200'
                              : 'bg-rose-100 text-rose-800 border border-rose-200'
                          }`}
                        >
                          {Math.round(m.match_score)}% • {m.fit_tier}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-slate-800">
                        {m.matched_skills?.slice(0, 4).join(', ') || 'None'}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-slate-800">
                        {m.min_experience_years.toFixed(0)}+ yrs
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
