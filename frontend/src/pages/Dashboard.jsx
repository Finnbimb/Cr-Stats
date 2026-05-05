import WarTop from '../components/WarTop.jsx'

function parseLastSeen(ls) {
  if (!ls) return null
  // Format: "20230524T133000.000Z"
  const m = ls.match(/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})/)
  if (!m) return null
  return new Date(`${m[1]}-${m[2]}-${m[3]}T${m[4]}:${m[5]}:${m[6]}.000Z`)
}

function calcActiveMembers(members) {
  if (!members?.length) return null
  const cutoff = Date.now() - 24 * 60 * 60 * 1000
  const active = members.filter(m => {
    const date = parseLastSeen(m.last_seen)
    return date ? date.getTime() > cutoff : true
  }).length
  return { active, total: members.length }
}

function Dashboard({ data, error, isLoading, avgTrophies, warData, membersData }) {
  if (isLoading) {
    return <section className="panel">Dashboard wird geladen...</section>
  }

  if (error) {
    return (
      <section className="panel page-stack">
        <h2>Dashboard</h2>
        <p className="message error">{error}</p>
        <p className="hint">
          Wenn noch kein Clan-Tag gespeichert ist, stelle ihn zuerst im Profile ein.
        </p>
        <a className="inline-link" href="#/profile">Zum Profile</a>
      </section>
    )
  }

  if (data?.message) {
    return (
      <section className="panel page-stack">
        <h2>Dashboard</h2>
        <p className="message error">{data.message}</p>
        <p className="hint">
          Hinterlege zuerst den Clan-Tag im Profile, damit Location und Ranking
          automatisch geladen werden koennen.
        </p>
        <a className="inline-link" href="#/profile">Zum Profile</a>
      </section>
    )
  }

  if (!data) return null

  const activity = calcActiveMembers(membersData)

  return (
    <section className="dashboard-layout">

      <div className="dashboard-left">
        <div className="card-grid card-grid--2col">

          <a href="#/rankings" className="panel stat-card stat-card--rank stat-card--link">
            <span className="stat-label">Leaderboard Rang ({data.location})</span>
            <strong>{data.leaderboard_rank != null ? `#${data.leaderboard_rank}` : '—'}</strong>
          </a>

          <a href="#/rankings" className="panel stat-card stat-card--war stat-card--link">
            <span className="stat-label">War Rang ({data.location})</span>
            <strong>{data.war_rank != null ? `#${data.war_rank}` : '—'}</strong>
          </a>

          <article className="panel stat-card stat-card--trophies">
            <span className="stat-label">Ø Trophäen</span>
            <strong>{avgTrophies != null ? avgTrophies.toLocaleString() : '—'}</strong>
          </article>

          <article className="panel stat-card stat-card--activity">
            <span className="stat-label">Aktiv (24h)</span>
            <strong>
              {activity
                ? `${activity.active} / ${activity.total}`
                : '—'}
            </strong>
          </article>

        </div>
      </div>

      <WarTop warData={warData} warRank={warData?.war_rank ?? null} />

    </section>
  )
}

export default Dashboard
