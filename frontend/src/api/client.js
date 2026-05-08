import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE || ''
export const api = axios.create({ baseURL, timeout: 120000 })

// Inject bearer token if logged in
api.interceptors.request.use((cfg) => {
  const t = localStorage.getItem('auth_token')
  if (t) cfg.headers.Authorization = `Bearer ${t}`
  return cfg
})

// On 401, clear token so the app falls back to login
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.response?.status === 401) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user')
      // soft reload to show login screen
      if (location.pathname !== '/login') window.dispatchEvent(new Event('auth:logout'))
    }
    return Promise.reject(err)
  }
)

export const ExcelAPI = {
  upload: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post('/api/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } }).then(r => r.data)
  },
  workbook: () => api.get('/api/workbook').then(r => r.data),
  clear: () => api.delete('/api/workbook').then(r => r.data),
  meta: (sheet) => api.get(`/api/sheets/${encodeURIComponent(sheet)}/meta`).then(r => r.data),
  summary: (sheet) => api.get(`/api/sheets/${encodeURIComponent(sheet)}/summary`).then(r => r.data),
  data: (sheet, query) => api.post(`/api/sheets/${encodeURIComponent(sheet)}/data`, query).then(r => r.data),
}

export const ChatAPI = {
  send: (message, sheet, history) => api.post('/api/chat', { message, sheet, history }).then(r => r.data),
}

export const InsightsAPI = {
  overview: () => api.get('/api/insights/overview').then(r => r.data),
  mismatches: () => api.get('/api/insights/mismatches').then(r => r.data),
}

export const AuthAPI = {
  config: () => api.get('/api/auth/config').then(r => r.data),
  login: (username, password) => api.post('/api/auth/login', { username, password }).then(r => r.data),
  me: () => api.get('/api/auth/me').then(r => r.data),
}
