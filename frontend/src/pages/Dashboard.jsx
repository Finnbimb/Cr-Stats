function Dashboard({ data, error, isLoading }) {
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
          <strong>{data.clan_name}</strong>
        </article>

        <article className="panel stat-card">
          <span className="stat-label">Username</span>
          <strong>{data.username}</strong>
        </article>

        <article className="panel stat-card">
          <span className="stat-label">Clan Tag</span>
          <strong>{data.clan_tag}</strong>
        </article>

        <article className="panel stat-card">
          <span className="stat-label">Leaderboard Rank</span>
          <strong>{`#${data.leaderboard_rank} (${data.location})`}</strong>
        </article>
      </div>
    </section>
  )
}

export default Dashboard
