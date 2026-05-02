function Dashboard({ data, error, isLoading, avgTrophies }) {
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

  return (
    <section className="page-stack">

      <div className="card-grid">

        <article className="panel stat-card stat-card--rank">
          <span className="stat-label">Leaderboard Rank</span>
          <strong>{`#${data.leaderboard_rank} (${data.location})`}</strong>
        </article>

        <article className="panel stat-card stat-card--trophies">
          <span className="stat-label">Ø Trophäen</span>
          <strong>{avgTrophies != null ? avgTrophies.toLocaleString() : '—'}</strong>
        </article>

        <article className="panel stat-card stat-card--war">
          <span className="stat-label">War Rang ({data.location})</span>
          <strong>{data.war_rank != null ? `#${data.war_rank}` : '—'}</strong>
        </article>
        
      </div>
    </section>
  )
}

export default Dashboard
