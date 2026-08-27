import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import AttractionImage from './AttractionImage'

// We will reuse AttractionImage and just pass a dummy structure or the image_url directly
// Actually AttractionImage takes { id, image_url } which Hotel has.

function HotelImage({ hotel, className }) {
  // If the hotel has an image_url, we just show it. Otherwise a placeholder.
  // We can reuse the default placeholder logic if needed, but for now a simple img works,
  // or we can just use the provided url.
  const src = hotel.image_url || 'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&q=80&w=800'
  return <img src={src} alt={hotel.name} className={className} />
}

export default function HotelCard({ hotel, index = 0 }) {
  const { t } = useTranslation()

  return (
    <Link
      to={`/explore/hotel/${hotel.id}`}
      className="attraction-card"
      style={{ animationDelay: `${Math.min(index, 11) * 45}ms`, display: 'block' }}
    >
      <div className="attraction-card-media">
        <HotelImage hotel={hotel} className="attraction-card-img" />
        <span className="media-badge" style={{ textTransform: 'capitalize' }}>
          {hotel.budget_tier || t('explore.hotelBadgeDefault')}
        </span>
      </div>

      <div className="attraction-card-body">
        <div className="attraction-card-head">
          <h3 className="attraction-card-name">{hotel.name}</h3>
          <span className="rating-inline">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M12 2l2.9 6.3 6.9.8-5.1 4.7 1.4 6.8-6.1-3.5-6.1 3.5 1.4-6.8L2.2 9.1l6.9-.8L12 2z" />
            </svg>
            {hotel.avg_rating ? hotel.avg_rating.toFixed(1) : t('explore.newRating')}
          </span>
        </div>
        <p className="attraction-card-desc" style={{ marginBottom: '4px', fontWeight: 'bold' }}>
          📍 {hotel.location}
        </p>
        <p className="attraction-card-desc">{hotel.description}</p>
      </div>
    </Link>
  )
}

export function HotelCardSkeleton() {
  return (
    <div className="attraction-card skeleton-card" aria-hidden="true">
      <div className="skeleton attraction-card-media" />
      <div className="attraction-card-body">
        <div className="skeleton skeleton-line" style={{ width: '70%', height: '1.1rem' }} />
        <div className="skeleton skeleton-line" style={{ width: '40%' }} />
        <div className="skeleton skeleton-line" style={{ width: '100%' }} />
        <div className="skeleton skeleton-line" style={{ width: '85%' }} />
      </div>
    </div>
  )
}
