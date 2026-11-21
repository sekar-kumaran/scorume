import React, { useState, useRef, useEffect } from 'react';
import { previewJdExtraction } from '../api/client';

const SAMPLE_AI_JD_TEXT = `Job Title: Senior Full-Stack AI Engineer
Location: Bengaluru, Karnataka / Hybrid (India)
Target CTC: ₹28 - ₹42 LPA
Experience Required: Minimum 4+ years building production-grade web applications with modern backend architectures and distributed ML inference pipelines.

Key Responsibilities:
- Design, build, and deploy production ML microservices and API gateways using Python (FastAPI).
- Architect responsive, data-dense web user interfaces using React.js and TypeScript.
- Build vector search and semantic retrieval pipelines using PostgreSQL, pgvector, and SentenceTransformers.
- Maintain high code quality through automated testing (pytest), Docker containerization, and CI/CD automation.

Required Skills & Technical Competencies:
- Programming: Python, TypeScript, JavaScript
- Frameworks: FastAPI, React.js, Next.js
- Databases: PostgreSQL, pgvector, Redis
- Infrastructure: Docker, Kubernetes, CI/CD, Git
- AI / ML: Sentence Transformers, NLP, Vector Embeddings, LLM Orchestration`;

export default function CampaignSetupView({
  activeJd,
  setActiveJd,
  onRunEvaluation,
  isEvaluating,
  onLoadSampleDemo,
  isLoadingDemo,
}) {
  const [inputMode, setInputMode] = useState('paste'); // 'paste' | 'upload'
  const [jdTitle, setJdTitle] = useState('');
  const [jdText, setJdText] = useState('');
  const [jdFile, setJdFile] = useState(null);
  const [expYears, setExpYears] = useState('3.0');
  const [skills, setSkills] = useState([]);
  const [queuedFiles, setQueuedFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [newSkillInput, setNewSkillInput] = useState('');
  const [showAddSkill, setShowAddSkill] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [formError, setFormError] = useState('');

  const fileInputRef = useRef(null);
  const jdFileInputRef = useRef(null);
  const debounceTimerRef = useRef(null);

  // Sync state if activeJd updates externally (e.g. after demo load or selecting from history)
  useEffect(() => {
    if (activeJd) {
      if (activeJd.title) setJdTitle(activeJd.title);
      if (activeJd.raw_text) setJdText(activeJd.raw_text);
      if (activeJd.min_experience_years !== undefined) {
        setExpYears(String(activeJd.min_experience_years));
      }
      if (activeJd.required_skills?.length > 0) {
        setSkills(activeJd.required_skills);
      }
    }
  }, [activeJd]);

  // Auto-detect title and skills when pasting or typing JD text
  const handleAutoExtract = async (textToExtract) => {
    const text = (textToExtract || jdText || '').trim();
    if (!text || text.length < 20) return;

    setIsExtracting(true);
    try {
      const res = await previewJdExtraction(text);
      if (res) {
        if (res.title && (!jdTitle || jdTitle === 'Untitled Role')) {
          setJdTitle(res.title);
        }
        if (res.required_skills && res.required_skills.length > 0) {
          setSkills(res.required_skills);
        }
        if (res.min_experience_years) {
          setExpYears(String(res.min_experience_years));
        }
      }
    } catch (err) {
      console.warn('Auto-extraction preview failed:', err);
    } finally {
      setIsExtracting(false);
    }
  };

  // Textarea change with debounce for skill detection
  const handleJdTextChange = (e) => {
    const newText = e.target.value;
    setJdText(newText);
    setFormError('');

    // Try to auto-detect title from first line if empty
    if (!jdTitle && newText.trim()) {
      const firstLine = newText.trim().split('\n')[0].replace(/^(role|title|job title|position)\s*:\s*/i, '').trim();
      if (firstLine && firstLine.length < 60 && !firstLine.includes('.')) {
        setJdTitle(firstLine);
      }
    }

    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    debounceTimerRef.current = setTimeout(() => {
      handleAutoExtract(newText);
    }, 1000);
  };

  // Clear / Start a completely fresh hiring drive
  const handleStartFresh = () => {
    setJdTitle('');
    setJdText('');
    setJdFile(null);
    setExpYears('3.0');
    setSkills([]);
    setQueuedFiles([]);
    setFormError('');
    setActiveJd(null);
  };

  // Populate sample template text for quick testing
  const handleLoadSampleTemplate = () => {
    setJdTitle('Senior Full-Stack AI Engineer');
    setJdText(SAMPLE_AI_JD_TEXT);
    setExpYears('4.0');
    setSkills(['Python', 'FastAPI', 'React.js', 'PostgreSQL', 'Docker', 'NLP', 'TypeScript']);
    setJdFile(null);
    setInputMode('paste');
    setFormError('');
  };

  // Candidate Resumes Dropzone Handlers
  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer?.files?.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files).filter((f) => {
        const ext = f.name.toLowerCase();
        return ext.endsWith('.pdf') || ext.endsWith('.docx') || ext.endsWith('.txt');
      });
      setQueuedFiles((prev) => [...prev, ...newFiles]);
      setFormError('');
    }
  };

  const handleFileSelect = (e) => {
    if (e.target?.files?.length > 0) {
      const newFiles = Array.from(e.target.files);
      setQueuedFiles((prev) => [...prev, ...newFiles]);
      setFormError('');
    }
  };

  const handleRemoveFile = (indexToRemove) => {
    setQueuedFiles((prev) => prev.filter((_, idx) => idx !== indexToRemove));
  };

  const handleRemoveSkill = (skillToRemove) => {
    setSkills((prev) => prev.filter((s) => s !== skillToRemove));
  };

  const handleAddSkill = (e) => {
    e.preventDefault();
    if (newSkillInput && newSkillInput.trim()) {
      const trimmed = newSkillInput.trim();
      if (!skills.includes(trimmed)) {
        setSkills((prev) => [...prev, trimmed]);
      }
      setNewSkillInput('');
      setShowAddSkill(false);
    }
  };

  // Job Description File Upload
  const handleJdFileUpload = (e) => {
    const file = e.target?.files?.[0];
    if (file) {
      setJdFile(file);
      setFormError('');

      // Auto-populate title from filename if title is empty
      if (!jdTitle) {
        const baseName = file.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ');
        setJdTitle(baseName.charAt(0).toUpperCase() + baseName.slice(1));
      }

      // If text file, read into textarea
      if (file.name.toLowerCase().endsWith('.txt')) {
        const reader = new FileReader();
        reader.onload = (event) => {
          const text = event.target?.result;
          if (text && typeof text === 'string') {
            setJdText(text);
            handleAutoExtract(text);
          }
        };
        reader.readAsText(file);
      } else {
        // For PDF or DOCX, indicate file staged
        setJdText(`[Staged file: ${file.name} (${(file.size / 1024).toFixed(1)} KB)]\nFull document parsing will occur locally on upload.`);
      }
    }
  };

  // Submit Evaluation
  const handleSubmitEvaluation = () => {
    const hasJdContent = (jdText && jdText.trim().length >= 15) || jdFile;
    if (!hasJdContent) {
      setFormError('Please provide a Job Description (paste requirements text or upload a JD document).');
      return;
    }
    if (queuedFiles.length === 0) {
      setFormError('Please select or drop at least one candidate resume (PDF or DOCX) to evaluate.');
      return;
    }

    setFormError('');
    onRunEvaluation({
      rawText: jdFile ? '' : jdText,
      file: jdFile,
      title: jdTitle.trim() || 'Untitled Role Benchmark',
      minExperienceYears: parseFloat(expYears) || 3.0,
      requiredSkills: skills,
      files: queuedFiles,
    });
  };

  const jdCharCount = jdText.length;
  const jdTokenEst = Math.round(jdCharCount / 7.8);
  const totalPayloadMB = (
    queuedFiles.reduce((acc, f) => acc + (f.size || 0), 0) / (1024 * 1024)
  ).toFixed(2);

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 KB';
    if (bytes < 1024 * 1024) {
      return `${Math.round(bytes / 1024)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="max-w-[1400px] w-full mx-auto py-8 px-6 flex flex-col gap-6 animate-fadeIn">
      {/* View Header with Pipeline Status & Action Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-700">
            <span>RECRUITMENT WORKFLOW</span>
            <span className="text-slate-300">/</span>
            <span>STEP 01: JOB BENCHMARK &amp; CANDIDATE SCREENING</span>
          </div>
          <h1 className="font-headline-xl text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight mt-1">
            Job Benchmark &amp; Candidate Screening
          </h1>
          <div className="flex flex-wrap items-center gap-2 mt-1.5 text-xs text-slate-600">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span className="font-semibold text-slate-900">Current Role:</span>
            <span className="font-medium text-blue-800 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
              {jdTitle || 'New Custom Requisition'}
            </span>
            <span className="text-slate-300">•</span>
            <span>100% Local Inference Engine</span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            type="button"
            onClick={handleStartFresh}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 text-xs font-semibold shadow-xs transition-all cursor-pointer btn-press"
            title="Clear all fields to evaluate a new position"
          >
            <span className="material-symbols-outlined text-[16px] text-slate-400">restart_alt</span>
            <span>Start Fresh</span>
          </button>

          <button
            type="button"
            onClick={handleLoadSampleTemplate}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 text-xs font-semibold shadow-xs transition-all cursor-pointer btn-press"
            title="Fill in a sample Job Description template"
          >
            <span className="material-symbols-outlined text-[16px] text-blue-600">content_paste</span>
            <span>Use AI Engineer Template</span>
          </button>

          {onLoadSampleDemo && (
            <button
              type="button"
              onClick={onLoadSampleDemo}
              disabled={isLoadingDemo}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-800 border border-blue-200 text-xs font-semibold shadow-xs transition-all cursor-pointer disabled:opacity-60 btn-press"
              title="Loads 12 pre-generated sample test resumes for demonstration"
            >
              <span className="material-symbols-outlined text-[16px] text-blue-600">auto_mode</span>
              <span>{isLoadingDemo ? 'Loading Demo Dataset...' : 'Load 12 Sample Resumes'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Validation Error Alert */}
      {formError && (
        <div className="p-3.5 bg-red-50 border border-red-200 rounded-xl flex items-center justify-between text-red-800 text-xs font-medium animate-fadeIn">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px] text-red-600">warning</span>
            <span>{formError}</span>
          </div>
          <button
            type="button"
            onClick={() => setFormError('')}
            className="text-red-500 hover:text-red-800 font-bold text-sm cursor-pointer"
          >
            ✕
          </button>
        </div>
      )}

      {/* Balanced 12-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Module 1: Job Description & Benchmark Configuration (7 Columns) */}
        <div className="lg:col-span-7 flex flex-col bg-white rounded-2xl p-6 border border-slate-200/90 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.06)] hover:shadow-[0_8px_30px_-6px_rgba(0,0,0,0.09)] transition-all duration-300">
          {/* Header & Segmented Mode Switch */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 mb-4 border-b border-slate-100">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-700 flex items-center justify-center border border-blue-100">
                <span className="material-symbols-outlined text-[18px]">tune</span>
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-900 leading-tight">
                  Job Benchmark Specification
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Define target position, experience bar, and technical skill taxonomy
                </p>
              </div>
            </div>

            {/* Segmented Toggle: Paste Text vs Upload File */}
            <div className="inline-flex p-1 bg-slate-100 rounded-xl self-start sm:self-auto border border-slate-200/60">
              <button
                type="button"
                onClick={() => setInputMode('paste')}
                className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                  inputMode === 'paste'
                    ? 'text-slate-900 bg-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Paste Text
              </button>
              <button
                type="button"
                onClick={() => {
                  setInputMode('upload');
                  jdFileInputRef.current?.click();
                }}
                className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                  inputMode === 'upload'
                    ? 'text-slate-900 bg-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Upload JD Document
              </button>
              <input
                ref={jdFileInputRef}
                type="file"
                accept=".txt,.pdf,.docx"
                className="sr-only"
                onChange={handleJdFileUpload}
              />
            </div>
          </div>

          {/* Job Role / Title Input Field */}
          <div className="flex flex-col gap-1.5 mb-4">
            <label className="text-xs uppercase tracking-wider text-slate-600 font-bold flex items-center justify-between">
              <span>Job Role / Requisition Title</span>
              <span className="text-[11px] text-slate-400 font-normal">e.g. Senior Backend Engineer</span>
            </label>
            <input
              type="text"
              value={jdTitle}
              onChange={(e) => {
                setJdTitle(e.target.value);
                setFormError('');
              }}
              placeholder="e.g. Senior Data Scientist — Applied ML, Full-Stack Engineer, DevOps Lead..."
              className="w-full h-10 px-3.5 bg-slate-50 rounded-xl font-sans text-sm font-semibold text-slate-900 border border-slate-200 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-100 focus:outline-none transition-all shadow-2xs"
            />
          </div>

          {/* JD Document / Text Section */}
          {inputMode === 'upload' && jdFile ? (
            <div className="mb-4 p-4 rounded-xl bg-blue-50/50 border border-blue-200 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-xs">
                  {jdFile.name.split('.').pop()?.toUpperCase()}
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-900">{jdFile.name}</div>
                  <div className="font-mono text-[11px] text-slate-500 mt-0.5">
                    {formatFileSize(jdFile.size)} • Ready for local PyMuPDF extraction
                  </div>
                </div>
              </div>
              <button
                type="button"
                onClick={() => {
                  setJdFile(null);
                  setJdText('');
                  setInputMode('paste');
                }}
                className="text-xs font-semibold text-red-600 hover:text-red-800 bg-white px-2.5 py-1 rounded-lg border border-red-200 shadow-2xs cursor-pointer"
              >
                Change File
              </button>
            </div>
          ) : (
            <div className="relative flex flex-col mb-4">
              <div className="flex justify-between items-center mb-1.5">
                <label className="text-xs uppercase tracking-wider text-slate-600 font-bold">
                  Job Description Text
                </label>
                <div className="flex items-center gap-3">
                  {isExtracting ? (
                    <span className="text-[11px] text-blue-600 font-semibold flex items-center gap-1">
                      <span className="w-3 h-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></span>
                      Detecting requirements...
                    </span>
                  ) : (
                    jdText.length > 30 && (
                      <button
                        type="button"
                        onClick={() => handleAutoExtract(jdText)}
                        className="text-[11px] text-blue-700 font-semibold hover:underline flex items-center gap-1 cursor-pointer"
                      >
                        <span className="material-symbols-outlined text-[13px]">refresh</span>
                        <span>Auto-Detect Skills</span>
                      </button>
                    )
                  )}
                  <span className="font-mono text-[11px] text-slate-400">
                    {jdCharCount} chars • ~{jdTokenEst} tokens
                  </span>
                </div>
              </div>

              <textarea
                rows={7}
                value={jdText}
                onChange={handleJdTextChange}
                placeholder="Paste complete job description requirements here (responsibilities, required tech stack, years of experience)..."
                className="w-full p-3.5 bg-slate-50/70 rounded-xl font-mono text-xs text-slate-800 border border-slate-200 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-100 focus:outline-none transition-all resize-y shadow-inner"
              />
            </div>
          )}

          {/* Module Inner Card: Key Requirements Extracted */}
          <div className="p-4 bg-slate-50/80 rounded-xl border border-slate-200/70 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px] text-blue-600">
                  data_thresholding
                </span>
                <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Extracted Benchmark Criteria
                </span>
              </div>
              <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-100/70 px-2.5 py-0.5 rounded-full border border-emerald-200">
                spaCy + EntityRuler Taxonomy
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-12 gap-4 items-start">
              {/* Threshold Tenure */}
              <div className="sm:col-span-4 flex flex-col gap-1.5">
                <label className="text-[11px] uppercase tracking-wider text-slate-600 font-bold">
                  Minimum Experience (YoE)
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    max="20"
                    value={expYears}
                    onChange={(e) => setExpYears(e.target.value)}
                    className="w-20 h-9 px-2.5 bg-white rounded-lg font-mono text-sm font-bold text-slate-900 border border-slate-300 focus:border-blue-500 focus:outline-none shadow-xs text-center"
                  />
                  <span className="text-xs font-semibold text-slate-600">
                    Years Req.
                  </span>
                </div>
                <span className="text-[10px] text-slate-400">Date math calculates non-overlapping tenure</span>
              </div>

              {/* Skills Tags List */}
              <div className="sm:col-span-8 flex flex-col gap-1.5">
                <div className="flex justify-between items-center">
                  <label className="text-[11px] uppercase tracking-wider text-slate-600 font-bold">
                    Required Technical Skills ({skills.length} Active)
                  </label>
                  <span className="text-[10px] text-slate-400 font-medium">Auto-Normalized</span>
                </div>

                <div className="flex flex-wrap gap-1.5 min-h-[38px] items-center p-2 bg-white rounded-xl border border-slate-200 shadow-2xs">
                  {skills.length === 0 ? (
                    <span className="text-xs text-slate-400 italic py-1">
                      No skills added yet. Paste JD text or click "+ Add Skill" below.
                    </span>
                  ) : (
                    skills.map((skill) => (
                      <span
                        key={skill}
                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-blue-50 text-blue-800 text-xs font-medium border border-blue-100 shadow-2xs hover:bg-blue-100 transition-colors"
                      >
                        <span>{skill}</span>
                        <button
                          type="button"
                          onClick={() => handleRemoveSkill(skill)}
                          className="text-blue-400 hover:text-red-600 font-bold leading-none cursor-pointer"
                          title={`Remove ${skill}`}
                        >
                          ×
                        </button>
                      </span>
                    ))
                  )}

                  {showAddSkill ? (
                    <form onSubmit={handleAddSkill} className="inline-flex items-center gap-1.5">
                      <input
                        type="text"
                        autoFocus
                        placeholder="e.g. Python, Docker..."
                        value={newSkillInput}
                        onChange={(e) => setNewSkillInput(e.target.value)}
                        className="h-7 px-2 text-xs bg-white rounded-md border border-blue-500 text-slate-900 focus:outline-none"
                      />
                      <button
                        type="submit"
                        className="text-xs px-2 py-1 rounded-md bg-blue-600 text-white font-medium hover:bg-blue-700 cursor-pointer"
                      >
                        Add
                      </button>
                      <button
                        type="button"
                        onClick={() => setShowAddSkill(false)}
                        className="text-xs text-slate-500 hover:text-slate-800 cursor-pointer"
                      >
                        Cancel
                      </button>
                    </form>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setShowAddSkill(true)}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs font-medium transition-all cursor-pointer"
                    >
                      <span className="material-symbols-outlined text-[14px]">add</span>
                      <span>Add Skill</span>
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Assurance Footer String */}
            <div className="flex items-center justify-between text-slate-500 font-mono text-[11px] pt-1.5 border-t border-slate-200/60">
              <div className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[14px] text-slate-400">
                  memory
                </span>
                <span>
                  Deterministic matching across 303 canonical technical competencies
                </span>
              </div>
              <span className="text-blue-700 font-semibold">Zero Hallucinations</span>
            </div>
          </div>
        </div>

        {/* Module 2: Candidate Resume Batch Upload Card (5 Columns) */}
        <div className="lg:col-span-5 flex flex-col bg-white rounded-2xl p-6 border border-slate-200/90 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.06)] hover:shadow-[0_8px_30px_-6px_rgba(0,0,0,0.09)] transition-all duration-300">
          {/* Module Header */}
          <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-100">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-700 flex items-center justify-center border border-indigo-100">
                <span className="material-symbols-outlined text-[18px]">folder_zip</span>
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-900 leading-tight">
                  Upload Candidate Resumes
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Select your own original CVs (PDF, DOCX, TXT)
                </p>
              </div>
            </div>
            <span className="font-mono text-xs px-2.5 py-1 rounded-full bg-slate-100 text-slate-800 font-bold border border-slate-200">
              {queuedFiles.length} READY
            </span>
          </div>

          {/* Dropzone Container */}
          <div
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            className={`h-40 w-full rounded-xl flex flex-col items-center justify-center p-4 cursor-pointer transition-all duration-200 text-center mb-4 group relative overflow-hidden border-2 border-dashed ${
              isDragging
                ? 'bg-blue-50/70 border-blue-500 shadow-inner'
                : 'bg-slate-50/70 border-slate-300 hover:bg-blue-50/40 hover:border-blue-400'
            }`}
          >
            <div className="w-11 h-11 rounded-full bg-white flex items-center justify-center text-blue-600 mb-2 group-hover:scale-110 transition-transform shadow-sm border border-slate-100">
              <span className="material-symbols-outlined text-[24px]">cloud_upload</span>
            </div>
            <p className="text-sm text-slate-800 font-semibold">
              Drop your original candidate CVs here, or{' '}
              <span className="text-blue-600 underline underline-offset-2">browse files</span>
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Supports 10–50+ PDF, DOCX, TXT files simultaneously
            </p>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.txt"
              className="sr-only"
              onChange={handleFileSelect}
            />
          </div>

          {/* Ingestion Stats Overview Bar */}
          <div className="flex items-center justify-between px-3.5 py-2.5 bg-slate-50 rounded-xl mb-3 font-mono text-xs text-slate-600 border border-slate-200/60">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${queuedFiles.length > 0 ? 'bg-emerald-500 animate-pulse' : 'bg-slate-300'}`}></span>
              <span className="text-slate-900 font-semibold">
                {queuedFiles.length} Resumes Staged
              </span>
            </div>
            <div>Total Size: {totalPayloadMB} MB</div>
          </div>

          {/* Queued Candidate Files List (Scrollable Area) */}
          <div className="flex flex-col gap-1.5 max-h-[260px] overflow-y-auto pr-1 mb-5">
            {queuedFiles.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-xs bg-slate-50/60 rounded-xl border border-dashed border-slate-200">
                No resumes staged yet. Drop candidate PDF/DOCX files here to evaluate against this role benchmark.
              </div>
            ) : (
              queuedFiles.map((file, idx) => {
                const isPdf = file.name.toLowerCase().endsWith('.pdf');
                return (
                  <div
                    key={`${file.name}-${idx}`}
                    className="flex items-center justify-between px-3 py-2 rounded-xl bg-white hover:bg-slate-50 transition-colors text-slate-800 border border-slate-200 shadow-2xs card-hover"
                  >
                    <div className="flex items-center gap-2.5 min-w-0 pr-2">
                      <span
                        className={`material-symbols-outlined text-[20px] shrink-0 ${
                          isPdf ? 'text-red-600' : 'text-blue-600'
                        }`}
                      >
                        {isPdf ? 'picture_as_pdf' : 'description'}
                      </span>
                      <span className="text-xs font-semibold truncate text-slate-800">
                        {file.name}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <span className="font-mono text-[11px] text-slate-500">
                        {formatFileSize(file.size)}
                      </span>
                      <div className="flex items-center gap-1 font-mono text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
                        <span className="material-symbols-outlined text-[12px] text-emerald-600">
                          check_circle
                        </span>
                        <span>Ready</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemoveFile(idx)}
                        className="text-slate-400 hover:text-red-600 text-xs font-bold px-1 transition-colors cursor-pointer"
                        title="Remove file"
                      >
                        ×
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Primary Execution CTA */}
          <button
            type="button"
            onClick={handleSubmitEvaluation}
            disabled={isEvaluating}
            className="w-full h-12 bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 hover:from-blue-700 hover:to-indigo-800 text-white font-semibold rounded-xl flex items-center justify-center gap-2 transition-all cursor-pointer shadow-md hover:shadow-lg hover:shadow-blue-500/25 active:scale-[0.99] disabled:opacity-60 disabled:cursor-not-allowed btn-press"
          >
            {isEvaluating ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span className="text-sm font-semibold">Running Local Semantic Screening...</span>
              </>
            ) : (
              <>
                <span className="text-sm font-semibold">
                  {queuedFiles.length > 0
                    ? `Evaluate & Rank ${queuedFiles.length} Candidate${queuedFiles.length > 1 ? 's' : ''}`
                    : 'Evaluate & Rank Candidates'}
                </span>
                <span className="material-symbols-outlined text-[20px]">arrow_forward</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Supplementary Trust & Privacy Bar */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-4 rounded-2xl bg-white text-slate-600 text-xs border border-slate-200/90 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center shrink-0 border border-blue-100">
            <span className="material-symbols-outlined text-[18px]">verified_user</span>
          </div>
          <span>
            Scorume operates 100% locally on your machine. No resume text, contact details, or candidate data is ever transmitted to external APIs or cloud LLMs.
          </span>
        </div>
        <div className="flex items-center gap-4 shrink-0 font-mono text-[11px]">
          <span>
            Inference: <strong className="text-slate-900 font-bold">~1.4s / cohort</strong>
          </span>
          <span>•</span>
          <span>
            Compliance: <strong className="text-emerald-700 font-bold">DPDP Act (India) Private</strong>
          </span>
        </div>
      </div>
    </div>
  );
}
