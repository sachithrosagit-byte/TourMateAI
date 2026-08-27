// Add/edit attraction form modal for the admin Attractions panel.
// Category options mirror the backend's known set (routes/users.py
// INTEREST_OPTIONS) so user interests keep mapping onto categories.
import { useState } from 'react'
import {
  createAttraction,
  updateAttraction,
  uploadAttractionImage,
} from '../../services/admin'

// Mirrors the backend's ALLOWED_IMAGE_EXTENSIONS (routes/admin.py).
const IMAGE_ACCEPT = 'image/jpeg,image/png,image/webp'

const CATEGORY_OPTIONS = [
  'Heritage',
  'Religious',
  'Historical',
  'Scenic',
  'Wildlife',
  'Hiking',
  'Hill Country',
  'Beach',
  'Nature',
]

/** Parse an optional coordinate input. Returns {value|null} or {error}. */
function parseCoord(raw, label, low, high) {
  const text = raw.trim()
  if (!text) return { value: null }
  const number = Number(text)
  if (Number.isNaN(number)) return { error: `${label} must be a number.` }
  if (number < low || number > high) {
    return { error: `${label} must be between ${low} and ${high}.` }
  }
  return { value: number }
}

export default function AttractionModal({ attraction, onClose, onSaved }) {
  const isEdit = Boolean(attraction)
  const [name, setName] = useState(attraction?.name || '')
  const [category, setCategory] = useState(attraction?.category || '')
  const [description, setDescription] = useState(attraction?.description || '')
  const [imageUrl, setImageUrl] = useState(attraction?.image_url || '')
  const [latitude, setLatitude] = useState(
    attraction?.latitude != null ? String(attraction.latitude) : ''
  )
  const [longitude, setLongitude] = useState(
    attraction?.longitude != null ? String(attraction.longitude) : ''
  )
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [uploading, setUploading] = useState(false)

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0]
    event.target.value = '' // allow re-picking the same file later
    if (!file) return

    setUploading(true)
    setError(null)
    try {
      const url = await uploadAttractionImage(file)
      setImageUrl(url)
    } catch (err) {
      setError(
        err?.response?.data?.error ||
          'Could not upload the image. Please try again.'
      )
    } finally {
      setUploading(false)
    }
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (submitting) return

    if (!name.trim()) {
      setError('Name is required.')
      return
    }
    const lat = parseCoord(latitude, 'Latitude', -90, 90)
    if (lat.error) return setError(lat.error)
    const lng = parseCoord(longitude, 'Longitude', -180, 180)
    if (lng.error) return setError(lng.error)

    setSubmitting(true)
    setError(null)
    const payload = {
      name: name.trim(),
      category: category || null,
      description: description.trim() || null,
      image_url: imageUrl.trim() || null,
      latitude: lat.value,
      longitude: lng.value,
    }
    try {
      const saved = isEdit
        ? await updateAttraction(attraction.id, payload)
        : await createAttraction(payload)
      onSaved(saved)
    } catch (err) {
      setError(
        err?.response?.data?.error ||
          'Could not save the attraction. Please try again.'
      )
      setSubmitting(false)
    }
  }

  return (
    <div className="adm-modal-backdrop" onClick={onClose}>
      <div
        className="adm-modal card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="attraction-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="adm-modal-head">
          <h2 id="attraction-modal-title">
            {isEdit ? 'Edit attraction' : 'Add attraction'}
          </h2>
          <button
            type="button"
            className="adm-modal-close"
            onClick={onClose}
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label className="label" htmlFor="attr-name">
              Name
            </label>
            <input
              id="attr-name"
              className="input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Sigiriya Rock Fortress"
              maxLength={200}
              autoFocus
            />
          </div>

          <div className="field">
            <label className="label" htmlFor="attr-category">
              Category
            </label>
            <select
              id="attr-category"
              className="input"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="">No category</option>
              {CATEGORY_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            <p className="hint">
              Categories power traveler interests and recommendations.
            </p>
          </div>

          <div className="field">
            <label className="label" htmlFor="attr-description">
              Description
            </label>
            <textarea
              id="attr-description"
              className="input"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="A short blurb travelers (and the chatbot) will see."
            />
          </div>

          <div className="adm-field-row">
            <div className="field">
              <label className="label" htmlFor="attr-lat">
                Latitude
              </label>
              <input
                id="attr-lat"
                className="input"
                value={latitude}
                onChange={(e) => setLatitude(e.target.value)}
                placeholder="7.9570"
                inputMode="decimal"
              />
            </div>
            <div className="field">
              <label className="label" htmlFor="attr-lng">
                Longitude
              </label>
              <input
                id="attr-lng"
                className="input"
                value={longitude}
                onChange={(e) => setLongitude(e.target.value)}
                placeholder="80.7603"
                inputMode="decimal"
              />
            </div>
          </div>

          <div className="field">
            <label className="label" htmlFor="attr-image-file">
              Photo
            </label>
            <div className="adm-image-upload">
              {imageUrl && (
                <img
                  className="adm-image-preview"
                  src={imageUrl}
                  alt=""
                />
              )}
              <input
                id="attr-image-file"
                className="input"
                type="file"
                accept={IMAGE_ACCEPT}
                onChange={handleFileChange}
                disabled={uploading}
              />
            </div>
            <p className="hint">
              {uploading
                ? 'Uploading…'
                : 'Choose a photo from this device (PC or mobile storage).'}
            </p>
          </div>

          {error && (
            <div className="alert alert-error" role="alert">
              {error}
            </div>
          )}

          <div className="adm-modal-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting || uploading}
            >
              {submitting
                ? 'Saving…'
                : isEdit
                  ? 'Save changes'
                  : 'Add attraction'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
