import { useEffect, useRef, useState } from 'react'
import './App.css'
import Dashboard from './pages/Dashboard.jsx'
import Login from './pages/Login.jsx'
import Members from './pages/Members.jsx'
import Profile from './pages/Profile.jsx'
import Rankings from './pages/Rankings.jsx'
import War from './pages/War.jsx'
import Topbar from './components/Topbar.jsx'
import { loginUser, registerUser, updateClanTag, getDashboard, getMembers, getWarPerformers, getWarParticipants } from './services/api.js'

const POLL_INTERVAL = 5 * 60 * 1000

function getPageFromHash() {
  const page = window.location.hash.replace('#/', '')
  if (['profile', 'login', 'members', 'rankings', 'war'].includes(page)) return page
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
  const [membersData, setMembersData] = useState(null)
  const [warData, setWarData] = useState(null)
  const [warParticipantsData, setWarParticipantsData] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const pollRef = useRef(null)

  async function loadAllData(showLoading = false) {
    if (showLoading) setIsLoading(true)
    setError('')
    try {
      const [dashResult, membersResult, warResult, warParticipantsResult] = await Promise.allSettled([
        getDashboard(token),
        getMembers(token),
        getWarPerformers(token),
        getWarParticipants(token),
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
      if (warResult.status === 'fulfilled') {
        setWarData(warResult.value)
      }
      if (warParticipantsResult.status === 'fulfilled') {
        setWarParticipantsData(warParticipantsResult.value)
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
    setWarData(null)
    setWarParticipantsData(null)
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
    <>
      <Topbar
        token={token}
        currentPage={currentPage}
        clanName={dashboardData?.clan_name}
        onLogout={handleLogout}
      />

      <main className="app-shell">
        {currentPage === 'dashboard' && (
          <Dashboard
            data={dashboardData}
            error={error}
            isLoading={isLoading && !dashboardData}
            onRefresh={() => loadAllData(true)}
            avgTrophies={avgTrophies}
            warData={warData}
            membersData={membersData}
          />
        )}
        {currentPage === 'members' && (
          <Members
            members={membersData}
            error={error}
            isLoading={isLoading && !membersData}
            onRefresh={() => loadAllData(true)}
          />
        )}
        {currentPage === 'rankings' && <Rankings />}
        {currentPage === 'war' && <War warData={warData} participantsData={warParticipantsData} isLoading={isLoading && !warParticipantsData} />}
        {currentPage === 'profile' && (
          <Profile
            token={token}
            onUnauthorized={handleLogout}
            onDashboardInvalidate={() => loadAllData(true)}
          />
        )}
      </main>
    </>
  )
}

export default App
