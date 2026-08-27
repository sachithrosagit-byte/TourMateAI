// Attraction imagery, in order of preference: a bundled real photo matched by
// name/category (assets/photos.js), then the row's `image_url`, then a
// stock-style SVG landscape tinted per category, with the sun position and
// ridge shape varied per attraction id so a grid of placeholders doesn't look
// copy-pasted.

import { attractionPhoto } from '../../assets/photos'

const THEMES = {
  heritage: { sky: ['#F6C68B', '#FBEADC'], far: '#C97B4A', near: '#9E3D22', sun: '#E8794A' },
  religious: { sky: ['#F3D28C', '#FBF0DA'], far: '#C9973F', near: '#8A6420', sun: '#DCA54C' },
  historical: { sky: ['#E8CBA6', '#F6EBDA'], far: '#A97B50', near: '#6E4B2E', sun: '#D9A05B' },
  scenic: { sky: ['#BFE0C8', '#EDF7EC'], far: '#5F9A6E', near: '#2E6B47', sun: '#F0C46A' },
  wildlife: { sky: ['#E3D9A8', '#F6F1DC'], far: '#8B9450', near: '#55622F', sun: '#E0A33F' },
  hiking: { sky: ['#B9D7D9', '#EAF4F2'], far: '#4E8388', near: '#1F5257', sun: '#F2CC7B' },
  'hill country': { sky: ['#C9DCCB', '#EFF6EE'], far: '#77A183', near: '#3D6B52', sun: '#EBD48F' },
  beach: { sky: ['#A8DCE0', '#EDF8F6'], far: '#3E9BA4', near: '#135E66', sun: '#F5C86B' },
  nature: { sky: ['#B7D6B4', '#EBF5E9'], far: '#5B8A5B', near: '#2F5D3A', sun: '#EFC670' },
}

const DEFAULT_THEME = { sky: ['#EAD9C2', '#F9F2E7'], far: '#B3835B', near: '#7A5232', sun: '#DCA54C' }

// Two ridge silhouettes so alternating cards get different skylines.
const RIDGES = [
  {
    far: 'M0 172 L70 106 L128 160 L210 92 L286 158 L348 118 L400 150 V260 H0 Z',
    near: 'M0 226 L84 152 L158 218 L248 142 L326 210 L400 176 V260 H0 Z',
  },
  {
    far: 'M0 150 L64 118 L142 168 L226 100 L302 164 L400 108 V260 H0 Z',
    near: 'M0 210 L96 158 L176 224 L262 156 L338 216 L400 188 V260 H0 Z',
  },
]

export default function AttractionImage({ attraction, className = '' }) {
  // Resolution order:
  //  1. Admin-uploaded image_url — always wins so that a custom photo set in
  //     the admin portal is shown everywhere, even for well-known attractions
  //     that have a bundled photo (Sigiriya, Anuradhapura, …).
  //  2. Bundled photo matched by attraction name / category (assets/photos.js).
  //  3. Generated SVG landscape placeholder tinted per category.
  if (attraction.image_url) {
    return (
      <img
        src={attraction.image_url}
        alt={attraction.name}
        className={className}
        loading="lazy"
      />
    )
  }

  const photo = attractionPhoto(attraction)
  if (photo) {
    return (
      <img
        src={photo.src}
        alt={attraction.name}
        className={className}
        style={{ objectPosition: photo.position }}
        loading="lazy"
      />
    )
  }

  const theme = THEMES[(attraction.category || '').toLowerCase()] || DEFAULT_THEME
  const seed = attraction.id || 0
  const ridge = RIDGES[seed % RIDGES.length]
  const sunX = 60 + ((seed * 53) % 280) // keep the sun inside the frame
  const skyId = `sky-${attraction.id}`

  return (
    <svg
      viewBox="0 0 400 260"
      preserveAspectRatio="xMidYMid slice"
      className={className}
      role="img"
      aria-label={attraction.name}
    >
      <defs>
        <linearGradient id={skyId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={theme.sky[0]} />
          <stop offset="100%" stopColor={theme.sky[1]} />
        </linearGradient>
      </defs>
      <rect width="400" height="260" fill={`url(#${skyId})`} />
      <circle cx={sunX} cy="78" r="30" fill={theme.sun} opacity="0.45" />
      <circle cx={sunX} cy="78" r="20" fill={theme.sun} opacity="0.9" />
      <path d={ridge.far} fill={theme.far} opacity="0.55" />
      <path d={ridge.near} fill={theme.near} opacity="0.9" />
    </svg>
  )
}
