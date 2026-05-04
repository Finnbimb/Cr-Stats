const MEDAL = { 1: '🥇', 2: '🥈', 3: '🥉' }

function ProgressBar({ value, max, color = 'var(--color-brand)' }) {
  const pct = max > 0 ? Math.min(100, Math.round((value / max) * 100)) : 0
  return (
    <div className="war-progress-wrap">
      <div
        className="war-progress-bar"
        style={{ width: `${pct}%`, background: color }}
      />
    </div>
  )
}

function WarTop({ warData, warRank }) {
  const isTraining = warData?.is_training
  const label = isTraining ? 'Aktueller Krieg (Training)' : 'Aktueller Krieg'
  const performers = warData?.performers ?? []
  const missingToday = warData?.missing_today ?? []

  const decksToday = warData?.decks_today ?? 0
  const decksTodayMax = warData?.decks_today_max ?? 0
  const decksTotal = warData?.decks_total ?? 0
  const decksTotalMax = warData?.decks_total_max ?? 0

  return (
    <article className="panel war-card">

      <header className="war-card-header">
        <span className="war-card-title">⚔ {label}</span>
        {isTraining && <span className="war-top-badge">Training</span>}
      </header>

      <div className="war-card-body">

        <div className="war-card-rank">
          {warRank != null
            ? <><span className="war-rank-label">Platz</span><strong className="war-rank-value">#{warRank}</strong></>
            : <strong className="war-rank-value">—</strong>
          }
        </div>

        <div className="war-card-stats">
          <div className="war-stat-row">
            <div className="war-stat-header">
              <span className="war-stat-label">Heute gespielt</span>
              <span className="war-stat-count">{decksToday} / {decksTodayMax}</span>
            </div>
            <ProgressBar value={decksToday} max={decksTodayMax} color="var(--color-brand)" />
          </div>

          <div className="war-stat-row">
            <div className="war-stat-header">
              <span className="war-stat-label">Gesamt dieser Krieg</span>
              <span className="war-stat-count">{decksTotal} / {decksTotalMax}</span>
            </div>
            <ProgressBar value={decksTotal} max={decksTotalMax} color="var(--color-accent-green)" />
          </div>
        </div>

      </div>

      {performers.length > 0 && (
        <div className="war-card-section">
          <p className="war-section-title">Top 3 Fame</p>
          <ol className="war-top-list">
            {performers.map((p) => (
              <li key={p.tag} className="war-top-row">
                <span className="war-top-medal">{MEDAL[p.rank] ?? `#${p.rank}`}</span>
                <span className="war-top-name">{p.name}</span>
                <span className="war-top-fame">{p.fame.toLocaleString()}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {missingToday.length > 0 && (
        <div className="war-missing">
          <span className="war-missing-icon">⚠</span>
          <span>Fehlende Battles heute: {missingToday.join(', ')}</span>
        </div>
      )}

    </article>
  )
}

export default WarTop
