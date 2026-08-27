// TourMateAI wordmark image.
// variant="colored" (default) → logo_colored.png  — used everywhere in the app shell.
// variant="bw"                → logo_black&white.png — used on the landing page & auth pages.

import logoColored from '../../assets/logo_colored.png'
import logoBW from '../../assets/logo_black&white.png'

export default function Logo({ size = 'md', variant = 'colored' }) {
  const src = variant === 'bw' ? logoBW : logoColored
  return (
    <span className={`logo logo-${size}`}>
      <img src={src} alt="TourMateAI" className="logo-mark" />
    </span>
  )
}
