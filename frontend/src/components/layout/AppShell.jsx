// The authenticated app shell: navbar + mobile drawer + page content + footer.
// Used as a layout route — child routes render into <Outlet />.

import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'
import MobileDrawer from './MobileDrawer'
import Footer from './Footer'
import './shell.css'

export default function AppShell() {
  const [drawerOpen, setDrawerOpen] = useState(false)

  return (
    <div className="app-shell">
      <Navbar onOpenDrawer={() => setDrawerOpen(true)} />
      <MobileDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />
      <main className="app-main">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}
