import { useState, useMemo } from 'react'
import RaceClansSidebar from '../components/RaceClansSidebar.jsx'
import Excused from '../components/Excused.jsx'
import ExcusedList from '../components/ExcusedList.jsx'

const SORT_OPTIONS = [
  { value: 'decks_used', label: 'Gesamt gespielt' },
  { value: 'fame', label: 'Fame' },
  { value: 'decks_used_today', label: 'Heute gespielt' },
]

const TRAINING_DAYS = 3
const WAR_DAYS = 4
const TOTAL_DAYS = TRAINING_DAYS + WAR_DAYS
const SHORT_DAYS = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa']

function ProgressBar({ value, max, color = 'var(--color-brand)' }) {
  const pct = max > 0 ? Math.min(100, Math.round((value / max) * 100)) : 0
  return (
    <div className="war-progress-wrap">
      <div className="war-progress-bar" style={{ width: `${pct}%`, background: color }} />
    </div>
  )
}

function formatRemaining(ms) {
  const totalH = Math.max(0, Math.floor(ms / (1000 * 60 * 60)))
  if (totalH < 24) {
    return `noch ${totalH} ${totalH === 1 ? 'Stunde' : 'Stunden'}`
  }
  const d = Math.floor(totalH / 24)
  const h = totalH % 24
  if (h === 0) return `noch ${d} ${d === 1 ? 'Tag' : 'Tage'}`
  return `noch ${d} ${d === 1 ? 'Tag' : 'Tage'} ${h} Std`
}

function formatDayTime(ms) {
  const d = new Date(ms)
  const day = SHORT_DAYS[d.getDay()]
  const time = d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
  return `${day} ${time}`
}

function WeekProgress({ warData, warLog }) {
  const wars = warLog?.wars
  if (!wars?.length) return null
  const lastTs = wars[wars.length - 1]?.created_at
  if (!lastTs) return null

  const lastRaceEndMs = lastTs * 1000
  const trainingEndMs = lastRaceEndMs + TRAINING_DAYS * 24 * 60 * 60 * 1000
  const raceEndMs = lastRaceEndMs + TOTAL_DAYS * 24 * 60 * 60 * 1000
  const totalMs = raceEndMs - lastRaceEndMs
  const nowMs = Date.now()

  const elapsedTotal = Math.max(0, Math.min(totalMs, nowMs - lastRaceEndMs))
  const nowPct = (elapsedTotal / totalMs) * 100

  const isTraining = !!warData?.is_training
  const trainingFillPct = Math.max(0, Math.min(100,
    ((nowMs - lastRaceEndMs) / (trainingEndMs - lastRaceEndMs)) * 100,
  ))
  const warFillPct = Math.max(0, Math.min(100,
    ((nowMs - trainingEndMs) / (raceEndMs - trainingEndMs)) * 100,
  ))

  const phaseEndMs = isTraining ? trainingEndMs : raceEndMs
  const remainingLabel = formatRemaining(phaseEndMs - nowMs)
  const phaseLabel = isTraining ? 'Training läuft' : 'Kriegstage laufen'

  return (
    <article className="panel war-week">
      <header className="war-week-header">
        <h3 className="war-week-title">Kriegswoche</h3>
        <span className="war-week-remaining">
          <span className="war-week-phase-label">{phaseLabel}</span>
          <span className="war-week-phase-sep">·</span>
          {remainingLabel}
        </span>
      </header>

      <div className="war-week-track">
        <div className="war-week-segment war-week-segment--training" style={{ flex: TRAINING_DAYS }}>
          <div className="war-week-fill war-week-fill--training" style={{ width: `${trainingFillPct}%` }} />
        </div>
        <div className="war-week-segment war-week-segment--war" style={{ flex: WAR_DAYS }}>
          <div className="war-week-fill war-week-fill--war" style={{ width: `${warFillPct}%` }} />
        </div>

        <div className="war-week-now" style={{ left: `${nowPct}%` }} aria-label="aktueller Zeitpunkt" />
      </div>

      <div className="war-week-labels">
        <div className="war-week-label-group">
          <span className="war-week-phase">Training</span>
          <span className="war-week-time">{formatDayTime(lastRaceEndMs)}</span>
        </div>
        <div className="war-week-label-group war-week-label-group--mid" style={{ left: `${(TRAINING_DAYS / TOTAL_DAYS) * 100}%` }}>
          <span className="war-week-phase">Kriegstage</span>
          <span className="war-week-time">{formatDayTime(trainingEndMs)}</span>
        </div>
        <div className="war-week-label-group war-week-label-group--right">
          <span className="war-week-phase">Race-Ende</span>
          <span className="war-week-time">{formatDayTime(raceEndMs)}</span>
        </div>
      </div>
    </article>
  )
}

