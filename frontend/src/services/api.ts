import type { DocumentItem, HistoryItem, SearchResult, Tokens, User } from '../types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API = `${API_URL}/api/v1`

let accessToken = localStorage.getItem('access_token') || ''
let refreshToken = localStorage.getItem('refresh_token') || ''

function saveTokens(tokens: Tokens) {
  accessToken = tokens.access_token
  refreshToken = tokens.refresh_token
  localStorage.setItem('access_token', accessToken)
  localStorage.setItem('refresh_token', refreshToken)
}

export function hasSession() { return Boolean(accessToken && refreshToken) }
export function clearSession() {
  accessToken = ''; refreshToken = ''
  localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token')
  localStorage.removeItem('user_email')
}

async function parseError(response: Response) {
  try {
    const body = await response.json()
    if (Array.isArray(body.detail)) return body.detail.map((x: { msg: string }) => x.msg).join('. ')
    return body.detail || 'Не удалось выполнить запрос'
  } catch { return `Ошибка сервера (${response.status})` }
}

async function raw(path: string, options: RequestInit = {}, retry = true): Promise<Response> {
  const headers = new Headers(options.headers)
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  const response = await fetch(`${API}${path}`, { ...options, headers })
  if (response.status === 401 && retry && refreshToken) {
    try { await auth.refresh(); return raw(path, options, false) } catch { clearSession(); window.dispatchEvent(new Event('session-expired')) }
  }
  if (!response.ok) throw new Error(await parseError(response))
  return response
}

async function json<T>(path: string, options?: RequestInit, retry = true): Promise<T> {
  return (await raw(path, options, retry)).json() as Promise<T>
}

export const auth = {
  async register(email: string, password: string): Promise<User> {
    const data = await json<{ user: User }>('/auth/register', { method: 'POST', body: JSON.stringify({ email, password }) })
    return data.user
  },
  async login(email: string, password: string) {
    const tokens = await json<Tokens>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) })
    saveTokens(tokens)
    localStorage.setItem('user_email', email)
  },
  async refresh() {
    const tokens = await json<Tokens>('/auth/refresh', { method: 'POST', body: JSON.stringify({ refresh_token: refreshToken }) }, false)
    saveTokens(tokens)
  },
  async logout() {
    try { await json('/auth/logout', { method: 'POST', body: JSON.stringify({ refresh_token: refreshToken }) }) } finally { clearSession() }
  },
}

export const documentsApi = {
  list: (limit = 100, offset = 0) => json<{ items: DocumentItem[]; total: number }>(`/documents?limit=${limit}&offset=${offset}`),
  get: (id: string) => json<DocumentItem>(`/documents/${id}`),
  delete: (id: string) => json<{ deleted: boolean }>(`/documents/${id}`, { method: 'DELETE' }),
  upload(file: File, onProgress: (value: number) => void): Promise<DocumentItem> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.open('POST', `${API}/documents/upload`)
      xhr.setRequestHeader('Authorization', `Bearer ${accessToken}`)
      xhr.upload.onprogress = e => e.lengthComputable && onProgress(Math.round(e.loaded / e.total * 100))
      xhr.onload = () => {
        let body: { document?: DocumentItem; detail?: string } = {}
        try { body = JSON.parse(xhr.responseText) } catch { /* response is not JSON */ }
        if (xhr.status >= 200 && xhr.status < 300 && body.document) resolve(body.document)
        else reject(new Error(typeof body.detail === 'string' ? body.detail : `Ошибка загрузки (${xhr.status})`))
      }
      xhr.onerror = () => reject(new Error('Нет соединения с сервером'))
      const data = new FormData(); data.append('file', file); xhr.send(data)
    })
  },
}

export const searchApi = {
  search: (query: string, documentId: string, offset: number) => {
    const params = new URLSearchParams({ q: query, limit: '10', offset: String(offset) })
    if (documentId) params.set('document_id', documentId)
    return json<{ query: string; document_id: string | null; items: SearchResult[]; total: number; limit: number; offset: number }>(`/search?${params}`)
  },
}

export const historyApi = {
  list: (limit = 100, offset = 0) => json<{ items: HistoryItem[]; total: number }>(`/history?limit=${limit}&offset=${offset}`),
  delete: (id: string) => json<{ deleted: boolean }>(`/history/${id}`, { method: 'DELETE' }),
  clear: () => json<{ deleted_count: number }>('/history', { method: 'DELETE' }),
}

export async function healthCheck() {
  const response = await fetch(`${API_URL}/health`)
  return response.ok
}
