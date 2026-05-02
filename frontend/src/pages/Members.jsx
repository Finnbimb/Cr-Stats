import { useEffect, useState } from 'react'
import { getMembers } from '../services/api.js'

const ROLE_LABEL = {
  leader:    'Anführer',
  coLeader:  'Vize',
  elder:     'Ältester',
  member:    'Mitglied',
}

function Members({ token, onUnauthorized }) {
  const [members, setMembers] = useState(null)
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    getMembers(token)
      .then(data => { if (active) setMembers(data.members) })
      .catch(err => {
        if (!active) return
        if (err.status === 401) { onUnauthorized(); return }
        setError(err.message)
      })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [token])

  return (
    <section className="page-stack">
      <header className="topbar">
        <div>
          <p className="eyebrow">CrStats</p>
          <h1>Mitglieder</h1>
        </div>
      </header>

      <div className="panel">
        {loading && <p className="hint">Lade Mitglieder…</p>}
        {error   && <p className="message error">{error}</p>}

        {members && (
          <table className="members-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Name</th>
                <th>Rolle</th>
                <th>Trophäen</th>
                <th>Clan War</th>
              </tr>
            </thead>
            <tbody>
              {members.map((m, i) => (
                <tr key={m.tag}>
                  <td className="members-rank">{m.clan_rank ?? i + 1}</td>
                  <td className="members-name">{m.name}</td>
                  <td>
                    <span className={`members-role members-role--${m.role}`}>
                      {ROLE_LABEL[m.role] ?? m.role}
                    </span>
                  </td>
                  <td className="members-trophies">🏆 {m.trophies?.toLocaleString()}</td>
                  <td className="members-cw hint">—</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  )
}

export default Members
