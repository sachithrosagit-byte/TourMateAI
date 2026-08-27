// Admin portal API calls (see backend/app/routes/admin.py for the contracts).
// Every endpoint 403s for non-admins; the Admin page gates on user.role first.

import api from './api'

// Stored attraction photos are served by the Flask backend, not the Vite dev
// server, so the relative path the upload endpoint returns needs the API
// origin prepended before it's usable as an <img src> / saved as image_url.
const API_ORIGIN = new URL(
  api.defaults.baseURL,
  window.location.origin
).origin

export async function fetchAnalytics() {
  const { data } = await api.get('/admin/analytics')
  return data // { totals: {...}, most_viewed: [...] }
}

export async function fetchAdminUsers() {
  const { data } = await api.get('/admin/users')
  return data.users // [{ id, name, email, role, interactions_count, ... }]
}

export async function fetchAdminAttractions() {
  const { data } = await api.get('/admin/attractions')
  return data.attractions // full rows + review_count
}

export async function createAttraction(fields) {
  const { data } = await api.post('/admin/attractions', fields)
  return data.attraction
}

export async function updateAttraction(id, fields) {
  const { data } = await api.put(`/admin/attractions/${id}`, fields)
  return data.attraction
}

export async function deleteAttraction(id) {
  const { data } = await api.delete(`/admin/attractions/${id}`)
  return data // { deleted: id }
}

/** Upload a photo (from the admin's PC or mobile device storage) and return
 *  its absolute URL, ready to store as an attraction's image_url. */
export async function uploadAttractionImage(file) {
  const form = new FormData()
  form.append('image', file)
  const { data } = await api.post('/admin/attractions/upload-image', form)
  return `${API_ORIGIN}${data.image_url}`
}
