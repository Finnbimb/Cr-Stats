import { useEffect, useState } from 'react'
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

import { getRankingsHistory, getWarLog } from '../services/api.js'

const COLOR_SCORE = 'var(--color-brand)'
const COLOR_RANK = '#f59e0b'
const COLOR_FAME = 'var(--color-accent-green)'

function formatDateShort(isoDate) {
  if (!isoDate) return ''
  const [y, m, d] = isoDate.split('-')
  return `${d}.${m}.`
}

function formatTimestampShort(ts) {
  if (!ts) return ''
  const d = new Date(ts * 1000)
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' })
}

function rankDomain([min, max]) {
  if (min == null || max == null || !Number.isFinite(min) || !Number.isFinite(max)) {
    return [1, 50]
  }
  const padding = Math.max(2, Math.round((max - min) * 0.25))
  return [Math.max(1, min - padding), max + padding]
}

function ChartShell({ title, subtitle, children, footer }) {
  return (
    <article className="panel ranking-chart-card">
      <header className="ranking-chart-header">
        <div>
          <h3 className="ranking-chart-title">{title}</h3>
          {subtitle && <p className="ranking-chart-subtitle">{subtitle}</p>}
        </div>
      </header>
      <div className="ranking-chart-body">
        {children}
      </div>
      {footer && <p className="ranking-chart-footer">{footer}</p>}
    </article>
  )
}

function EmptyState({ message }) {
  return (
    <div className="ranking-empty">
      <p>{message}</p>
    </div>
  )
}

function TrophyChart({ history, location }) {
  const snapshots = history?.snapshots ?? []
  const hasClan = history?.has_clan
  const hasLocation = history?.has_location

  if (!hasClan) {
    return (
      <ChartShell title="Trophäen-Bestenliste" subtitle="Verlauf der Clan-Punkte und des Rangs">
        <EmptyState message="Kein Clan hinterlegt. Trage zuerst deinen Clan-Tag im Profil ein." />
      </ChartShell>
    )
  }
  if (!hasLocation) {
    return (
      <ChartShell title="Trophäen-Bestenliste" subtitle="Verlauf der Clan-Punkte und des Rangs">
        <EmptyState message="Keine Location hinterlegt." />
      </ChartShell>
    )
  }
  if (snapshots.length === 0) {
    return (
      <ChartShell
        title="Trophäen-Bestenliste"
        subtitle={location ? `Verlauf in ${location}` : 'Verlauf der Clan-Punkte'}
      >
        <EmptyState message="Daten werden gesammelt — erster Verlauf in ein paar Tagen sichtbar." />
      </ChartShell>
    )
  }

  const ranked = snapshots.filter(s => s.trophy_rank != null)
  const data = snapshots.map(s => ({
    label: formatDateShort(s.date),
    score: s.clan_score,
    rank: s.trophy_rank,
  }))

  const ranks = ranked.map(s => s.trophy_rank)
  const rDomain = rankDomain([Math.min(...ranks), Math.max(...ranks)])

  return (
    <ChartShell
      title="Trophäen-Bestenliste"
      subtitle={location ? `Verlauf in ${location}` : 'Verlauf der Clan-Punkte'}
      footer={ranked.length === 0 ? `Clan ist aktuell nicht in der ${location ?? ''}-Bestenliste (Top 1000).` : null}
    >
      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={data} margin={{ top: 10, right: 12, bottom: 4, left: 0 }}>
          <CartesianGrid stroke="var(--border-weak)" vertical={false} />
          <XAxis dataKey="label" stroke="var(--text-muted)" fontSize={12} tickLine={false} />
          <YAxis
            yAxisId="score"
            orientation="left"
            stroke={COLOR_SCORE}
            fontSize={12}
            tickLine={false}
            tickFormatter={v => v?.toLocaleString?.('de-DE') ?? v}
          />
          <YAxis
            yAxisId="rank"
            orientation="right"
            stroke={COLOR_RANK}
            fontSize={12}
            tickLine={false}
            reversed
            domain={rDomain}
            tickFormatter={v => `#${v}`}
            allowDecimals={false}
          />
          <Tooltip
            contentStyle={{ borderRadius: 8, border: '1px solid var(--border-medium)' }}
            formatter={(value, name) => {
              if (name === 'Rang') return [`#${value}`, name]
              if (name === 'Clan-Punkte') return [Number(value).toLocaleString('de-DE'), name]
              return [value, name]
            }}
          />
          <Legend iconType="circle" wrapperStyle={{ fontSize: '0.78rem' }} />
          <Line
            yAxisId="score"
            type="monotone"
            dataKey="score"
            name="Clan-Punkte"
            stroke={COLOR_SCORE}
            strokeWidth={2.5}
            dot={false}
            connectNulls
          />
          <Line
            yAxisId="rank"
            type="monotone"
            dataKey="rank"
            name="Rang"
            stroke={COLOR_RANK}
            strokeWidth={2.5}
            strokeDasharray="4 4"
            dot={false}
            connectNulls
          />
        </ComposedChart>
      </ResponsiveContainer>
    </ChartShell>
  )
}

