import { useState } from 'react'

function getUsernameFromToken(token) {
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    const payload = JSON.parse(atob(base64))
    return payload.sub || 'User'
  } catch {
    return 'User'
  }
}

function IconChevronLeft() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="15 18 9 12 15 6" />
    </svg>
  )
}

function IconChevronRight() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="9 18 15 12 9 6" />
    </svg>
  )
}

function IconGrid() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
  )
}

export default function Sidebar({ token, currentPage, onLogout }) {
  const [open, setOpen] = useState(true)
  const [profileOpen, setProfileOpen] = useState(false)
  const username = getUsernameFromToken(token)
  const initial = username[0]?.toUpperCase() || '?'

  return (
    <>
      <aside className={`sidebar ${open ? 'sidebar-open' : 'sidebar-closed'}`}>
        <div className="sidebar-header">
          {open && <span className="sidebar-brand">Navigation</span>}
          <button className="sidebar-toggle-btn" onClick={() => setOpen(v => !v)}>
            {open ? <IconChevronRight /> : <IconChevronLeft />}
          </button>
        </div>

        <nav className="sidebar-nav">
          <a
            href="#/dashboard"
            className={`sidebar-link ${currentPage === 'dashboard' ? 'active' : ''}`}
          >
            <IconGrid />
            {open && <span>Dashboard</span>}
          </a>
        </nav>

        <div className="sidebar-footer">
          <button className="sidebar-avatar-btn" onClick={() => setProfileOpen(v => !v)}>
            <span className="sidebar-avatar-circle">{initial}</span>
            {open && <span className="sidebar-avatar-name">{username}</span>}
          </button>
        </div>
      </aside>

      {profileOpen && (
        <div className="profile-popup-overlay" onClick={() => setProfileOpen(false)}>
          <div
            className="profile-popup-card"
            style={{ right: open ? 228 : 60 }}
            onClick={e => e.stopPropagation()}
          >
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
