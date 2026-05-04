import { useState, useMemo } from 'react'

const SORT_OPTIONS = [
  { value: 'decks_used', label: 'Gesamt gespielt' },
  { value: 'fame', label: 'Fame' },
  { value: 'decks_used_today', label: 'Heute gespielt' },
]

function ProgressBar({ value, max, color = 'var(--color-brand)' }) {
  const pct = max > 0 ? Math.min(100, Math.round((value / max) * 100)) : 0
  return (
    <div className="war-progress-wrap">
      <div className="war-progress-bar" style={{ width: `${pct}%`, background: color }} />
    </div>
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
          {clanCount > 0 && <span className="war-training-of">von {clanCount} Clans</span>}
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

export default function War({ warData, participantsData, isLoading }) {
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState('decks_used')
  const [reversed, setReversed] = useState(false)

  if (isLoading) {
    return <section className="panel">War-Daten werden geladen...</section>
  }

  const participants = participantsData?.participants ?? []
  const isTraining = (participantsData ?? warData)?.is_training ?? false

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    let list = q
      ? participants.filter(p => p.name.toLowerCase().includes(q))
      : [...participants]

    list.sort((a, b) => b[sortBy] - a[sortBy])
    if (reversed) list.reverse()
    return list
  }, [participants, search, sortBy, reversed])

  return (
    <section className="page-stack">
      <WarHeader data={participantsData ?? warData} />

      <div className="panel">
        <div className="war-controls">
          <input
            className="war-search"
            type="text"
            placeholder="Name suchen…"
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
                <th>Name</th>
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
