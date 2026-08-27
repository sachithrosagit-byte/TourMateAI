import React from 'react'
import { useTranslation } from 'react-i18next'

export default function LanguageSwitcher({ className = 'btn-ghost' }) {
  const { i18n } = useTranslation()

  const changeLanguage = (e) => {
    i18n.changeLanguage(e.target.value)
  }

  return (
    <select
      className={`select select-bordered select-sm ${className}`}
      style={{ 
        padding: '0.2rem 1.8rem 0.2rem 0.8rem', 
        fontSize: '0.85rem', 
        minHeight: '2rem', 
        height: '2rem',
        borderRadius: 'var(--radius-full)',
        fontFamily: 'var(--font-body)'
      }}
      value={i18n.language || 'en'}
      onChange={changeLanguage}
      aria-label="Select language"
    >
      <option value="en">English</option>
      <option value="si">සිංහල</option>
      <option value="it">Italiano</option>
    </select>
  )
}
