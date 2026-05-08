function RaceClansSidebar({ raceClans }) {
  const hasData = raceClans?.length > 0
  const own = hasData ? raceClans.find(c => c.is_own) : null

  let gap = null
  if (own && own.rank > 1) {
    const above = raceClans.find(c => c.rank === own.rank - 1)
    if (above) {
      gap = { rank: above.rank, diff: Math.max(0, above.fame - own.fame) }
    }
  }

  let lead = null
  if (own && own.rank === 1 && raceClans.length > 1) {
    const second = raceClans.find(c => c.rank === 2)
    if (second) lead = Math.max(0, own.fame - second.fame)
  }

  return (
    <aside className="panel war-race-clans">
      <h3 className="war-race-clans-title">Race-Standings</h3>

      {!hasData ? (
        <p className="hint" style={{ margin: 0 }}>Daten werden geladen…</p>
      ) : (
        <ol className="war-race-clans-list">
          {raceClans.map(c => (
            <li
              key={c.tag ?? c.rank}
              className={`war-race-clan${c.is_own ? ' war-race-clan--own' : ''}`}
            >
              <span className="war-race-clan-rank">{c.rank}</span>
              <span className="war-race-clan-name" title={c.name}>{c.name}</span>
              <span className="war-race-clan-fame">
                {(c.fame ?? 0).toLocaleString('de-DE')}
              </span>
            </li>
          ))}
        </ol>
      )}

      {gap && (
        <p className="war-race-gap">
          Noch <strong>{gap.diff.toLocaleString('de-DE')}</strong> Punkte bis Platz #{gap.rank}
        </p>
      )}
      {lead != null && (
        <p className="war-race-gap war-race-gap--lead">
          Vorsprung vor #2: <strong>{lead.toLocaleString('de-DE')}</strong>
        </p>
      )}
    </aside>
  )
}

export default RaceClansSidebar
