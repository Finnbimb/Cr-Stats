import { useEffect, useState } from 'react'
import './App.css'
import Dashboard from './pages/Dashboard.jsx'
import Login from './pages/Login.jsx'
import Profile from './pages/Profile.jsx'
import { loginUser } from './services/api.js'

function getPageFromHash() {
  const page = window.location.hash.replace('#/', '')

  if (page === 'profile' || page === 'login') {
    return page
  }

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
  const [loginError, setLoginError] = useState('')
  const [isLoggingIn, setIsLoggingIn] = useState(false)

  useEffect(() => {
    function handleHashChange() {
      setCurrentPage(getPageFromHash())
    }

    handleHashChange()
    window.addEventListener('hashchange', handleHashChange)

    return () => {
      window.removeEventListener('hashchange', handleHashChange)
    }
  }, [])

  useEffect(() => {
    if (!token && currentPage !== 'login') {
      navigateTo('login')
    }

    if (token && currentPage === 'login') {
      navigateTo('dashboard')
    }
  }, [currentPage, token])

  async function handleLogin(username, password) {
    setIsLoggingIn(true)
    setLoginError('')

    try {
      const data = await loginUser(username, password)
      localStorage.setItem('token', data.access_token)
      setToken(data.access_token)
      navigateTo('dashboard')
    } catch (error) {
      setLoginError(error.message)
    } finally {
      setIsLoggingIn(false)
    }
  }

  function handleLogout() {
    localStorage.removeItem('token')
    setToken('')
    setLoginError('')
    navigateTo('login')
  }

  if (!token) {
    return (
      <main className="auth-layout">
        <Login
          error={loginError}
          isLoading={isLoggingIn}
          onLogin={handleLogin}
        />
      </main>
    )
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">CrStats Frontend</p>
          <h1>Clan Dashboard</h1>
        </div>

        <nav className="nav-actions">
          <a
            className={currentPage === 'dashboard' ? 'active' : ''}
            href="#/dashboard"
          >
            Dashboard
          </a>
          <a
            className={currentPage === 'profile' ? 'active' : ''}
            href="#/profile"
          >
            Profile
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
