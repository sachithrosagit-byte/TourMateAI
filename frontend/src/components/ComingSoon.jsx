// Friendly empty-state used by pages whose features haven't landed yet.

import '../styles/pages.css'

export default function ComingSoon({ icon = '🌴', title, children }) {
  return (
    <div className="card coming-soon">
      <span className="coming-soon-icon" aria-hidden="true">{icon}</span>
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  )
}
