const MEDAL = { 1: '🥇', 2: '🥈', 3: '🥉' }

function WarTop({ warData }) {
  const label = warData?.is_training ? 'Letzter Krieg' : 'Aktueller Krieg'
  const performers = warData?.performers ?? []

  return (
    <article className="panel war-top">
      <header className="war-top-header">
        <span className="war-top-title">Top 3 Clankrieg</span>
        <span className="war-top-badge">{label}</span>
      </header>

      {performers.length === 0 ? (
        <p className="hint">Keine Daten verfügbar</p>
      ) : (
        <ol className="war-top-list">
          {performers.map((p) => (
            <li key={p.tag} className="war-top-row">
              <span className="war-top-medal">{MEDAL[p.rank] ?? `#${p.rank}`}</span>
              <span className="war-top-name">{p.name}</span>
              <span className="war-top-fame">{p.fame.toLocaleString()} Fame</span>
            </li>
          ))}
        </ol>
      )}
    </article>
  )
}

export default WarTop
