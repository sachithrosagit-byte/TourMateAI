// Shared Axios instance for talking to the Flask backend.
//
// A request interceptor attaches the current user's Firebase ID token as
// `Authorization: Bearer <token>` to EVERY outgoing request, so callers never have
// to think about auth. `getIdToken()` returns a cached token and only hits the
// network when the token is close to expiry, so this is cheap to call per-request.

import axios from 'axios'
import { auth } from '../firebase'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api',
})

api.interceptors.request.use(async (config) => {
  const user = auth.currentUser
  if (user) {
    const token = await user.getIdToken()
    config.headers.Authorization = `Bearer ${token}`
  }
  
  // Attach current language to all GET requests
  const lang = localStorage.getItem('i18nextLng') || 'en'
  if (config.method === 'get') {
    config.params = { ...config.params, lang }
  }
  
  return config
})

export default api
