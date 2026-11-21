import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar.jsx';
import Footer from './components/Footer.jsx';
import CampaignSetupView from './components/CampaignSetupView.jsx';
import CandidateRankingsView from './components/CandidateRankingsView.jsx';
import CandidateDeepDiveDrawer from './components/CandidateDeepDiveDrawer.jsx';
import EvaluationHistoryView from './components/EvaluationHistoryView.jsx';
import RoleMatcherFinderView from './components/RoleMatcherFinderView.jsx';
import {
  fetchSystemHealth,
  parseJobDescription,
  uploadAndEvaluateBatch,
  loadSampleDemoDataset,
  fetchJobDescriptions,
  fetchRankedCandidates,
  fetchCandidateDetail,
} from './api/client.js';

export default function App() {
  const [activeTab, setActiveTab] = useState('benchmark-config');
  const [healthInfo, setHealthInfo] = useState(null);
  const [activeJd, setActiveJd] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [isLoadingDemo, setIsLoadingDemo] = useState(false);
  const [showHelpDocs, setShowHelpDocs] = useState(false);
  const [notification, setNotification] = useState(null);

  const showNotification = (msg, type = 'success') => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 4000);
  };

  // Initial load: set page title/favicon, fetch health status, list recent JDs and auto-select latest evaluated JD
  useEffect(() => {
    document.title = 'Scorume (evaluation engine)';
    const favicon = document.querySelector("link[rel*='icon']");
    if (favicon) {
      favicon.href = '/logo.png';
    }

    fetchSystemHealth()
      .then((data) => setHealthInfo(data))
      .catch(() => setHealthInfo({ status: 'offline' }));

    // Auto-load latest active hiring drive and its evaluated candidates
    fetchJobDescriptions()
      .then(async (jds) => {
        if (jds && jds.length > 0) {
          const latestJd = jds[0];
          setActiveJd(latestJd);
          try {
            const evalResponse = await fetchRankedCandidates(latestJd.id);
            if (evalResponse.candidates?.length > 0) {
              setCandidates(evalResponse.candidates);
            }
          } catch (e) {
            console.warn('Could not fetch existing candidates:', e);
          }
        }
      })
      .catch((err) => console.warn('Could not load JDs:', err));
  }, []);

  // Handle running semantic evaluation from Screen 1
  const handleRunEvaluation = async ({ rawText, file, title, minExperienceYears, requiredSkills, files }) => {
    setIsEvaluating(true);
    try {
      // 1. Parse / persist Job Description
      const parsedJd = await parseJobDescription({
        rawText,
        file,
        title,
        minExperienceYears,
        skills: requiredSkills,
      });
      setActiveJd(parsedJd);

      // 2. Upload and evaluate candidate files if provided
      if (files && files.length > 0) {
        const batchResponse = await uploadAndEvaluateBatch(parsedJd.id, files);
        setCandidates(batchResponse.candidates || []);
        showNotification(`Successfully evaluated ${batchResponse.total_candidates} candidates for '${parsedJd.title}'!`);
        setActiveTab('candidate-rankings');
      } else {
        // If no files uploaded, check if candidates already exist or navigate to rankings
        try {
          const evalResponse = await fetchRankedCandidates(parsedJd.id);
          setCandidates(evalResponse.candidates || []);
        } catch {
          setCandidates([]);
        }
        showNotification(`Benchmark '${parsedJd.title}' criteria updated successfully.`);
        setActiveTab('candidate-rankings');
      }
    } catch (err) {
      console.error('Evaluation run failed:', err);
      showNotification(
        `Evaluation failed: ${err.response?.data?.detail || err.message}`,
        'error'
      );
    } finally {
      setIsEvaluating(false);
    }
  };

  // Handle one-click sample demo load
  const handleLoadSampleDemo = async () => {
    setIsLoadingDemo(true);
    try {
      const demoResponse = await loadSampleDemoDataset();
      setActiveJd({
        id: demoResponse.jd_id,
        title: demoResponse.jd_title,
        required_skills: demoResponse.jd_required_skills,
        min_experience_years: demoResponse.jd_min_experience_years,
      });
      setCandidates(demoResponse.candidates || []);
      showNotification(
        `Ingested 12 synthetic test resumes for '${demoResponse.jd_title}'!`
      );
      setActiveTab('candidate-rankings');
    } catch (err) {
      console.error('Sample demo load failed:', err);
      showNotification('Could not load sample dataset. Please check backend.', 'error');
    } finally {
      setIsLoadingDemo(false);
    }
  };

  // When selecting a candidate to inspect in the deep-dive drawer
  const handleSelectCandidate = async (candidate) => {
    setSelectedCandidate(candidate);
    // Fetch deeper detail if evaluation ID exists
    try {
      const detail = await fetchCandidateDetail(candidate.id);
      setSelectedCandidate((prev) => ({
        ...prev,
        ...detail,
        dynamicRank: candidate.dynamicRank || candidate.rank,
        recomputedScore: candidate.recomputedScore ?? candidate.overall_score,
      }));
    } catch (err) {
      console.warn('Could not fetch extra candidate detail:', err);
    }
  };

  // When user selects a campaign run from history
  const handleSelectCampaign = ({ jd, candidates: campCandidates }) => {
    setActiveJd(jd);
    setCandidates(campCandidates || []);
    setActiveTab('candidate-rankings');
    showNotification(`Loaded historical run for '${jd.title}'.`);
  };

  return (
    <div className="min-h-screen bg-background font-sans text-on-surface flex flex-col selection:bg-secondary selection:text-white">
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        hasEvaluations={candidates.length > 0}
        healthInfo={healthInfo}
        onOpenHelp={() => setShowHelpDocs(true)}
      />

      {/* Toast Notification */}
      {notification && (
        <div
          className={`fixed bottom-6 right-6 z-50 px-4 py-2.5 rounded-lg shadow-lg flex items-center gap-2 font-data-mono-sm text-data-mono-sm animate-fadeIn ${
            notification.type === 'error'
              ? 'bg-error text-on-error'
              : 'bg-primary-container text-on-primary'
          }`}
        >
          <span className="material-symbols-outlined text-[18px]">
            {notification.type === 'error' ? 'error' : 'check_circle'}
          </span>
          <span>{notification.msg}</span>
        </div>
      )}

      {/* Main Page Views */}
      <main className="w-full pt-14 bg-background flex-1 flex flex-col">
        {activeTab === 'benchmark-config' && (
          <CampaignSetupView
            activeJd={activeJd}
            setActiveJd={setActiveJd}
            onRunEvaluation={handleRunEvaluation}
            isEvaluating={isEvaluating}
            onLoadSampleDemo={handleLoadSampleDemo}
            isLoadingDemo={isLoadingDemo}
          />
        )}

        {activeTab === 'candidate-rankings' && (
          <CandidateRankingsView
            activeJd={activeJd}
            candidates={candidates}
            onSelectCandidate={handleSelectCandidate}
            onNavigateToSetup={() => setActiveTab('benchmark-config')}
          />
        )}

        {activeTab === 'role-matcher-finder' && (
          <RoleMatcherFinderView
            activeJd={activeJd}
            onSelectCandidate={handleSelectCandidate}
          />
        )}

        {activeTab === 'evaluation-history' && (
          <EvaluationHistoryView
            onSelectCampaign={handleSelectCampaign}
            onNavigateToSetup={() => setActiveTab('benchmark-config')}
          />
        )}
      </main>

      {/* Candidate Deep-Dive Drawer (Module 5) */}
      <CandidateDeepDiveDrawer
        isOpen={Boolean(selectedCandidate)}
        candidate={selectedCandidate}
        activeJd={activeJd}
        onClose={() => setSelectedCandidate(null)}
      />

      {/* Help Docs Modal */}
      {showHelpDocs && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-primary-container/40 backdrop-blur-[2px]">
          <div className="bg-surface-container-lowest max-w-lg w-full rounded-xl shadow-xl p-6 border border-surface-container-high/60 flex flex-col gap-4 animate-fadeIn">
            <div className="flex items-center justify-between border-b border-surface-container-high pb-3">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary">help</span>
                <h3 className="font-headline-sm text-headline-sm font-semibold">
                  Scorume Engine Architecture
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowHelpDocs(false)}
                className="text-on-surface-variant hover:text-on-surface"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <div className="font-body-sm text-body-sm text-on-surface-variant space-y-3">
              <p>
                <strong className="text-on-surface">100% Local Processing:</strong> All documents,
                embeddings, and inferences run locally on-device. No candidate data ever leaves the
                private network environment.
              </p>
              <p>
                <strong className="text-on-surface">Deterministic AST Parsing:</strong> Uses spaCy
                EntityRuler pattern matching against 303 canonical engineering competencies and 1,688
                aliases for zero-hallucination skill extraction.
              </p>
              <p>
                <strong className="text-on-surface">Vector Cosine Proximity:</strong> Dense sentence
                embeddings generated using <code className="bg-surface-container px-1 rounded">all-MiniLM-L6-v2</code>{' '}
                measure conceptual contextual alignment between work experience and job responsibilities.
              </p>
              <p>
                <strong className="text-on-surface">Explainable AI (XAI):</strong> Transparent point
                attributions (+47 pts core skills, +20 pts tenure, +21 pts semantic relevance) provide
                an auditable record for hiring compliance.
              </p>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                type="button"
                onClick={() => setShowHelpDocs(false)}
                className="px-4 py-2 bg-primary text-on-primary rounded-lg text-xs font-medium hover:bg-primary-container"
              >
                Close Documentation
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Global Footer */}
      <Footer />
    </div>
  );
}