function WarChart({ wars, location }) {
  if (!wars || wars.length === 0) {
    return (
      <ChartShell title="Clan-Krieg" subtitle="Letzte abgeschlossene Kriege">
        <EmptyState message="Keine Kriegs-History verfügbar." />
      </ChartShell>
    )
  }

  const data = wars.map((w, i) => ({
    label: w.created_at ? formatTimestampShort(w.created_at) : `Krieg ${i + 1}`,
    fame: w.fame ?? null,
    leaderboardRank: w.leaderboard_rank ?? null,
    raceRank: w.race_rank ?? null,
  }))

  const lbRanks = wars.map(w => w.leaderboard_rank).filter(r => r != null)
  const rDomain = lbRanks.length
    ? rankDomain([Math.min(...lbRanks), Math.max(...lbRanks)])
    : [1, 50]

  const subtitle = location ? `Verlauf in ${location}` : 'Verlauf der Kriegs-Punkte'
  const noLeaderboard = lbRanks.length === 0

  return (
    <ChartShell
      title="Clan-Krieg"
      subtitle={subtitle}
      footer={
        noLeaderboard
          ? 'Bestenlisten-Rang wird ab jetzt täglich gesammelt — Verlauf in ein paar Tagen sichtbar.'
          : null
      }
    >
      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={data} margin={{ top: 10, right: 12, bottom: 4, left: 0 }}>
          <CartesianGrid stroke="var(--border-weak)" vertical={false} />
          <XAxis dataKey="label" stroke="var(--text-muted)" fontSize={12} tickLine={false} />
          <YAxis
            yAxisId="fame"
            orientation="left"
            stroke={COLOR_FAME}
            fontSize={12}
            tickLine={false}
            tickFormatter={v => v?.toLocaleString?.('de-DE') ?? v}
          />
          <YAxis
            yAxisId="rank"
            orientation="right"
            stroke={COLOR_RANK}
            fontSize={12}
            tickLine={false}
            reversed
            domain={rDomain}
            tickFormatter={v => `#${v}`}
            allowDecimals={false}
          />
          <Tooltip
            contentStyle={{ borderRadius: 8, border: '1px solid var(--border-medium)' }}
            formatter={(value, name, item) => {
              if (name === 'Bestenlisten-Rang') return [`#${value}`, name]
              if (name === 'Fame') {
                const raceRank = item?.payload?.raceRank
                const formatted = Number(value).toLocaleString('de-DE')
                return [
                  raceRank != null ? `${formatted}  (Platz im Krieg: #${raceRank})` : formatted,
                  name,
                ]
              }
              return [value, name]
            }}
          />
          <Legend iconType="circle" wrapperStyle={{ fontSize: '0.78rem' }} />
          <Line
            yAxisId="fame"
            type="monotone"
            dataKey="fame"
            name="Fame"
            stroke={COLOR_FAME}
            strokeWidth={2.5}
            dot={{ r: 3 }}
            connectNulls
          />
          <Line
            yAxisId="rank"
            type="monotone"
            dataKey="leaderboardRank"
            name="Bestenlisten-Rang"
            stroke={COLOR_RANK}
            strokeWidth={2.5}
            strokeDasharray="4 4"
            dot={{ r: 3 }}
            connectNulls
          />
        </ComposedChart>
      </ResponsiveContainer>
    </ChartShell>
  )
}

export default function Rankings({ token }) {
  const [history, setHistory] = useState(null)
  const [warLog, setWarLog] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    async function load() {
      setIsLoading(true)
      setError('')
      try {
        const [h, w] = await Promise.allSettled([
          getRankingsHistory(token),
          getWarLog(token),
        ])
        if (cancelled) return
        if (h.status === 'fulfilled') setHistory(h.value)
        if (w.status === 'fulfilled') setWarLog(w.value)
        if (h.status === 'rejected' && w.status === 'rejected') {
          setError(h.reason?.message || 'Fehler beim Laden')
        }
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }
    if (token) load()
    return () => { cancelled = true }
  }, [token])

  if (isLoading) {
    return <section className="panel">Rankings werden geladen…</section>
  }
  if (error) {
    return (
      <section className="panel page-stack">
        <p className="message error">{error}</p>
      </section>
    )
  }

  return (
    <section className="page-stack">
      <TrophyChart history={history} location={history?.location} />
      <WarChart wars={warLog?.wars} location={history?.location} />
    </section>
  )
}
