import axios from 'axios'

const api = axios.create({
  baseURL: 'https://career-platform-rtdk.onrender.com/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('career_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('career_token')
      localStorage.removeItem('career_user')
      window.location.href = '/login'
    }
    const message = err.response?.data?.detail || 'Something went wrong.'
    return Promise.reject(new Error(message))
  }
)

// ── Auth ─────────────────────────────────────────────────────────────────────
export const registerUser = (data) => api.post('/auth/register', data)
export const loginUser = (data) => api.post('/auth/login', data)

// ── Users ────────────────────────────────────────────────────────────────────

// ── Resume ───────────────────────────────────────────────────────────────────
export const uploadResume = (file, userId) => {
  const form = new FormData()
  form.append('file', file)
  return api.post(`/resume/upload?user_id=${userId}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
export const listResumes = (userId) => api.get(`/resume/${userId}/list`)
export const deleteResume = (resumeId) => api.delete(`/resume/${resumeId}`)

// ── Jobs ─────────────────────────────────────────────────────────────────────
export const searchJobs = (query, location, results = 20, resumeId = null) => {
  const params = { resume_id: resumeId }
  return api.post('/jobs/search', { query, location, results }, { params })
}
export const saveJob = (jobData, userId) =>
  api.post(`/jobs/save?user_id=${userId}`, jobData)
export const getSavedJobs = (userId, status = null) => {
  const params = status ? { status } : {}
  return api.get(`/jobs/saved/${userId}`, { params })
}
export const updateJobStatus = (jobId, status, notes = null) =>
  api.patch(`/jobs/saved/${jobId}/status`, { status, notes })
export const deleteSavedJob = (jobId) => api.delete(`/jobs/saved/${jobId}`)

// ── Match ────────────────────────────────────────────────────────────────────
export const getCareerAdvice = (resumeId, jobTitle, jobDescription) =>
  api.post('/match/advice', { resume_id: resumeId, job_title: jobTitle, job_description: jobDescription })

// ── Agent ────────────────────────────────────────────────────────────────────

// ── Interview ────────────────────────────────────────────────────────────────
export const generateQuestions = (resumeId, jobTitle, jobDescription, questionType, count) =>
  api.post('/interview/questions', {
    resume_id: resumeId,
    job_title: jobTitle,
    job_description: jobDescription,
    question_type: questionType,
    count,
  })

export const evaluateAnswer = (question, userAnswer, jobTitle, idealFramework) =>
  api.post('/interview/evaluate', {
    question,
    user_answer: userAnswer,
    job_title: jobTitle,
    ideal_answer_framework: idealFramework,
  })

