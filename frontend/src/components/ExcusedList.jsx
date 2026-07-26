function ExcusedList({ excused }) {
    if (!excused || excused.length === 0) {
        return <p>Keine entschuldigten Mitglieder.</p>
    }

    return (
        <div className="excused-list">
            <h3>Entschuldigte Mitglieder</h3>
            <ul>
                {excused.map((member) => (
                    <li key={member.player_tag}>
                        {member.name}, {member.reason}
                    </li>
                ))}
            </ul>
        </div>
    )
}
export default ExcusedList