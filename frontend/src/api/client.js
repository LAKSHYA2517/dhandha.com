import { useAuthStore } from '../store/authStore'

const API_BASE = '/api'

async function request(method, path, { body, isFormData } = {}) {
  const token = useAuthStore.getState().token
  const headers = {}
  if (!isFormData) headers['Content-Type'] = 'application/json'
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(API_BASE + path, {
    method,
    headers,
    body: isFormData ? body : body ? JSON.stringify(body) : undefined,
  })

  if (res.status === 401) {
    useAuthStore.getState().logout()
  }

  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(data.detail || data.message || `HTTP ${res.status}`)
  }
  return data
}

export const api = {
  get: (path) => request('GET', path),
  post: (path, body) => request('POST', path, { body }),
  put: (path, body) => request('PUT', path, { body }),
  delete: (path) => request('DELETE', path),
  upload: (path, formData) => request('POST', path, { body: formData, isFormData: true }),
}
