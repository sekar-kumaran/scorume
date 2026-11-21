/**
 * Axios API Client for the AI-Based Resume Matching & Candidate Ranking Engine.
 * Communicates with the FastAPI backend (`http://localhost:8000` or `/api` proxy).
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000,
});

/**
 * System Health & Model Status
 */
export async function fetchSystemHealth() {
  const { data } = await apiClient.get('/api/health');
  return data;
}

/**
 * Module 1: Parse a Job Description from raw text or uploaded PDF/DOCX file.
 */
export async function parseJobDescription({ rawText, file, title, minExperienceYears, skills }) {
  const formData = new FormData();
  if (file) {
    formData.append('file', file);
  }
  if (rawText && rawText.trim()) {
    formData.append('raw_text', rawText.trim());
  }
  if (title && title.trim()) {
    formData.append('title', title.trim());
  }
  if (minExperienceYears !== undefined && minExperienceYears !== null && minExperienceYears !== '') {
    formData.append('min_experience_years', String(minExperienceYears));
  }
  if (skills && Array.isArray(skills) && skills.length > 0) {
    formData.append('skills', JSON.stringify(skills));
  }

  const { data } = await apiClient.post('/api/jd/parse', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

/**
 * Preview extracted title, skills, and experience from JD text without saving.
 */
export async function previewJdExtraction(rawText) {
  const { data } = await apiClient.post('/api/jd/extract-preview', { raw_text: rawText });
  return data;
}

/**
 * Module 1: Update extracted JD required skills or minimum experience benchmark.
 */
export async function updateJobDescriptionSkills(jdId, payload) {
  const { data } = await apiClient.put(`/api/jd/${jdId}/skills`, {
    required_skills: payload.required_skills,
    min_experience_years: payload.min_experience_years,
    title: payload.title,
    recalculate_candidates: payload.recalculate_candidates ?? true,
  });
  return data;
}

/**
 * Modules 2 & 3: Upload and evaluate a batch of 10-50+ PDF/DOCX resumes against a JD.
 */
export async function uploadAndEvaluateBatch(jdId, files, replaceExisting = true) {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  const { data } = await apiClient.post(
    `/api/evaluations/${jdId}/batch?replace_existing=${replaceExisting}`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
    }
  );
  return data;
}

/**
 * Interactive Manual Resume Entry: Paste or type a candidate resume directly in the browser.
 * @param {string} jdId
 * @param {Object} payload
 * @param {string} [payload.candidate_name]
 * @param {string} [payload.email]
 * @param {string} [payload.phone]
 * @param {string} payload.raw_resume_text
 */
export async function createManualCandidateResume(jdId, payload) {
  const { data } = await apiClient.post(`/api/evaluations/${jdId}/manual`, payload);
  return data;
}

/**
 * Module 4: Fetch all ranked candidates for a specific Job Description.
 */
export async function fetchRankedCandidates(jdId) {
  const { data } = await apiClient.get(`/api/evaluations/${jdId}`);
  return data;
}

/**
 * Module 5: Fetch full deep-dive XAI payload for a single candidate evaluation.
 */
export async function fetchCandidateDetail(evaluationId) {
  const { data } = await apiClient.get(`/api/evaluations/candidate/${evaluationId}`);
  return data;
}

/**
 * Screen 4: Fetch evaluation & campaign history runs with aggregate metrics.
 */
export async function fetchEvaluationHistory() {
  const { data } = await apiClient.get('/api/evaluations/history');
  return data;
}

/**
 * Screen 4: Delete a specific historical campaign run.
 */
export async function deleteCampaignHistoryRun(jdId) {
  const { data } = await apiClient.delete(`/api/evaluations/history/${jdId}`);
  return data;
}

/**
 * Screen 4: Purge all evaluation history for a completely clean slate.
 */
export async function purgeAllEvaluationHistory() {
  const { data } = await apiClient.delete('/api/evaluations/history/purge-all');
  return data;
}

/**
 * Screen 5: Role Matcher - Find candidates from cross-pools matching requisition specs.
 */
export async function findCandidatesForRole(payload) {
  const { data } = await apiClient.post('/api/evaluations/role-matcher/find-candidates', payload);
  return data;
}

/**
 * Screen 5: Role Matcher - Reverse match a candidate against active benchmarks.
 */
export async function reverseMatchCandidate(payload) {
  const { data } = await apiClient.post('/api/evaluations/role-matcher/reverse-match', payload);
  return data;
}

/**
 * Fetch all available Job Description benchmarks.
 */
export async function fetchJobDescriptions() {
  const { data } = await apiClient.get('/api/jd');
  return data;
}

/**
 * Export candidate ranking leaderboard as CSV download.
 */
export function getExportCsvUrl(jdId) {
  return `${API_BASE_URL}/api/evaluations/${jdId}/export-csv`;
}

/**
 * Demo Helper: One-click loader that ingests the sample Full-Stack AI JD and all 12 real-profile resumes.
 */
export async function loadSampleDemoDataset() {
  const { data } = await apiClient.post('/api/demo/load-sample');
  return data;
}

export default apiClient;