function WarHeader({ data }) {
  const warRank = data?.war_rank
  const clanCount = data?.clan_count ?? 0
  const isTraining = data?.is_training
  const decksToday = data?.decks_today ?? 0
  const decksTodayMax = data?.decks_today_max ?? 0
  const decksTotal = data?.decks_total ?? 0
  const decksTotalMax = data?.decks_total_max ?? 0

  return (
    <div className="panel war-page-header">
      <div className="war-page-overview">
        <div className="war-card-rank">
          {warRank != null
            ? <><span className="war-rank-label">Platz</span><strong className="war-rank-value">#{warRank}</strong></>
            : <strong className="war-rank-value">—</strong>
          }
          {clanCount > 0 && <span className="war-training-of">von {clanCount}</span>}
        </div>

        <div className="war-page-badge-wrap">
          <span className={`war-top-badge${isTraining ? '' : ' war-top-badge--active'}`}>
            {isTraining ? 'Training' : 'Kriegstag'}
          </span>
        </div>
      </div>

      {!isTraining && (
        <div className="war-page-bars">
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
      )}
    </div>
  )
}

export default function War({ warData, participantsData, warLog, isLoading, token, membersData, excused, onDashboardInvalidate }) {
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState('decks_used')
  const [reversed, setReversed] = useState(false)

  const participants = participantsData?.participants ?? []
  const isTraining = (participantsData ?? warData)?.is_training ?? false

  const [showExcuseForm, setShowExcuseForm] = useState(false)

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    let list = q
      ? participants.filter(p => p.name.toLowerCase().includes(q))
      : [...participants]

    list.sort((a, b) => b[sortBy] - a[sortBy])
    if (reversed) list.reverse()
    return list
  }, [participants, search, sortBy, reversed])

  if (isLoading) {
    return <section className="panel">War-Daten werden geladen...</section>
  }

  return (
    <section className="page-stack">
      <div className="war-header-row">
        <RaceClansSidebar raceClans={participantsData?.race_clans} />
        <WarHeader data={participantsData ?? warData} />
        <div className="excused">
          <ExcusedList excused={excused} />
          <button onClick={() => {if (!showExcuseForm) setShowExcuseForm(true); else setShowExcuseForm(false)}}>Abmeldung hinzufügen</button>
      </div>
      
      {showExcuseForm && <Excused token={token} members={membersData} onClose={() => setShowExcuseForm(false)} onDashboardInvalidate={() => {onDashboardInvalidate()}} />}
      </div>
      <WeekProgress warData={participantsData ?? warData} warLog={warLog} />

      <div className="panel">
        <div className="war-controls">
          <input
            className="war-search"
            type="text"
            placeholder="Suchen…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />

          <div className="war-controls-right">
            <div className="war-sort-group">
              {SORT_OPTIONS.map(opt => (
                <button
                  key={opt.value}
                  className={`war-sort-btn${sortBy === opt.value ? ' active' : ''}`}
                  onClick={() => setSortBy(opt.value)}
                >
                  {opt.label}
                </button>
              ))}
            </div>

            <button
              className={`war-reverse-btn${reversed ? ' active' : ''}`}
              onClick={() => setReversed(v => !v)}
              title="Reihenfolge umkehren"
            >
              {reversed ? '↑' : '↓'}
            </button>
          </div>
        </div>

        {filtered.length === 0 ? (
          <p className="hint" style={{ marginTop: '1rem' }}>
            {participants.length === 0 ? 'Keine Teilnehmer gefunden.' : 'Kein Treffer für diese Suche.'}
          </p>
        ) : (
          <table className="members-table war-participants-table">
            <thead>
              <tr>
                <th className="members-rank">#</th>
                <th className="war-header-name">Name</th>
                <th className="war-col-fame">Fame</th>
                <th className="war-col-decks">Heute</th>
                <th className="war-col-decks">Gesamt (Kriegstage)</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p, i) => (
                <tr key={p.tag} className={p.is_current_member ? '' : 'war-row--ex-member'}>
                  <td className="members-rank">{reversed ? filtered.length - i : i + 1}</td>
                  <td className="war-participant-name">
                    {p.name}
                    {!p.is_current_member && <span className="war-ex-badge">Ex</span>}
                  </td>
                  <td className="war-col-fame war-fame-value">{p.fame.toLocaleString()}</td>
                  <td className={`war-col-decks${!isTraining && p.decks_used_today === 0 && p.is_current_member ? ' war-decks--zero' : ''}`}>
                    {p.decks_used_today} / 4
                  </td>
                  <td className="war-col-decks">{p.decks_used}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  )
}
