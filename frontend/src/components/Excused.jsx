import React from "react";

function handleSubmit(event) {
    event.preventDefault();
    const name = event.target.name.value;
    const reason = event.target.reason.value;
    // Hier kannst du die Logik hinzufügen, um die Entschuldigung zu verarbeiten,
    // z.B. eine API-Anfrage senden oder den Zustand aktualisieren.
    console.log(`Entschuldigung eingereicht für ${name} mit Grund: ${reason}`);
    alert(`Entschuldigung eingereicht für ${name} mit Grund: ${reason}`);
}

function Excused({ members, onClose }) {
    const participants = Array.isArray(members) ? members : [];

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
                        <select name="name" required defaultValue="">
                            <option value="" disabled>Bitte wählen...</option>
                            {participants.map((participant) => (
                                <option key={participant.tag ?? participant.name} value={participant.name}>
                                    {participant.name}
                                </option>
                            ))}
                        </select>
                    </label>

                    <label requred className="form-field">
                        <span>Dauer der Abwesenheit</span>
                        <select>
                            <option value="">Tag(e)</option>
                            <option value="1">Wochen</option>
                        </select>
                        <input type="number" name="amount" required />
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
