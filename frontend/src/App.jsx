import { useEffect, useState } from 'react'
import './App.css'
import Dashboard from './pages/Dashboard.jsx'
import Login from './pages/Login.jsx'
import Members from './pages/Members.jsx'
import Profile from './pages/Profile.jsx'
import Sidebar from './components/Sidebar.jsx'
import { loginUser, registerUser, updateClanTag, getDashboard, getMembers } from './services/api.js'

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

  const [dashboardData, setDashboardData] = useState(null)
  const [dashboardError, setDashboardError] = useState('')
  const [dashboardLoading, setDashboardLoading] = useState(false)

  const [membersData, setMembersData] = useState(null)
  const [membersError, setMembersError] = useState('')
  const [membersLoading, setMembersLoading] = useState(false)

  useEffect(() => {
    if (!token || currentPage !== 'dashboard' || dashboardData !== null) return
    let isActive = true
    setDashboardLoading(true)
    setDashboardError('')
    getDashboard(token)
      .then(data => { if (isActive) setDashboardData(data) })
      .catch(err => {
        if (!isActive) return
        if (err.status === 401) { handleLogout(); return }
        setDashboardError(err.message)
      })
      .finally(() => { if (isActive) setDashboardLoading(false) })
    return () => { isActive = false }
  }, [currentPage, token, dashboardData])

  useEffect(() => {
    if (!token || currentPage !== 'members' || membersData !== null) return
    let isActive = true
    setMembersLoading(true)
    setMembersError('')
    getMembers(token)
      .then(data => { if (isActive) setMembersData(data.members) })
      .catch(err => {
        if (!isActive) return
        if (err.status === 401) { handleLogout(); return }
        setMembersError(err.message)
      })
      .finally(() => { if (isActive) setMembersLoading(false) })
    return () => { isActive = false }
  }, [currentPage, token, membersData])

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
    setDashboardData(null)
    setMembersData(null)
    navigateTo('login')
  }

  function invalidateDashboard() {
    setDashboardData(null)
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
      {currentPage === 'dashboard' ? (
        <>
          <header className="topbar">
            <div>
              <p className="eyebrow">CrStats</p>
              <h1>Clan Dashboard</h1>
            </div>
          </header>

          <Dashboard
            data={dashboardData}
            error={dashboardError}
            isLoading={dashboardLoading}
            onRefresh={invalidateDashboard}
            onUnauthorized={handleLogout}
          />
        </>
      ) : currentPage === 'members' ? (
        <Members
          members={membersData}
          error={membersError}
          isLoading={membersLoading}
          onUnauthorized={handleLogout}
        />
      ) : (
        <Profile
          token={token}
          onUnauthorized={handleLogout}
          onDashboardInvalidate={invalidateDashboard}
        />
      )}

      <Sidebar token={token} currentPage={currentPage} onLogout={handleLogout} />
    </main>
  )
}

export default App
