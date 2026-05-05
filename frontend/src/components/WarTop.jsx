const MEDAL = { 1: '🥇', 2: '🥈', 3: '🥉' }

const DAY_NAMES = ['Sonntag', 'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag']
const WAR_START_WEEKDAY_UTC = 4 // Donnerstag

function nextWarStart(warLog) {
  const wars = warLog?.wars
  if (!wars?.length) return null
  const last = wars[wars.length - 1]
  const lastTs = last?.created_at
  if (!lastTs) return null

  const lastDate = new Date(lastTs * 1000)
  const now = new Date()
  const target = new Date(now)
  target.setUTCHours(
    lastDate.getUTCHours(),
    lastDate.getUTCMinutes(),
    lastDate.getUTCSeconds(),
    0,
  )
  const daysUntilTarget = (WAR_START_WEEKDAY_UTC - target.getUTCDay() + 7) % 7
  target.setUTCDate(target.getUTCDate() + daysUntilTarget)
  if (target.getTime() <= now.getTime()) {
    target.setUTCDate(target.getUTCDate() + 7)
  }
  return target
}

function periodProgress(warData, warLog) {
  const wars = warLog?.wars
  if (!wars?.length) return null
  const last = wars[wars.length - 1]
  const lastTs = last?.created_at
  if (!lastTs) return null

  const lastRaceEndMs = lastTs * 1000
  const trainingEndMs = lastRaceEndMs + 3 * 24 * 60 * 60 * 1000
  const warEndMs = lastRaceEndMs + 7 * 24 * 60 * 60 * 1000
  const now = Date.now()

  const isTraining = !!warData?.is_training
  const startMs = isTraining ? lastRaceEndMs : trainingEndMs
  const endMs = isTraining ? trainingEndMs : warEndMs
  const total = endMs - startMs
  if (total <= 0) return null

  const elapsed = Math.max(0, Math.min(total, now - startMs))
  const pct = Math.round((elapsed / total) * 100)
  const remainingMs = Math.max(0, endMs - now)
  const remainingH = Math.round(remainingMs / (1000 * 60 * 60))
  let remainingLabel
  if (remainingH < 24) {
    remainingLabel = `noch ${remainingH} ${remainingH === 1 ? 'Stunde' : 'Stunden'}`
  } else {
    const d = Math.round(remainingH / 24)
    remainingLabel = `noch ${d} ${d === 1 ? 'Tag' : 'Tage'}`
  }
  return { pct, isTraining, remainingLabel }
}

function PeriodProgressBar({ progress }) {
  if (!progress) return null
  const color = progress.isTraining ? 'var(--color-brand)' : 'var(--color-accent-red)'
  const label = progress.isTraining ? 'Trainingsphase' : 'Kriegstage'
  return (
    <div className="war-period-progress">
      <div className="war-period-progress-header">
        <span className="war-stat-label">{label}</span>
        <span className="war-stat-count">{progress.remainingLabel}</span>
      </div>
      <div className="war-progress-wrap">
        <div
          className="war-progress-bar"
          style={{ width: `${progress.pct}%`, background: color }}
        />
      </div>
    </div>
  )
}

function formatWarStart(date) {
  if (!date) return null
  const now = new Date()
  const diffMs = date.getTime() - now.getTime()
  const diffH = Math.round(diffMs / (1000 * 60 * 60))

  const dayName = DAY_NAMES[date.getDay()]
  const time = date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })

  let relative
  if (diffH < 24) {
    relative = `in ${diffH} ${diffH === 1 ? 'Stunde' : 'Stunden'}`
  } else {
    const diffDays = Math.round(diffH / 24)
    relative = `in ${diffDays} ${diffDays === 1 ? 'Tag' : 'Tagen'}`
  }
  return `${dayName}, ${time} Uhr (${relative})`
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

function TrainingView({ warData, warRank, warLog }) {
  const clanCount = warData?.clan_count ?? 0
  const participantCount = warData?.participant_count ?? 0
  const warStart = nextWarStart(warLog)
  const warStartLabel = formatWarStart(warStart)
  const progress = periodProgress(warData, warLog)

  return (
    <a href="#/war" className="panel war-card war-card--link">
      <header className="war-card-header">
        <span className="war-card-title">⚔ Trainingsphase</span>
        <span className="war-top-badge">Training</span>
      </header>

      <div className="war-training-body">
        {warRank != null && (
          <div className="war-training-rank-block">
            <span className="war-rank-label">Platz</span>
            <strong className="war-rank-value">#{warRank}</strong>
            {clanCount > 0 && (
              <span className="war-training-of">von {clanCount} Clans</span>
            )}
          </div>
        )}

        <div className="war-training-meta">
          {participantCount > 0 && (
            <div className="war-training-meta-row">
              <span className="war-training-meta-icon">👥</span>
              <span>{participantCount} Mitglieder nehmen teil</span>
            </div>
          )}
          {warStartLabel && (
            <div className="war-training-meta-row">
              <span className="war-training-meta-icon">⏳</span>
              <span>Kriegstag beginnt {warStartLabel}</span>
            </div>
          )}
        </div>

        <PeriodProgressBar progress={progress} />
      </div>
    </a>
  )
}

function WarTop({ warData, warRank, warLog }) {
  if (warData?.is_training) {
    return <TrainingView warData={warData} warRank={warRank} warLog={warLog} />
  }

  const performers = warData?.performers ?? []
  const missingToday = warData?.missing_today ?? []
  const decksToday = warData?.decks_today ?? 0
  const decksTodayMax = warData?.decks_today_max ?? 0
  const decksTotal = warData?.decks_total ?? 0
  const decksTotalMax = warData?.decks_total_max ?? 0
  const progress = periodProgress(warData, warLog)

  return (
    <a href="#/war" className="panel war-card war-card--link">

      <header className="war-card-header">
        <span className="war-card-title">⚔ Aktueller Krieg</span>
        <span className="war-card-link-hint">Alle Teilnehmer →</span>
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

          <PeriodProgressBar progress={progress} />
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

    </a>
  )
}

export default WarTop
