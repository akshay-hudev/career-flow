import axios from 'axios'

const api = axios.create({
  baseURL: 'https://career-platform-rtdk.onrender.com/',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const message = err.response?.data?.detail || 'Something went wrong.'
    return Promise.reject(new Error(message))
  }
)

// ── Users ────────────────────────────────────────────────────────────────────
export const createUser = (data) => api.post('/users/', data)
export const getUser = (userId) => api.get(`/users/${userId}`)

// ── Resume ───────────────────────────────────────────────────────────────────
export const uploadResume = (file, userId) => {
  const form = new FormData()
  form.append('file', file)
  return api.post(`/resume/upload?user_id=${userId}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
export const listResumes = (userId) => api.get(`/resume/${userId}/list`)
export const getResume = (resumeId) => api.get(`/resume/${resumeId}`)
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
export const scoreMatch = (resumeId, jobDescriptions) =>
  api.post('/match/score', { resume_id: resumeId, job_descriptions: jobDescriptions })
export const getCareerAdvice = (resumeId, jobTitle, jobDescription) =>
  api.post('/match/advice', { resume_id: resumeId, job_title: jobTitle, job_description: jobDescription })

// ── Agent ────────────────────────────────────────────────────────────────────
export const runCareerAgent = (file, jobQuery, location = 'India') => {
  const form = new FormData()
  form.append('file', file)
  return api.post(
    `/agent/run?job_query=${encodeURIComponent(jobQuery)}&location=${encodeURIComponent(location)}`,
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  )
}

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

export default api
