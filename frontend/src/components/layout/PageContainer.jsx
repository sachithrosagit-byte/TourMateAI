// Standard page wrapper — every page inside the app shell should render its
// content through this so titles, widths, and spacing stay consistent.
//
//   <PageContainer title="Explore" subtitle="Find your next stop" actions={<button/>}>
//     …page content…
//   </PageContainer>
//
// width: 'default' (1200px) | 'narrow' (704px, forms/reading) | 'wide' (1400px, maps)

export default function PageContainer({
  title,
  subtitle,
  actions,
  width = 'default',
  children,
}) {
  return (
    <div className={`page page-${width}`}>
      {(title || actions) && (
        <div className="page-header">
          <div>
            {title && <h1 className="page-title">{title}</h1>}
            {subtitle && <p className="page-subtitle">{subtitle}</p>}
          </div>
          {actions && <div className="page-actions">{actions}</div>}
        </div>
      )}
      {children}
    </div>
  )
}
