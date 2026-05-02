import { useState } from 'react'
import '../auth.css'

function IconUser() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="8" r="4" />
      <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" />
    </svg>
  )
}

function IconMail() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="4" width="20" height="16" rx="2" />
      <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
    </svg>
  )
}

function IconKey() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="7.5" cy="15.5" r="5.5" />
      <path d="m21 2-9.6 9.6" />
      <path d="m15.5 7.5 3 3L22 7l-3-3" />
    </svg>
  )
}

function IconHash() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="4" y1="9" x2="20" y2="9" />
      <line x1="4" y1="15" x2="20" y2="15" />
      <line x1="10" y1="3" x2="8" y2="21" />
      <line x1="16" y1="3" x2="14" y2="21" />
    </svg>
  )
}

function IconEye({ closed }) {
  if (closed) {
    return (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
        <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
        <line x1="1" y1="1" x2="23" y2="23" />
      </svg>
    )
  }
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  )
}

function Login({ error, isLoading, onLogin, onRegister }) {
  const [tab, setTab] = useState('login')
  const [step, setStep] = useState(1)

  // Login state
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)

  // Register state
  const [rUsername, setRUsername] = useState('')
  const [rEmail, setREmail] = useState('')
  const [rPassword, setRPassword] = useState('')
  const [rConfirm, setRConfirm] = useState('')
  const [rClanTag, setRClanTag] = useState('')
  const [showRPw, setShowRPw] = useState(false)
  const [showRConfirm, setShowRConfirm] = useState(false)
  const [localError, setLocalError] = useState('')

  function switchTab(next) {
    setTab(next)
    setStep(1)
    setLocalError('')
  }

  function handleLoginSubmit(e) {
    e.preventDefault()
    onLogin(username, password)
  }

  function handleStep1(e) {
    e.preventDefault()
    setLocalError('')
    if (rPassword !== rConfirm) {
      setLocalError('Passwörter stimmen nicht überein.')
      return
    }
    setStep(2)
  }

  function handleRegisterSubmit(e) {
    e.preventDefault()
    setLocalError('')
    onRegister(rUsername, rEmail, rPassword, rClanTag)
  }

  const displayError = localError || error

  return (
    <div className="auth-layout">
      <div className="auth-brand">
        <div className="auth-logo">👑</div>
        <h1 className="auth-title">CRStats</h1>
        <p className="auth-subtitle">Clash Royale Clan Dashboard</p>
      </div>

      <div className="auth-card">
        <div className="auth-tabs">
          <button
            type="button"
            className={`auth-tab${tab === 'login' ? ' active' : ''}`}
            onClick={() => switchTab('login')} 
          >
            Einloggen
          </button>
          <button
            type="button"
            className={`auth-tab${tab === 'register' ? ' active' : ''}`}
            onClick={() => switchTab('register')}
          >
            Registrieren
          </button>
        </div>

        {tab === 'login' && (
          <form className="auth-form" onSubmit={handleLoginSubmit}>
            <div className="auth-field">
              <label className="auth-field-label">Benutzername</label>
              <div className="auth-input-wrap">
                <span className="icon-left"><IconUser /></span>
                <input
                  className="auth-input"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  placeholder="DeinName"
                  autoComplete="username"
                  required
                />
              </div>
            </div>

            <div className="auth-field">
              <label className="auth-field-label">Passwort</label>
              <div className="auth-input-wrap">
                <span className="icon-left"><IconKey /></span>
                <input
                  className="auth-input has-right-icon"
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  required
                />
                <button type="button" className="icon-right" onClick={() => setShowPw(v => !v)}>
                  <IconEye closed={showPw} />
                </button>
              </div>
            </div>

            <div className="auth-forgot">
              <span>Passwort vergessen?</span>
            </div>

            {displayError && <p className="auth-error">{displayError}</p>}

            <button className="auth-btn-primary" type="submit" disabled={isLoading}>
              {isLoading ? 'Lade...' : 'Einloggen'}
            </button>

            <div className="auth-or">oder</div>

            <button type="button" className="auth-btn-secondary" onClick={() => switchTab('register')}>
              Noch kein Konto? Registrieren
            </button>
          </form>
        )}

        {tab === 'register' && step === 1 && (
          <form className="auth-form" onSubmit={handleStep1}>
            <div className="step-indicator">
              <div className="step-circle active">1</div>
              <span className="step-name active">Konto</span>
              <div className="step-line" />
              <div className="step-circle inactive">2</div>
              <span className="step-name">Clan</span>
            </div>

            <div className="auth-field">
              <label className="auth-field-label">Benutzername</label>
              <div className="auth-input-wrap">
                <span className="icon-left"><IconUser /></span>
                <input
                  className="auth-input"
                  value={rUsername}
                  onChange={e => setRUsername(e.target.value)}
                  placeholder="DeinName"
                  autoComplete="username"
                  required
                />
              </div>
            </div>

            <div className="auth-field">
              <label className="auth-field-label">E-Mail</label>
              <div className="auth-input-wrap">
                <span className="icon-left"><IconMail /></span>
                <input
                  className="auth-input"
                  type="email"
                  value={rEmail}
                  onChange={e => setREmail(e.target.value)}
                  placeholder="deine@email.de"
                  autoComplete="email"
                  required
                />
              </div>
            </div>

            <div className="auth-field">
              <label className="auth-field-label">Passwort</label>
              <div className="auth-input-wrap">
                <span className="icon-left"><IconKey /></span>
                <input
                  className="auth-input has-right-icon"
                  type={showRPw ? 'text' : 'password'}
                  value={rPassword}
                  onChange={e => setRPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete="new-password"
                  required
                />
                <button type="button" className="icon-right" onClick={() => setShowRPw(v => !v)}>
                  <IconEye closed={showRPw} />
                </button>
              </div>
            </div>

            <div className="auth-field">
              <label className="auth-field-label">Passwort Bestätigen</label>
              <div className="auth-input-wrap">
                <span className="icon-left"><IconKey /></span>
                <input
                  className="auth-input has-right-icon"
                  type={showRConfirm ? 'text' : 'password'}
                  value={rConfirm}
                  onChange={e => setRConfirm(e.target.value)}
                  placeholder="••••••••"
                  autoComplete="new-password"
                  required
                />
                <button type="button" className="icon-right" onClick={() => setShowRConfirm(v => !v)}>
                  <IconEye closed={showRConfirm} />
                </button>
              </div>
            </div>

            {displayError && <p className="auth-error">{displayError}</p>}

            <button className="auth-btn-primary" type="submit">
              Weiter →
            </button>

            <div className="auth-or">oder</div>

            <button type="button" className="auth-btn-secondary" onClick={() => switchTab('login')}>
              Bereits registriert? Einloggen
            </button>
          </form>
        )}

        {tab === 'register' && step === 2 && (
          <form className="auth-form" onSubmit={handleRegisterSubmit}>
            <div className="step-indicator">
              <div className="step-circle inactive">1</div>
              <span className="step-name">Konto</span>
              <div className="step-line" />
              <div className="step-circle active">2</div>
              <span className="step-name active">Clan</span>
            </div>

            <div className="auth-field">
              <label className="auth-field-label">Clan Tag</label>
              <div className="auth-input-wrap">
                <span className="icon-left"><IconHash /></span>
                <input
                  className="auth-input"
                  value={rClanTag}
                  onChange={e => setRClanTag(e.target.value)}
                  placeholder="#ABCD123"
                  autoComplete="off"
                />
              </div>
            </div>

            <p className="hint" style={{ fontSize: '0.85rem', margin: 0 }}>
              Optional – kann später im Profil gesetzt werden.
            </p>

            {displayError && <p className="auth-error">{displayError}</p>}

            <button className="auth-btn-primary" type="submit" disabled={isLoading}>
              {isLoading ? 'Registriert...' : 'Registrieren'}
            </button>

            <button type="button" className="auth-btn-secondary" onClick={() => setStep(1)}>
              ← Zurück
            </button>
          </form>
        )}
      </div>

      <p className="auth-footer">CRStats ist kein offizielles Supercell-Produkt.</p>
    </div>
  )
}

export default Login
