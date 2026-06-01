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

function Excused({ members }) {
    const participants = Array.isArray(members) ? members : [];
    return(
        <div className= "background war-card">
            <div className="excused">
                <h2>Wen willst du entschuldigen?</h2>
                <p>{participants.length > 0 && participants[0]?.name ? `Ausgewählt: ${participants[0].name}` : 'Kein Mitglied ausgewählt'}</p>
                <form onSubmit={handleSubmit}>
                    <label>
                        Name des Mitglieds:
                        <select name="name" required defaultValue="">
                            <option value="" disabled>Bitte wählen...</option>
                            {participants.map((participant) => (
                                <option key={participant.tag ?? participant.name} value={participant.name}>
                                    {participant.name}
                                </option>
                            ))}
                        </select>
                    </label>
                    <br />
                    <label>
                        Grund der Entschuldigung:
                        <textarea name="reason" required></textarea>
                    </label>
                    <br />
                    <button type="submit">Entschuldigung einreichen</button>
                </form>
            </div>
        </div>
    )
}

export default Excused