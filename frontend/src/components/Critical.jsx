function parseLastSeen(ls) {
  if (!ls) return null
  const m = ls.match(/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})/)
  if (!m) return null
  return new Date(`${m[1]}-${m[2]}-${m[3]}T${m[4]}:${m[5]}:${m[6]}.000Z`)
}

function formatLastSeen(ls) {
  const date = parseLastSeen(ls)
  if (!date) return '—'
  const formatted = date.toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' })
  const diffD = Math.floor((Date.now() - date.getTime()) / (1000 * 60 * 60 * 24))
  return `${formatted} (vor ${diffD} ${diffD === 1 ? 'Tag' : 'Tagen'})`
}

function Critical({ membersData, critical }) {
    if (!membersData) {
    return (
      <section className="panel page-stack">
        <h2>Dashboard</h2>
        <p className="message error">Clan-Tag nicht gefunden</p>
        <p className="hint">
          Hinterlege zuerst den Clan-Tag im Profile, damit Location und Ranking
          automatisch geladen werden koennen.
        </p>
      </section>
      )
    }
    
    if (!critical || critical.length === 0) {
    return <section>… keine kritischen Mitglieder.</section>
    }
    else {
        return (
            <section className="panel critical-panel">
                <h2>Kritische Mitglieder</h2>
                <p className="critical-summary">
                    Es gibt {critical.length} {critical.length === 1 ? 'kritisches' : 'kritische'} {critical.length === 1 ? 'Mitglied' : 'Mitglieder'}.
                </p>
                <div className="critical-list">
                    {critical.map(cr => (
                        <div className="critical-row" key={cr.tag}>
                            <span className="critical-name">{cr.name}</span>
                            <span className="critical-tag">{cr.tag}</span>
                            <span className="critical-seen">{formatLastSeen(cr.last_seen)}</span>
                        </div>
                    ))}
                </div>
            </section>
        )
    }
}

export default Critical