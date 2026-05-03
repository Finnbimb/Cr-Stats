import { useState } from 'react'
import '../topbar.css'

function getUsernameFromToken(token) {
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    const payload = JSON.parse(atob(base64))
    return payload.sub || 'User'
  } catch {
    return 'User'
  }
}

const PAGE_TITLES = {
  dashboard: 'Clan Dashboard',
  members: 'Mitglieder',
  rankings: 'Rankings',
  war: 'War',
  profile: 'Profil',
}

function IconGrid() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
  )
}

function IconUsers() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  )
}

function IconTrophy() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6" />
      <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18" />
      <path d="M4 22h16" />
      <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22" />
      <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22" />
      <path d="M18 2H6v7a6 6 0 0 0 12 0V2z" />
    </svg>
  )
}

function IconSwords() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="14.5 17.5 3 6 3 3 6 3 17.5 14.5" />
      <line x1="13" y1="19" x2="19" y2="13" />
      <line x1="16" y1="16" x2="20" y2="20" />
      <line x1="19" y1="21" x2="21" y2="19" />
      <polyline points="14.5 6.5 18 3 21 3 21 6 17.5 9.5" />
      <line x1="5" y1="14" x2="9" y2="18" />
      <line x1="7" y1="21" x2="9" y2="19" />
      <line x1="3" y1="19" x2="5" y2="21" />
    </svg>
  )
}

const NAV_ITEMS = [
  { page: 'dashboard', label: 'Dashboard', Icon: IconGrid },
  { page: 'members', label: 'Mitglieder', Icon: IconUsers },
  { page: 'rankings', label: 'Rankings', Icon: IconTrophy },
  { page: 'war', label: 'War', Icon: IconSwords },
]

export default function Topbar({ token, currentPage, clanName, onLogout }) {
  const [profileOpen, setProfileOpen] = useState(false)
  const username = getUsernameFromToken(token)
  const initial = username[0]?.toUpperCase() || '?'
  const pageTitle = PAGE_TITLES[currentPage] || ''

  return (
    <>
      <header className="app-topbar">
        <nav className="topbar-nav">
          {NAV_ITEMS.map(({ page, label, Icon }) => (
            <a
              key={page}
              href={`#/${page}`}
              className={`topbar-link${currentPage === page ? ' active' : ''}`}
            >
              <Icon />
              <span>{label}</span>
            </a>
          ))}
        </nav>

        <div className="topbar-page-title">
          {clanName && <p className="eyebrow">{clanName}</p>}
          <h1 className="topbar-heading">{pageTitle}</h1>
        </div>

        <button
          className="topbar-avatar-btn"
          onClick={() => setProfileOpen(v => !v)}
        >
          <span className="topbar-avatar-circle">{initial}</span>
        </button>
      </header>

      {profileOpen && (
        <div className="profile-popup-overlay" onClick={() => setProfileOpen(false)}>
          <div className="profile-popup-card" onClick={e => e.stopPropagation()}>
            <div className="profile-popup-avatar">{initial}</div>
            <p className="profile-popup-username">{username}</p>
            <a
              href="#/profile"
              className="profile-popup-action"
              onClick={() => setProfileOpen(false)}
            >
              Profil anzeigen
            </a>
            <button
              className="profile-popup-logout"
              onClick={() => { setProfileOpen(false); onLogout() }}
            >
              Abmelden
            </button>
          </div>
        </div>
      )}
    </>
  )
}
