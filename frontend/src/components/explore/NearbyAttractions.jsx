import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import AttractionCard, { AttractionCardSkeleton } from './AttractionCard'
import useLikes from '../../hooks/useLikes'
import { fetchNearbyAttractions } from '../../services/attractions'
import '../../styles/explore.css'

export default function NearbyAttractions({ attractionId }) {
  const { t, i18n } = useTranslation()
  const [attractions, setAttractions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  const { liked, toggleLike } = useLikes()

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    fetchNearbyAttractions(attractionId)
      .then((data) => {
        if (!cancelled) {
          setAttractions(data)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError(t('detail.attraction.loadError'))
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [attractionId, i18n.language])

  if (loading) {
    return (
      <section className="nearby-attractions" style={{ marginTop: '3rem' }}>
        <h2 className="detail-section-title">{t('detail.attraction.nearby')}</h2>
        <div className="attraction-grid" aria-busy="true">
          {Array.from({ length: 4 }, (_, i) => (
            <AttractionCardSkeleton key={`nearby-skel-${i}`} />
          ))}
        </div>
      </section>
    )
  }

  if (error) {
    return null // Fail silently or show error depending on preference. Silently is better for non-critical sections.
  }

  if (attractions.length === 0) {
    return (
      <section className="nearby-attractions" style={{ marginTop: '3rem' }}>
        <h2 className="detail-section-title">{t('detail.attraction.nearby')}</h2>
        <p>{t('detail.attraction.nearbyEmpty')}</p>
      </section>
    )
  }

  return (
    <section className="nearby-attractions" style={{ marginTop: '3rem' }}>
      <h2 className="detail-section-title">{t('detail.attraction.nearby')}</h2>
      <div className="attraction-grid">
        {attractions.map((attraction, i) => (
          <AttractionCard
            key={attraction.id}
            attraction={attraction}
            index={i}
            liked={liked.has(attraction.id)}
            onToggleLike={toggleLike}
          />
        ))}
      </div>
    </section>
  )
}
