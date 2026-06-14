import React from "react";
import { addExcused } from "../services/api";

function Excused({ token, members, onClose }) {
    const participants = Array.isArray(members) ? members : [];

    async function handleSubmit(event) {
        event.preventDefault();
        const player_tag= event.target.player_tag.value
        const name= participants.find(p => p.tag === player_tag)?.name
        const amount= Number(event.target.amount.value)
        const unit = event.target.unit.value
        const reason= event.target.reason.value;

        const data = {player_tag, name, amount, unit, reason}   

        try{
            await addExcused(token, data)
            onClose()
        }
        catch (err) {
            alert(err.message)
        } 


    }

    // Backdrop-Klick schließt; Klick im Card-Bereich wird gestoppt (stopPropagation).
    return (
        <div className="excuse-overlay" onClick={onClose}>
            <div className="excuse-modal" onClick={(event) => event.stopPropagation()}>
                <div className="excuse-modal-header">
                    <h2>Wen willst du entschuldigen?</h2>
                    {onClose && (
                        <button
                            type="button"
                            className="excuse-close"
                            onClick={onClose}
                            aria-label="Schließen"
                        >
                            ×
                        </button>
                    )}
                </div>

                <p className="excuse-count">{participants.length} Mitglieder verfügbar</p>

                <form className="excuse-form" onSubmit={handleSubmit}>
                    <label className="form-field">
                        <span>Name des Mitglieds</span>
                        <select name="player_tag" required defaultValue="">
                            <option value="" disabled>Bitte wählen...</option>
                            {participants.map((participant) => (
                                <option key={participant.tag ?? participant.name} value={participant.tag}>
                                    {participant.name}
                                </option>
                            ))}
                        </select>
                    </label>

                    <label className="form-field">
                        <span>Dauer der Abwesenheit</span>
                        <div className="duration-row">
                            <input type="number" name="amount" min="1" required />
                            <select name="unit">
                                <option value="days">Tag(e)</option>
                                <option value="weeks">Wochen</option>
                            </select>
                        </div>
                    </label>

                    <label className="form-field">
                        <span>Grund der Entschuldigung</span>
                        <textarea name="reason" rows={3} required></textarea>
                    </label>

                    <div className="excuse-actions">
                        {onClose && (
                            <button type="button" className="excuse-cancel" onClick={onClose}>
                                Abbrechen
                            </button>
                        )}
                        <button type="submit" className="excuse-submit">
                            Entschuldigung einreichen
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default Excused;
