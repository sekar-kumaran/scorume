import React, { useState, useEffect } from 'react';
import {
  fetchEvaluationHistory,
  fetchRankedCandidates,
  deleteCampaignHistoryRun,
  purgeAllEvaluationHistory,
} from '../api/client';

export default function EvaluationHistoryView({
  onSelectCampaign,
  onNavigateToSetup,
}) {
  const [historyData, setHistoryData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  const loadHistory = async () => {
    setIsLoading(true);
    try {
      const data = await fetchEvaluationHistory();
      setHistoryData(data);
    } catch (err) {
      console.error('Failed to load evaluation history:', err);
      setHistoryData({
        summary: {
          total_evaluations: 0,
          resumes_screened: 0,
          avg_match_yield: 0,
          avg_batch_latency: '1.4s',
        },
        runs: [],
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteRun = async (e, run) => {
    e.stopPropagation();
    if (!window.confirm(`Delete recruitment drive '${run.title}' (#${run.run_id}) and all its evaluated candidate records?`)) {
      return;
    }
    try {
      await deleteCampaignHistoryRun(run.jd_id);
      await loadHistory();
    } catch (err) {
      console.error('Failed to delete campaign run:', err);
      alert('Could not delete run. Please try again.');
    }
  };

  const handlePurgeAll = async () => {
    if (!window.confirm('Are you sure you want to delete ALL historical drives and candidate evaluations? This will reset the database to a completely clean slate.')) {
      return;
    }
    try {
      await purgeAllEvaluationHistory();
      await loadHistory();
    } catch (err) {
      console.error('Failed to purge history:', err);
      alert('Could not purge history. Please try again.');
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const runs = historyData?.runs || [];
  const summary = historyData?.summary || {
    total_evaluations: runs.length,
    resumes_screened: 13,
    avg_match_yield: 25.0,
    avg_batch_latency: '1.2s',
  };

  // Filter runs by category and search
  const filteredRuns = runs.filter((run) => {
    if (selectedCategory === 'eng' && !run.department.toLowerCase().includes('infra') && !run.department.toLowerCase().includes('engine') && !run.department.toLowerCase().includes('platform')) return false;
    if (selectedCategory === 'prod' && !run.department.toLowerCase().includes('product') && !run.department.toLowerCase().includes('design')) return false;
    if (selectedCategory === 'data' && !run.department.toLowerCase().includes('data') && !run.department.toLowerCase().includes('ai')) return false;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = run.title?.toLowerCase().includes(q);
      const matchDept = run.department?.toLowerCase().includes(q);
      const matchId = run.run_id?.toLowerCase().includes(q);
      return matchTitle || matchDept || matchId;
    }
    return true;
  });

  const handleExportBatchLog = () => {
    const jsonStr = JSON.stringify(historyData, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scorume_evaluation_audit_log_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleViewCampaign = async (run) => {
    try {
      const evalResponse = await fetchRankedCandidates(run.jd_id);
      onSelectCampaign({
        jd: {
          id: evalResponse.jd_id,
          title: evalResponse.jd_title,
          required_skills: evalResponse.jd_required_skills,
          min_experience_years: evalResponse.jd_min_experience_years,
        },
        candidates: evalResponse.candidates || [],
      });
    } catch (err) {
      console.error('Error fetching campaign run:', err);
    }
  };

  return (
    <div className="w-full max-w-[1400px] mx-auto px-6 py-8 flex flex-col gap-6 animate-fadeIn">
      {/* Top Action / Context Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-700">
            <span>RECRUITMENT ARCHIVE</span>
            <span className="text-slate-300">/</span>
            <span>AUDIT RECORDS</span>
          </div>
          <div className="flex items-center gap-2.5 mt-1">
            <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
              Hiring Drives &amp; Evaluation History
            </h1>
            <span className="font-mono text-xs font-bold px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
              India Edition
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Access past candidate evaluations, benchmark criteria, and recruitment audit logs
          </p>
        </div>

        <div className="flex items-center gap-2.5 self-start lg:self-center shrink-0 flex-wrap">
          <button
            type="button"
            onClick={handleExportBatchLog}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white text-slate-700 font-semibold text-xs border border-slate-200 shadow-sm hover:bg-slate-50 hover:shadow transition-all cursor-pointer btn-press"
          >
            <span className="material-symbols-outlined text-[16px] text-slate-400">
              file_download
            </span>
            <span>Export Audit Log</span>
          </button>

          {runs.length > 0 && (
            <button
              type="button"
              onClick={handlePurgeAll}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-red-50 hover:bg-red-100 text-red-700 font-semibold text-xs border border-red-200 shadow-sm transition-all cursor-pointer btn-press"
              title="Delete all historical candidate drives and clear database"
            >
              <span className="material-symbols-outlined text-[16px] text-red-600">delete_sweep</span>
              <span>Clear History</span>
            </button>
          )}

          <button
            type="button"
            onClick={onNavigateToSetup}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-md hover:shadow-lg hover:shadow-blue-500/20 transition-all cursor-pointer btn-press"
          >
            <span className="material-symbols-outlined text-[16px]">add</span>
            <span>New Hiring Drive</span>
          </button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: Total Drives */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/90 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.06)] hover:shadow-[0_8px_30px_-6px_rgba(0,0,0,0.09)] transition-all card-hover flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] uppercase tracking-wider text-slate-500 font-bold">
              Total Hiring Drives
            </span>
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-100">
              <span className="material-symbols-outlined text-[18px]">folder_special</span>
            </div>
          </div>
          <div className="mt-3">
            <div className="flex items-baseline gap-1.5">
              <span className="font-mono text-2xl font-extrabold text-slate-900">
                {summary.total_evaluations}
              </span>
              <span className="text-xs text-slate-500 font-medium">Job Openings</span>
            </div>
            <div className="flex items-center gap-1.5 mt-1 font-mono text-[11px] text-emerald-700 font-semibold">
              <span className="material-symbols-outlined text-[13px]">check_circle</span>
              <span>Active in local storage</span>
            </div>
          </div>
        </div>

        {/* KPI 2: Resumes Screened */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/90 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.06)] hover:shadow-[0_8px_30px_-6px_rgba(0,0,0,0.09)] transition-all card-hover flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] uppercase tracking-wider text-slate-500 font-bold">
              Resumes Screened
            </span>
            <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center border border-indigo-100">
              <span className="material-symbols-outlined text-[18px]">description</span>
            </div>
          </div>
          <div className="mt-3">
            <div className="flex items-baseline gap-1.5">
              <span className="font-mono text-2xl font-extrabold text-slate-900">
                {summary.resumes_screened}
              </span>
              <span className="text-xs text-slate-500 font-medium">Candidates</span>
            </div>
            <div className="flex items-center gap-1.5 mt-1 font-mono text-[11px] text-emerald-700 font-semibold">
              <span className="material-symbols-outlined text-[13px]">verified</span>
              <span>Smart Engine Parsed</span>
            </div>
          </div>
        </div>

        {/* KPI 3: Match Yield */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/90 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.06)] hover:shadow-[0_8px_30px_-6px_rgba(0,0,0,0.09)] transition-all card-hover flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] uppercase tracking-wider text-slate-500 font-bold">
              Top-Tier Shortlist Yield
            </span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100">
              <span className="material-symbols-outlined text-[18px]">star</span>
            </div>
          </div>
          <div className="mt-3">
            <div className="flex items-baseline gap-1.5">
              <span className="font-mono text-2xl font-extrabold text-emerald-700">
                {summary.avg_match_yield}%
              </span>
              <span className="text-xs text-slate-500 font-medium">High Match</span>
            </div>
            <div className="flex items-center gap-1.5 mt-1 font-mono text-[11px] text-slate-500 font-medium">
              <span>Threshold score ≥ 80%</span>
            </div>
          </div>
        </div>

        {/* KPI 4: Speed */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/90 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.06)] hover:shadow-[0_8px_30px_-6px_rgba(0,0,0,0.09)] transition-all card-hover flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] uppercase tracking-wider text-slate-500 font-bold">
              Avg Screening Speed
            </span>
            <div className="w-8 h-8 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center border border-teal-100">
              <span className="material-symbols-outlined text-[18px]">bolt</span>
            </div>
          </div>
          <div className="mt-3">
            <div className="flex items-baseline gap-1.5">
              <span className="font-mono text-2xl font-extrabold text-teal-700">
                {summary.avg_batch_latency}
              </span>
              <span className="text-xs text-slate-500 font-medium">per cohort</span>
            </div>
            <div className="flex items-center gap-1.5 mt-1 font-mono text-[11px] text-emerald-700 font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>Local On-Device AI</span>
            </div>
          </div>
        </div>
      </div>

      {/* Search & Filter Controls */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white p-3 rounded-2xl border border-slate-200/80 shadow-xs">
        <div className="relative flex-1 max-w-md">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[18px] text-slate-400">
            search
          </span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by role title, job code, or department..."
            className="w-full h-9 pl-9 pr-3 text-xs bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 text-slate-900 transition-all placeholder:text-slate-400"
          />
        </div>

        {/* Quick Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto">
          <button
            type="button"
            onClick={() => setSelectedCategory('all')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer btn-press ${
              selectedCategory === 'all'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:text-slate-900'
            }`}
          >
            All Roles ({runs.length})
          </button>
          <button
            type="button"
            onClick={() => setSelectedCategory('eng')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer btn-press ${
              selectedCategory === 'eng'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:text-slate-900'
            }`}
          >
            Engineering
          </button>
          <button
            type="button"
            onClick={() => setSelectedCategory('prod')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer btn-press ${
              selectedCategory === 'prod'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:text-slate-900'
            }`}
          >
            Product &amp; Design
          </button>
          <button
            type="button"
            onClick={() => setSelectedCategory('data')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer btn-press ${
              selectedCategory === 'data'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:text-slate-900'
            }`}
          >
            Data &amp; AI
          </button>
        </div>
      </div>

      {/* Main Evaluation Runs Data Table */}
      <div className="w-full bg-white rounded-2xl shadow-[0_4px_20px_-4px_rgba(0,0,0,0.06)] overflow-hidden flex flex-col border border-slate-200/90">
        {/* Table Header Action Strip */}
        <div className="px-5 py-3 bg-slate-50 flex items-center justify-between text-slate-600 text-[11px] uppercase tracking-wider font-bold border-b border-slate-200">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px] text-blue-600">history</span>
            <span>Historical Hiring Drives &amp; Candidate Cohorts</span>
          </div>
          <div className="flex items-center gap-3 font-mono text-[11px] normal-case text-slate-500">
            <span>Sorted by Most Recent</span>
            <button
              type="button"
              onClick={loadHistory}
              title="Refresh Table"
              className="text-slate-500 hover:text-blue-600 transition-colors cursor-pointer"
            >
              <span className="material-symbols-outlined text-[18px]">refresh</span>
            </button>
          </div>
        </div>

        {/* Table Body Container */}
        <div className="overflow-x-auto w-full">
          <table className="w-full text-left border-collapse min-w-[1000px]">
            <thead>
              <tr className="bg-slate-50/50 text-[11px] text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-100">
                <th className="py-3 px-4 whitespace-nowrap">Drive Code &amp; Date</th>
                <th className="py-3 px-4 min-w-[240px]">Role / Benchmark Spec</th>
                <th className="py-3 px-4 whitespace-nowrap">Location / Dept</th>
                <th className="py-3 px-4 text-right whitespace-nowrap">Resumes</th>
                <th className="py-3 px-4 min-w-[280px]">Top Ranked Candidates</th>
                <th className="py-3 px-4 whitespace-nowrap">Weights</th>
                <th className="py-3 px-4 text-center whitespace-nowrap">Status</th>
                <th className="py-3 px-4 text-right whitespace-nowrap">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs text-slate-800">
              {isLoading ? (
                <tr>
                  <td colSpan={8} className="py-14 text-center text-slate-500">
                    <div className="inline-flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                      <span>Loading historical recruitment records...</span>
                    </div>
                  </td>
                </tr>
              ) : filteredRuns.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-14 text-center text-slate-500">
                    No matching hiring drives found.
                  </td>
                </tr>
              ) : (
                filteredRuns.map((run) => (
                  <tr
                    key={run.run_id}
                    className="hover:bg-blue-50/30 transition-all duration-150 group cursor-pointer"
                    onClick={() => handleViewCampaign(run)}
                  >
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <div className="font-mono text-xs font-bold text-blue-700">
                        #{run.run_id}
                      </div>
                      <div className="font-mono text-[11px] text-slate-400 mt-0.5">
                        {run.created_at}
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="text-sm font-bold text-slate-900 group-hover:text-blue-700 transition-colors">
                        {run.title}
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5 font-medium">
                        {run.benchmark_spec}
                      </div>
                    </td>

                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
                        {run.department}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-right whitespace-nowrap">
                      <div className="font-mono text-xs font-bold text-slate-900">
                        {run.files_count} Resumes
                      </div>
                      <div className="font-mono text-[10px] text-emerald-700 font-semibold">
                        {run.processed_status}
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        {run.top_candidates?.map((cand, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-lg bg-blue-50 text-blue-900 font-mono text-[11px] font-semibold border border-blue-100"
                          >
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                            <span>{cand.name}</span>
                            <span className="text-blue-700 font-bold">
                              {Math.round(cand.score)}%
                            </span>
                          </span>
                        ))}
                        {(!run.top_candidates || run.top_candidates.length === 0) && (
                          <span className="text-slate-400 text-xs italic">Awaiting evaluations</span>
                        )}
                      </div>
                    </td>

                    <td className="py-3.5 px-4 whitespace-nowrap font-mono text-[11px] text-slate-500">
                      {run.calibrated_weights}
                    </td>

                    <td className="py-3.5 px-4 text-center whitespace-nowrap">
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full font-mono text-[11px] bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold">
                        <span className="material-symbols-outlined text-[13px] text-emerald-600">check</span>
                        {run.status}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-right whitespace-nowrap">
                      <div className="inline-flex items-center gap-1.5 justify-end">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleViewCampaign(run);
                          }}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-blue-600 text-white font-medium text-xs transition-all cursor-pointer btn-press shadow-xs"
                        >
                          <span>View Results</span>
                          <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
                        </button>
                        <button
                          type="button"
                          onClick={(e) => handleDeleteRun(e, run)}
                          className="w-7 h-7 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 flex items-center justify-center transition-colors cursor-pointer"
                          title="Delete this drive"
                        >
                          <span className="material-symbols-outlined text-[16px]">delete</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
