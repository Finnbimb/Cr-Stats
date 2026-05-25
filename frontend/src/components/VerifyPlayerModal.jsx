import { useState } from 'react'
import '../modal.css'
import { checkPlayerTagExists } from '../services/api'

function VerifyPlayerModal({ onClose, onSuccess }) {
    const [playerTag, setPlayerTag] = useState('')
    const [token, setToken] = useState('')

    function handleSubmit(e) {
        e.preventDefault()
        checkPlayerTagExists({
            player_tag: playerTag,
            token: token,
        })
            .then(res => {
                if (res.exists) {
                    onSuccess()
                } else {
                    alert('Der Spieler-Tag konnte nicht verifiziert werden. Bitte überprüfe die Eingabe und versuche es erneut.')
                }
            })
            .catch(() => {
                alert('Fehler bei der Verifizierung des Spieler-Tags. Bitte versuche es später erneut.')
            })
    }

    return (
        <div className="modal-overlay">
            <div className="modal-card">
                <h2>Player-Tag verifizieren</h2>
                <form onSubmit={handleSubmit}>
                    <label>
                        <input
                            type="text"
                            value={playerTag}
                            onChange={e => setPlayerTag(e.target.value)}
                            placeholder="Spieler-Tag (z.B. #ABCD123)"
                            required
                        />
                    </label>
                    <label>
                        <input
                            type="text"
                            value={token}
                            onChange={e => setToken(e.target.value)}
                            placeholder="Token"
                            required
                        />
                    </label>
                    <button type="submit">Verifizieren</button>
                </form>
                <button onClick={onClose}>Abbrechen</button>
            </div>
        </div>
    )
}

export default VerifyPlayerModal
