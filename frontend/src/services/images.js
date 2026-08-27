// Image recognition API calls (see backend/app/routes/images.py for the
// contracts these mirror). The backend expands the matched attraction id into
// a full attraction object, so everything here is ready to render.

import api from './api'

// Stored uploads are served by the Flask backend, not the Vite dev server, so
// relative paths like "/api/images/uploads/<file>" need the API origin.
const API_ORIGIN = new URL(
  api.defaults.baseURL,
  window.location.origin
).origin

export function uploadedImageUrl(path) {
  return path ? `${API_ORIGIN}${path}` : path
}

export async function recognizeImage(file) {
  const form = new FormData()
  form.append('image', file)
  const { data } = await api.post('/images/recognize', form)
  return data // { id, image_url, identified_name, confidence, description, matched_attraction, created_at }
}

export async function fetchUploadHistory({ limit = 20 } = {}) {
  const { data } = await api.get('/images', { params: { limit } })
  return data.images // newest first, same shape as recognizeImage()
}
