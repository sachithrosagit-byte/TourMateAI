// Primary navigation items, shared by the desktop navbar and mobile drawer.
//
// Admin visibility: the backend doesn't return a `role` yet, so the Admin link
// stays hidden for everyone until the Users table grows one. No frontend
// change will be needed beyond the backend sending user.role === 'admin'.

import { useTranslation } from 'react-i18next'
import { useAuth } from '../context/AuthContext'

export default function useNavItems() {
  const { user } = useAuth()
  const { t } = useTranslation()

  const items = [
    { to: '/', label: t('nav.home') },
    { to: '/explore', label: t('nav.explore') },
    { to: '/itineraries', label: t('nav.itineraries') },
    { to: '/chat', label: t('nav.chat') },
    { to: '/identify', label: t('nav.identify') },
  ]
  if (user?.role === 'admin') items.push({ to: '/admin', label: t('nav.admin') })
  return items
}
