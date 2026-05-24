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
    
    if (critical === null){
        return (
            <section className="panel page-stack">
                <h2>Kritische Mitglieder</h2>
                <p>Keine kritischen Mitglieder gefunden.</p>
            </section>
        )
    }
    else {
        return (
            <section className="panel page-stack">
                <h2>Kritische Mitglieder</h2>
                <p>Es gibt {critical} kritische Mitglieder.</p>
            </section>
        )
    }
}