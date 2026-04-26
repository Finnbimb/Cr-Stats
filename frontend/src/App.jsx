import { useEffect, useState } from 'react'
import './App.css'
import Dashboard from './pages/Dashboard.jsx'
import Login from './pages/Login.jsx'
import Profile from './pages/Profile.jsx'
import { loginUser, registerUser, updateClanTag } from './services/api.js'

function getPageFromHash() {
  const page = window.location.hash.replace('#/', '')
  if (page === 'profile' || page === 'login') return page
  return 'dashboard'
}

function navigateTo(page) {
  const nextHash = `#/${page}`
  if (window.location.hash !== nextHash) {
    window.location.hash = nextHash
  }
}

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '')
  const [currentPage, setCurrentPage] = useState(getPageFromHash())
  const [authError, setAuthError] = useState('')
  const [isAuthLoading, setIsAuthLoading] = useState(false)

  useEffect(() => {
    function handleHashChange() {
      setCurrentPage(getPageFromHash())
    }
    handleHashChange()
    window.addEventListener('hashchange', handleHashChange)
    return () => window.removeEventListener('hashchange', handleHashChange)
  }, [])

  useEffect(() => {
    if (!token && currentPage !== 'login') navigateTo('login')
    if (token && currentPage === 'login') navigateTo('dashboard')
  }, [currentPage, token])

  async function handleLogin(username, password) {
    setIsAuthLoading(true)
    setAuthError('')
    try {
      const data = await loginUser(username, password)
      localStorage.setItem('token', data.access_token)
      setToken(data.access_token)
      navigateTo('dashboard')
    } catch (err) {
      setAuthError(err.message)
    } finally {
      setIsAuthLoading(false)
    }
  }

  async function handleRegister(username, email, password, clanTag) {
    setIsAuthLoading(true)
    setAuthError('')
    try {
      await registerUser(username, email, password)
      const data = await loginUser(username, password)
      localStorage.setItem('token', data.access_token)
      setToken(data.access_token)
      if (clanTag.trim()) {
        const normalized = clanTag.trim().toUpperCase()
        await updateClanTag(data.access_token, normalized.startsWith('#') ? normalized : `#${normalized}`)
      }
      navigateTo('dashboard')
    } catch (err) {
      setAuthError(err.message)
    } finally {
      setIsAuthLoading(false)
    }
  }

  function handleLogout() {
    localStorage.removeItem('token')
    setToken('')
    setAuthError('')
    navigateTo('login')
  }

  if (!token) {
    return (
      <Login
        error={authError}
        isLoading={isAuthLoading}
        onLogin={handleLogin}
        onRegister={handleRegister}
      />
    )
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">CrStats</p>
          <h1>Clan Dashboard</h1>
        </div>
        <nav className="nav-actions">
          <a className={currentPage === 'dashboard' ? 'active' : ''} href="#/dashboard">
            Dashboard
          </a>
          <a className={currentPage === 'profile' ? 'active' : ''} href="#/profile">
            Profil
          </a>
          <button onClick={handleLogout} type="button">
            Logout
          </button>
        </nav>
      </header>

      {currentPage === 'dashboard' ? (
        <Dashboard token={token} onUnauthorized={handleLogout} />
      ) : (
        <Profile token={token} onUnauthorized={handleLogout} />
      )}
    </main>
  )
}

export default App
