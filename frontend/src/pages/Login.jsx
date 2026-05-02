import { useCallback, useEffect, useRef, useState } from 'react'
import '../auth.css'

const SLIDE_INTERVAL = 4500
const LOOP_RESET_DELAY = 650

const featureSlides = [
  {
    label: 'Start',
    title: 'Clan in Sekunden verbinden',
    text: 'Registrieren, Clan-Tag setzen und CRStats lädt deine wichtigsten Clan-Daten direkt in dein Dashboard.',
    stat: 'Clan Tag',
    value: '#ABCD123',
  },
  {
    label: 'Ranking',
    title: 'Leaderboard ohne Suchen',
    text: 'Behalte Clan-Name, Rang, Trophäen und Region an einem Ort, ohne jedes Mal ins Spiel wechseln zu müssen.',
    stat: 'Ranking',
    value: 'Top 200',
  },
  {
    label: 'War',
    title: 'War-Checks für den Alltag',
    text: 'Der Fokus liegt auf Clan-War-Übersicht, offenen Teilnehmern und schnellen Checks für Leader und Co-Leader.',
    stat: 'War View',
    value: 'Live',
  },
  {
    label: 'Profil',
    title: 'Daten bleiben änderbar',
    text: 'Wenn sich dein Clan ändert, aktualisierst du den Tag später im Profil und das Dashboard zieht nach.',
    stat: 'Profil',
    value: 'Flexibel',
  },
]

const carouselSlides = [...featureSlides, featureSlides[0]]

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
  const [activeFeature, setActiveFeature] = useState(0)

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

  const timerRef = useRef(null)
  const resetTimeoutRef = useRef(null)
  const skipNextScrollRef = useRef(false)
  const cardRefs = useRef([])
  const trackRef = useRef(null)
  const isProgrammaticRef = useRef(false)

  const startTimer = useCallback(() => {
    clearInterval(timerRef.current)
    timerRef.current = setInterval(() => {
      setActiveFeature(f => f + 1)
    }, SLIDE_INTERVAL)
  }, [])

  function scrollToCard(index, behavior = 'smooth') {
    const el = trackRef.current
    const card = cardRefs.current[index]
    if (!el || !card) return
    isProgrammaticRef.current = true
    el.scrollTo({ left: card.offsetLeft - 20, behavior })
  }

  function selectFeature(index) {
    clearTimeout(resetTimeoutRef.current)
    setActiveFeature(index)
    startTimer()
  }

  useEffect(() => {
    startTimer()
    return () => {
      clearInterval(timerRef.current)
      clearTimeout(resetTimeoutRef.current)
    }
  }, [startTimer])

  useEffect(() => {
    if (skipNextScrollRef.current) {
      skipNextScrollRef.current = false
      return
    }

    scrollToCard(activeFeature)

    if (activeFeature === featureSlides.length) {
      clearTimeout(resetTimeoutRef.current)
      resetTimeoutRef.current = setTimeout(() => {
        scrollToCard(0, 'instant')
        skipNextScrollRef.current = true
        setActiveFeature(0)
      }, LOOP_RESET_DELAY)
    }
  }, [activeFeature])

  useEffect(() => {
    const el = trackRef.current
    if (!el) return

    function handleScrollDone() {
      if (isProgrammaticRef.current) {
        isProgrammaticRef.current = false
        return
      }
      const scrollLeft = el.scrollLeft
      let closest = 0
      let minDist = Infinity
      cardRefs.current.forEach((card, i) => {
        if (!card) return
        const dist = Math.abs((card.offsetLeft - 20) - scrollLeft)
        if (dist < minDist) { minDist = dist; closest = i }
      })
      setActiveFeature(closest % featureSlides.length)
      startTimer()
    }

    if ('onscrollend' in el) {
      el.addEventListener('scrollend', handleScrollDone)
      return () => el.removeEventListener('scrollend', handleScrollDone)
    }
    let t
    function onScroll() { clearTimeout(t); t = setTimeout(handleScrollDone, 200) }
    el.addEventListener('scroll', onScroll)
    return () => { el.removeEventListener('scroll', onScroll); clearTimeout(t) }
  }, [startTimer])

  const displayError = localError || error

  return (
    <div className="auth-layout">
      <section className="auth-shell" aria-label="CRStats Login">
        <div className="auth-main">
          <div className="auth-brand">
            <div className="auth-logo">CR</div>
            <div>
              <p className="auth-kicker">Clan Command Center</p>
              <h1 className="auth-title">CRStats</h1>
              <p className="auth-subtitle">Clash Royale Clan Dashboard</p>
            </div>
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

                <p className="hint auth-hint">
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
        </div>

        <aside className="auth-royale-panel" aria-label="CRStats Hinweise">
          <div className="auth-hero-copy">
            <p className="auth-kicker">Für aktive Clans</p>
            <h2>Dein Clan-Dashboard für optimale Clan-Performance.</h2>
            <p>
              CRStats bündelt Clan-Tag, Ranking und War-Checks in einer Oberfläche,
              die schneller lesbar ist als ein Wechsel durchs Spielmenü.
            </p>
          </div>

          {/* <div className="auth-figure-stage" aria-hidden="true">
            <div className="royale-figure figure-prince">
              <span className="figure-plume" />
              <span className="figure-head" />
              <span className="figure-body" />
              <span className="figure-shield" />
              <span className="figure-spear" />
            </div>
            <div className="royale-tower">
              <span className="tower-crown" />
              <span className="tower-roof" />
              <span className="tower-body" />
              <span className="tower-gate" />
            </div>
            <div className="royale-figure figure-archer">
              <span className="figure-hair" />
              <span className="figure-head" />
              <span className="figure-body" />
              <span className="figure-bow" />
            </div>
            <div className="auth-arena-floor" />
          </div> */}

          <div ref={trackRef} className="auth-carousel">
            {carouselSlides.map((slide, index) => (
              <article
                key={`${slide.label}-${index}`}
                ref={el => { cardRefs.current[index] = el }}
                className="auth-feature-card"
                aria-hidden={index === featureSlides.length}
              >
                <div>
                  <span>{slide.stat}</span>
                  <strong>{slide.value}</strong>
                </div>
                <h3>{slide.title}</h3>
                <p>{slide.text}</p>
              </article>
            ))}
          </div>

          <div className="auth-carousel-dots">
            {featureSlides.map((_, index) => (
              <button
                key={index}
                type="button"
                className={`auth-carousel-dot${activeFeature % featureSlides.length === index ? ' active' : ''}`}
                onClick={() => selectFeature(index)}
              />
            ))}
          </div>

          <p className="auth-footer">
            Dieses Material ist inoffiziell und wird nicht von Supercell unterstützt.
          </p>
        </aside>
      </section>
    </div>
  )
}

export default Login
