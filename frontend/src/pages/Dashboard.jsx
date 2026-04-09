import { useEffect, useState } from 'react'
import { getDashboard } from '../services/api.js'

function Dashboard({ onUnauthorized, token }) {
  const [dashboardData, setDashboardData] = useState(null)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let isActive = true

    async function loadDashboard() {
      setIsLoading(true)
      setError('')

      try {
        const data = await getDashboard(token)

        if (isActive) {
          setDashboardData(data)
        }
      } catch (loadError) {
        if (!isActive) {
          return
        }

        if (loadError.status === 401) {
          onUnauthorized()
          return
        }

        setError(loadError.message)
      } finally {
        if (isActive) {
          setIsLoading(false)
        }
      }
    }

    loadDashboard()

    return () => {
      isActive = false
    }
  }, [onUnauthorized, token])

  if (isLoading) {
    return <section className="panel">Dashboard wird geladen...</section>
  }

  if (error) {
    return (
      <section className="panel page-stack">
        <h2>Dashboard</h2>
        <p className="message error">{error}</p>
        <p className="hint">
          Wenn noch kein Clan-Tag gespeichert ist, stelle ihn zuerst im Profile
          ein.
        </p>
        <a className="inline-link" href="#/profile">
          Zum Profile
        </a>
      </section>
    )
  }

  if (dashboardData?.message) {
    return (
      <section className="panel page-stack">
        <h2>Dashboard</h2>
        <p className="message error">{dashboardData.message}</p>
        <p className="hint">
          Hinterlege zuerst Clan-Tag und Location im Profile, damit das Ranking
          geladen werden kann.
        </p>
        <a className="inline-link" href="#/profile">
          Zum Profile
        </a>
      </section>
    )
  }

  return (
    <section className="page-stack">
      <div className="panel">
        <p className="eyebrow">Dashboard</p>
        <h2>Deine aktuellen Stats</h2>
        <p className="hint">
          Diese Werte kommen direkt vom Backend-Endpunkt `/dashboard`.
        </p>
      </div>

      <div className="card-grid">
        <article className="panel stat-card">
          <span className="stat-label">Clan</span>
          <strong>{dashboardData.clan_name}</strong>
        </article>

        <article className="panel stat-card">
          <span className="stat-label">Username</span>
          <strong>{dashboardData.username}</strong>
        </article>

        <article className="panel stat-card">
          <span className="stat-label">Clan Tag</span>
          <strong>{dashboardData.clan_tag}</strong>
        </article>

        <article className="panel stat-card">
          <span className="stat-label">Leaderboard Rank</span>
          <strong>{`#${dashboardData.leaderboard_rank} (${dashboardData.location})`}</strong>
        </article>

        {/* <article className="panel stat-card">
          <span className="stat-label">Location</span>
          <strong>{dashboardData.location}</strong>
        </article> */}
      </div>
    </section>
  )
}

export default Dashboard
