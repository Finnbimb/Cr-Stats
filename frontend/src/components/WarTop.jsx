const MEDAL = { 1: '🥇', 2: '🥈', 3: '🥉' }

function parseCrTimestamp(ts) {
  if (!ts) return null
  const m = ts.match(/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})/)
  if (!m) return null
  return new Date(`${m[1]}-${m[2]}-${m[3]}T${m[4]}:${m[5]}:${m[6]}.000Z`)
}

function formatCountdown(date) {
  if (!date) return null
  const diff = date.getTime() - Date.now()
  if (diff <= 0) return 'Bald'
  const totalMinutes = Math.floor(diff / 60000)
  const days = Math.floor(totalMinutes / 1440)
  const hours = Math.floor((totalMinutes % 1440) / 60)
  const minutes = totalMinutes % 60
  if (days > 0) return `${days}T ${hours}h ${minutes}min`
  if (hours > 0) return `${hours}h ${minutes}min`
  return `${minutes}min`
}

function formatWarStart(date) {
  if (!date) return null
  return date.toLocaleString('de-DE', {
    weekday: 'short', day: '2-digit', month: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

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

function TrainingView({ warData, warRank }) {
  const warStartDate = parseCrTimestamp(warData?.period_end_time)
  const countdown = formatCountdown(warStartDate)
  const warStartLabel = formatWarStart(warStartDate)
  const clanCount = warData?.clan_count ?? 0

  return (
    <article className="panel war-card">
      <header className="war-card-header">
        <span className="war-card-title">⚔ Trainingsphase</span>
        <span className="war-top-badge">Training</span>
      </header>

      <div className="war-training-body">
        <div className="war-training-countdown-block">
          <span className="war-training-countdown-label">Kriegstag beginnt in</span>
          <strong className="war-training-countdown-value">{countdown ?? '—'}</strong>
        </div>

        <div className="war-training-meta">
          {warStartLabel && (
            <div className="war-training-meta-row">
              <span className="war-training-meta-icon">🗓</span>
              <span>{warStartLabel} Uhr</span>
            </div>
          )}
          {clanCount > 0 && (
            <div className="war-training-meta-row">
              <span className="war-training-meta-icon">⚔</span>
              <span>{clanCount} Clans nehmen teil</span>
            </div>
          )}
          {warRank != null && (
            <div className="war-training-meta-row">
              <span className="war-training-meta-icon">🏆</span>
              <span>Training-Platz <strong>#{warRank}</strong></span>
            </div>
          )}
        </div>
      </div>
    </article>
  )
}

function WarTop({ warData, warRank }) {
  if (warData?.is_training) {
    return <TrainingView warData={warData} warRank={warRank} />
  }

  const performers = warData?.performers ?? []
  const missingToday = warData?.missing_today ?? []
  const decksToday = warData?.decks_today ?? 0
  const decksTodayMax = warData?.decks_today_max ?? 0
  const decksTotal = warData?.decks_total ?? 0
  const decksTotalMax = warData?.decks_total_max ?? 0

  return (
    <article className="panel war-card">

      <header className="war-card-header">
        <span className="war-card-title">⚔ Aktueller Krieg</span>
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
