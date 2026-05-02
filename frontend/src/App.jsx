import { useEffect, useRef, useState } from 'react'
import './App.css'
import Dashboard from './pages/Dashboard.jsx'
import Login from './pages/Login.jsx'
import Members from './pages/Members.jsx'
import Profile from './pages/Profile.jsx'
import Sidebar from './components/Sidebar.jsx'
import { loginUser, registerUser, updateClanTag, getDashboard, getMembers } from './services/api.js'

const POLL_INTERVAL = 5 * 60 * 1000

function getPageFromHash() {
  const page = window.location.hash.replace('#/', '')
  if (page === 'profile' || page === 'login' || page === 'members') return page
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

  const [sidebarOpen, setSidebarOpen] = useState(false)

  const [dashboardData, setDashboardData] = useState(null)
  const [membersData, setMembersData] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const pollRef = useRef(null)

  async function loadAllData(showLoading = false) {
    if (showLoading) setIsLoading(true)
    setError('')
    try {
      const [dashResult, membersResult] = await Promise.allSettled([
        getDashboard(token),
        getMembers(token),
      ])
      if (dashResult.status === 'fulfilled') {
        setDashboardData(dashResult.value)
      } else {
        if (dashResult.reason?.status === 401) { handleLogout(); return }
        setError(dashResult.reason?.message || 'Fehler beim Laden')
      }
      if (membersResult.status === 'fulfilled') {
        setMembersData(membersResult.value.members)
      } else if (membersResult.reason?.status === 401) {
        handleLogout()
      }
    } finally {
      if (showLoading) setIsLoading(false)
    }
  }

  useEffect(() => {
    if (!token) return
    loadAllData(true)
    pollRef.current = setInterval(() => loadAllData(false), POLL_INTERVAL)
    return () => clearInterval(pollRef.current)
  }, [token])

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
    clearInterval(pollRef.current)
    localStorage.removeItem('token')
    setToken('')
    setAuthError('')
    setDashboardData(null)
    setMembersData(null)
    navigateTo('login')
  }

  const avgTrophies = membersData?.length
    ? Math.round(membersData.reduce((sum, m) => sum + (m.trophies || 0), 0) / membersData.length)
    : null

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
    <main className={`app-shell${sidebarOpen ? ' sidebar-is-open' : ''}`}>
      {currentPage === 'dashboard' ? (
        <>
          <header className="topbar">
            <div>
              <p className="eyebrow">{dashboardData?.clan_name || 'Clan Dashboard'}</p>
              <h1>Clan Dashboard</h1>
            </div>
          </header>

          <Dashboard
            data={dashboardData}
            error={error}
            isLoading={isLoading && !dashboardData}
            onRefresh={() => loadAllData(true)}
            avgTrophies={avgTrophies}
          />
        </>
      ) : currentPage === 'members' ? (
        <Members
          members={membersData}
          error={error}
          isLoading={isLoading && !membersData}
          onRefresh={() => loadAllData(true)}
          clanName={dashboardData?.clan_name}
        />
      ) : (
        <Profile
          token={token}
          onUnauthorized={handleLogout}
          onDashboardInvalidate={() => loadAllData(true)}
        />
      )}

      <Sidebar token={token} currentPage={currentPage} onLogout={handleLogout} open={sidebarOpen} onToggle={() => setSidebarOpen(v => !v)} />
    </main>
  )
}

export default App
