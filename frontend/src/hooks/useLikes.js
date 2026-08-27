// Liked-attraction state for the heart buttons. Likes are persisted locally
// (so hearts survive a refresh) and each NEW like is logged to
// POST /api/interactions as recommender training signal. Un-liking is local
// only — the backend keeps the original event, which is fine for implicit
// feedback data.

import { useState } from 'react'
import { logInteraction } from '../services/attractions'

const STORAGE_KEY = 'tm-liked-attractions'

function readLiked() {
  try {
    const raw = JSON.parse(localStorage.getItem(STORAGE_KEY))
    return new Set(Array.isArray(raw) ? raw : [])
  } catch {
    return new Set()
  }
}

export default function useLikes() {
  const [liked, setLiked] = useState(readLiked)

  const toggleLike = (attractionId) => {
    const next = new Set(liked)
    if (next.has(attractionId)) {
      next.delete(attractionId)
    } else {
      next.add(attractionId)
      logInteraction(attractionId, 'like')
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...next]))
    setLiked(next)
  }

  return { liked, toggleLike }
}
