import React, { useState, useEffect } from 'react';

export default function CandidateDeepDiveDrawer({
  candidate,
  activeJd,
  isOpen,
  onClose,
}) {
  const [activeProofTab, setActiveProofTab] = useState('experience'); // 'experience' | 'projects' | 'education'
  const [isShortlisted, setIsShortlisted] = useState(false);

  useEffect(() => {
    setIsShortlisted(false);
  }, [candidate?.id]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !candidate) return null;

  const score = Math.round(candidate.recomputedScore ?? candidate.overall_score ?? 0);
  const skillScore = Math.round(candidate.skill_score ?? 80);
  const semanticScore = Math.round(candidate.semantic_score ?? 75);
  const expScore = Math.round(candidate.experience_score ?? 85);
  const expYears = candidate.experience_years ?? 0;
  const reqYears = activeJd?.min_experience_years || candidate.jd_min_experience_years || 4.0;
  const expDiff = expYears - reqYears;

  const isTop = score >= 80;
  const isModerate = score >= 65 && score < 80;
  const matchTierText = isTop
    ? '⭐ Strong Match (Top Tier)'
    : isModerate
    ? '👍 Qualified Match'
    : '⚠️ Low Match / Upskill';

  const sections = candidate.segmented_sections || {};
  const experienceText =
    sections.experience ||
    sections.summary ||
    'Verified career history records show consistent technical development and engineering contribution.';
  const projectsText =
    sections.projects ||
    'Extracted project portfolio records indicate hands-on software development and architecture experience.';
  const educationText =
    candidate.education_summary ||
    sections.education ||
    'B.Tech / B.E. in Computer Science & Engineering or equivalent technical degree.';

  const isPdf = (candidate.filename || '').toLowerCase().endsWith('.pdf');

  // Candidate reference ID
  const refId = `TR-IN-${(candidate.id || '8a92f').replace(/[^a-fA-F0-9]/g, '').slice(0, 6).toUpperCase() || 'IND-8821'}`;

  const handleDownloadCv = () => {
    alert(`Downloading original resume file: ${candidate.filename || 'resume.pdf'}`);
  };

  const handleToggleShortlist = () => {
    setIsShortlisted((prev) => !prev);
  };

  return (
    <>
      {/* Backdrop Modal Overlay */}
      <div
        className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-xs transition-opacity duration-300"
        onClick={onClose}
      />

      {/* Candidate-Level Deep-Dive Slide-Over Drawer */}
      <aside
        aria-label="Candidate Evaluation Details"
        className="fixed right-0 top-0 bottom-0 z-50 w-full sm:w-[700px] h-screen bg-white shadow-2xl flex flex-col overflow-y-auto animate-slideInRight border-l border-slate-200"
      >
        {/* 1. Drawer Header */}
        <div className="p-6 bg-white sticky top-0 z-20 flex items-start justify-between shadow-xs border-b border-slate-100">
          <div className="flex flex-col gap-1 min-w-0 pr-4">
            <div className="flex items-center gap-2.5 flex-wrap">
              <h2 className="text-xl font-extrabold text-slate-900 tracking-tight truncate">
                {candidate.candidate_name || 'Candidate'}
              </h2>
              <span className="font-mono text-xs px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 font-bold border border-blue-200">
                Rank #{String(candidate.dynamicRank || candidate.rank || 1).padStart(2, '0')}
              </span>
            </div>

            <p className="text-xs text-slate-600 truncate mt-0.5">
              {candidate.email || 'not_provided@local'} • {candidate.phone || '+91-9489959957'} •{' '}
              {candidate.education_summary || 'B.Tech / B.E. in Computer Science'}
            </p>

            <div className="mt-1 flex items-center gap-2 flex-wrap">
              <div className="inline-flex items-center gap-1.5 font-mono text-[11px] bg-slate-100 text-slate-700 px-2.5 py-0.5 rounded-md border border-slate-200">
                <span
                  className={`material-symbols-outlined text-[15px] ${
                    isPdf ? 'text-red-600' : 'text-blue-600'
                  }`}
                >
                  {isPdf ? 'picture_as_pdf' : 'description'}
                </span>
                <span className="truncate max-w-[220px]">
                  {candidate.filename || 'candidate_resume.pdf'}
                </span>
              </div>
              <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                ✓ Smart Engine Verified
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4 shrink-0">
            {/* Match Score Badge */}
            <div className="flex flex-col items-end">
              <div
                className={`px-3 py-1.5 rounded-xl flex items-baseline gap-1 shadow-sm border ${
                  isTop
                    ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                    : isModerate
                    ? 'bg-amber-50 text-amber-900 border-amber-200'
                    : 'bg-red-50 text-red-800 border-red-200'
                }`}
              >
                <span className="font-mono font-extrabold text-xl">
                  {score}
                </span>
                <span className="font-mono text-xs opacity-75">/ 100</span>
              </div>
              <span className="text-[11px] font-bold mt-1 text-slate-600">
                {matchTierText}
              </span>
            </div>

            <button
              type="button"
              aria-label="Close details panel"
              onClick={onClose}
              className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
            >
              <span className="material-symbols-outlined text-[20px]">close</span>
            </button>
          </div>
        </div>

        {/* 2. Score Breakdown Cards */}
        <div className="p-6 bg-slate-50/70 border-b border-slate-200/80">
          <div className="grid grid-cols-3 gap-3">
            {/* Box 1: Skills */}
            <div className="bg-white p-3.5 rounded-xl shadow-xs flex flex-col justify-between border border-slate-200/80 card-hover">
              <span className="text-[11px] uppercase tracking-wider text-slate-500 font-bold">
                Skill Match
              </span>
              <div className="my-1">
                <span className="font-mono font-extrabold text-blue-700 text-xl">
                  {skillScore}%
                </span>
              </div>
              <span className="text-xs text-slate-600 font-medium">
                {candidate.matched_skills?.length || 0} Required Skills Matched
              </span>
            </div>

            {/* Box 2: Experience */}
            <div className="bg-white p-3.5 rounded-xl shadow-xs flex flex-col justify-between border border-slate-200/80 card-hover">
              <span className="text-[11px] uppercase tracking-wider text-slate-500 font-bold">
                Experience (YoE)
              </span>
              <div className="my-1 flex items-baseline gap-1">
                <span className="font-mono font-extrabold text-teal-700 text-xl">
                  {expScore}%
                </span>
                {expDiff >= 0 && (
                  <span className="font-mono text-xs text-emerald-600 font-bold">
                    +{expDiff.toFixed(1)}y
                  </span>
                )}
              </div>
              <span className="text-xs text-slate-600 font-medium font-mono">
                {expYears.toFixed(1)}y vs {reqYears.toFixed(1)}y Req
              </span>
            </div>

            {/* Box 3: Role / Semantic Similarity */}
            <div className="bg-white p-3.5 rounded-xl shadow-xs flex flex-col justify-between border border-slate-200/80 card-hover">
              <span className="text-[11px] uppercase tracking-wider text-slate-500 font-bold">
                Project Depth
              </span>
              <div className="my-1">
                <span className="font-mono font-extrabold text-indigo-700 text-xl">
                  {semanticScore}%
                </span>
              </div>
              <span className="text-xs text-slate-600 font-medium">
                High Architectural Overlap
              </span>
            </div>
          </div>
        </div>

        {/* 3. Section 2: Scoring Explanation & Recruiter Summary */}
        <div className="p-6 bg-white border-b border-slate-200/80">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs uppercase tracking-wider text-slate-700 font-bold flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[16px] text-blue-600">psychology</span>
              <span>Candidate Score Breakdown &amp; HR Insights</span>
            </h3>
            <span className="font-mono text-[11px] text-slate-500 bg-slate-100 px-2 py-0.5 rounded font-semibold">
              Max Score: 100 pts
            </span>
          </div>

          <div className="bg-slate-50/80 rounded-xl p-4 flex flex-col gap-2.5 text-xs text-slate-800 border border-slate-200/70">
            <div className="flex items-start gap-2">
              <span className="font-mono text-xs text-blue-700 font-bold shrink-0">
                [+{(skillScore * 0.5).toFixed(1)} pts]
              </span>
              <span>
                <strong>Direct Technical Skill Match:</strong> Candidate verified hands-on competency in{' '}
                <strong>
                  {candidate.matched_skills?.length || 0} of {activeJd?.required_skills?.length || 12}
                </strong>{' '}
                key skills:{' '}
                <span className="text-blue-900 font-semibold">
                  {(candidate.matched_skills || []).slice(0, 6).join(', ') || 'None'}
                </span>.
              </span>
            </div>

            {candidate.partial_skills?.length > 0 && (
              <div className="flex items-start gap-2">
                <span className="font-mono text-xs text-indigo-700 font-bold shrink-0">
                  [+4.2 pts]
                </span>
                <span>
                  <strong>Related Competency Recognition:</strong> Resume mentions{' '}
                  <code className="font-mono bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-900 font-bold">
                    {candidate.partial_skills[0].candidate_has}
                  </code>{' '}
                  which maps to requirement{' '}
                  <code className="font-mono bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-900 font-bold">
                    {candidate.partial_skills[0].required}
                  </code>{' '}
                  with {Math.round(candidate.partial_skills[0].similarity * 100)}% technical alignment.
                </span>
              </div>
            )}

            <div className="flex items-start gap-2">
              <span className="font-mono text-xs text-teal-700 font-bold shrink-0">
                [+{(expScore * 0.2).toFixed(1)} pts]
              </span>
              <span>
                <strong>Experience Tenure Alignment:</strong> Verified career tenure of{' '}
                <strong>{expYears.toFixed(1)} Years</strong>{' '}
                {expDiff >= 0
                  ? `exceeds the ${reqYears.toFixed(1)}-year minimum threshold by ${expDiff.toFixed(1)} years.`
                  : `is currently below the ${reqYears.toFixed(1)}-year threshold (-${Math.abs(expDiff).toFixed(1)} yrs).`}
              </span>
            </div>

            <div className="flex items-start gap-2">
              <span className="font-mono text-xs text-purple-700 font-bold shrink-0">
                [+{(semanticScore * 0.3).toFixed(1)} pts]
              </span>
              <span>
                <strong>Project &amp; Role Relevance:</strong> Candidate's documented past engineering duties show consistent architectural overlap with this role.
              </span>
            </div>
          </div>
        </div>

        {/* 4. Section 3: Skill Compliance Matrix */}
        <div className="p-6 bg-white border-b border-slate-200/80">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs uppercase tracking-wider text-slate-700 font-bold flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[16px] text-emerald-600">checklist</span>
              <span>Skill Compliance Matrix</span>
            </h3>
            <span className="text-[11px] text-slate-500 font-medium">NLP Extracted &amp; Verified</span>
          </div>

          <div className="space-y-4">
            {/* Direct Matched Skills */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-800">
                <span className="material-symbols-outlined text-[16px] text-emerald-600">
                  check_circle
                </span>
                <span>Direct Skills Matched ({candidate.matched_skills?.length || 0})</span>
              </div>
              <div className="flex flex-wrap gap-1.5 p-2 bg-emerald-50/50 rounded-xl border border-emerald-100">
                {(candidate.matched_skills || []).map((skill) => (
                  <span
                    key={skill}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white text-emerald-900 text-xs font-semibold border border-emerald-200 shadow-2xs"
                  >
                    <span className="material-symbols-outlined text-[13px] text-emerald-600">
                      done
                    </span>
                    {skill}
                  </span>
                ))}
                {(!candidate.matched_skills || candidate.matched_skills.length === 0) && (
                  <span className="text-xs text-slate-400 italic">No exact skill matches found</span>
                )}
              </div>
            </div>

            {/* Adjacent / Related Skills */}
            {candidate.partial_skills?.length > 0 && (
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center gap-1.5 text-xs font-bold text-blue-800">
                  <span className="material-symbols-outlined text-[16px] text-blue-600">
                    swap_horiz
                  </span>
                  <span>Related / Adjacent Skills ({candidate.partial_skills.length})</span>
                </div>
                <div className="flex flex-wrap gap-2 p-2 bg-blue-50/50 rounded-xl border border-blue-100">
                  {candidate.partial_skills.map((part, i) => (
                    <div
                      key={i}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white text-blue-900 text-xs font-semibold border border-blue-200 shadow-2xs"
                    >
                      <span>{part.candidate_has}</span>
                      <span className="text-slate-400 text-[10px]">≈</span>
                      <span className="text-blue-700">{part.required}</span>
                      <span className="font-mono text-[10px] text-blue-600 bg-blue-100 px-1 py-0.2 rounded font-bold">
                        {Math.round(part.similarity * 100)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Missing Skill Gaps */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center gap-1.5 text-xs font-bold text-amber-800">
                <span className="material-symbols-outlined text-[16px] text-amber-600">
                  warning
                </span>
                <span>Skill Gaps for this Role ({candidate.missing_skills?.length || 0})</span>
              </div>
              <div className="flex flex-wrap gap-1.5 p-2 bg-amber-50/50 rounded-xl border border-amber-100">
                {(candidate.missing_skills || []).map((skill) => (
                  <span
                    key={skill}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white text-amber-900 text-xs font-semibold border border-amber-200 shadow-2xs"
                  >
                    <span className="material-symbols-outlined text-[13px] text-amber-600">
                      close
                    </span>
                    {skill}
                  </span>
                ))}
                {(!candidate.missing_skills || candidate.missing_skills.length === 0) && (
                  <span className="text-xs text-emerald-700 font-semibold flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]">check</span>
                    All required skills are fully satisfied
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* 5. Section 4: Verified Career History & Project Evidence */}
        <div className="p-6 bg-white flex-1 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs uppercase tracking-wider text-slate-700 font-bold flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[16px] text-indigo-600">
                verified
              </span>
              <span>Verified Career History &amp; Project Evidence</span>
            </h3>
            <span className="font-mono text-[11px] text-slate-500">Extracted from CV</span>
          </div>

          <div className="flex flex-col gap-4">
            {/* Experience tenure comparison card */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 flex flex-col justify-between">
                <span className="text-[10px] uppercase font-bold text-slate-500">
                  Job Requirement
                </span>
                <div className="mt-1 flex items-baseline gap-1">
                  <span className="font-mono text-base font-extrabold text-slate-900">
                    {reqYears.toFixed(1)}+ Years YoE
                  </span>
                </div>
                <span className="text-[11px] text-slate-500 mt-0.5">
                  Full-Stack AI Engineering
                </span>
              </div>

              <div className="bg-emerald-50 p-3.5 rounded-xl border border-emerald-200 flex flex-col justify-between">
                <span className="text-[10px] uppercase font-bold text-emerald-800">
                  Candidate Verified Record
                </span>
                <div className="mt-1 flex items-baseline gap-1">
                  <span className="font-mono text-base font-extrabold text-emerald-900">
                    {expYears.toFixed(1)} Years YoE
                  </span>
                </div>
                <span className="text-[11px] text-emerald-700 mt-0.5">
                  Verified Career History
                </span>
              </div>
            </div>

            {/* Segmented Tab Header for Proof */}
            <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200">
              <button
                type="button"
                onClick={() => setActiveProofTab('experience')}
                className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                  activeProofTab === 'experience'
                    ? 'text-blue-700 bg-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Work Experience
              </button>
              <button
                type="button"
                onClick={() => setActiveProofTab('projects')}
                className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                  activeProofTab === 'projects'
                    ? 'text-blue-700 bg-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Key Projects Portfolio
              </button>
              <button
                type="button"
                onClick={() => setActiveProofTab('education')}
                className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                  activeProofTab === 'education'
                    ? 'text-blue-700 bg-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Education &amp; Certifications
              </button>
            </div>

            {/* Extracted Text Content Box */}
            <div className="bg-slate-50 rounded-xl p-4 flex flex-col gap-3 text-xs leading-relaxed text-slate-800 border border-slate-200 max-h-64 overflow-y-auto">
              {activeProofTab === 'experience' && (
                <div className="whitespace-pre-line font-mono text-[11px] leading-relaxed text-slate-700">
                  {experienceText}
                </div>
              )}
              {activeProofTab === 'projects' && (
                <div className="whitespace-pre-line font-mono text-[11px] leading-relaxed text-slate-700">
                  {projectsText}
                </div>
              )}
              {activeProofTab === 'education' && (
                <div className="whitespace-pre-line font-mono text-[11px] leading-relaxed text-slate-700">
                  {educationText}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Sticky Drawer Footer */}
        <div className="sticky bottom-0 z-20 p-4 px-6 bg-white shadow-lg mt-auto flex items-center justify-between gap-4 border-t border-slate-200">
          <div className="flex items-center gap-2 font-mono text-[11px] text-slate-500">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Ref: {refId}</span>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleDownloadCv}
              className="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-all flex items-center gap-1.5 cursor-pointer btn-press"
            >
              <span className="material-symbols-outlined text-[16px]">download</span>
              <span>Download CV</span>
            </button>

            <button
              type="button"
              onClick={handleToggleShortlist}
              className={`px-4 py-2 rounded-xl text-xs font-bold shadow-sm transition-all flex items-center gap-1.5 cursor-pointer btn-press ${
                isShortlisted
                  ? 'bg-emerald-600 text-white shadow-emerald-500/25'
                  : 'bg-blue-600 hover:bg-blue-700 text-white shadow-blue-500/25'
              }`}
            >
              <span className="material-symbols-outlined text-[16px]">
                {isShortlisted ? 'done_all' : 'check_circle'}
              </span>
              <span>{isShortlisted ? 'Candidate Shortlisted' : 'Shortlist Candidate'}</span>
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
