import { useState } from 'react'

function Login({ error, isLoading, onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  function handleSubmit(event) {
    event.preventDefault()
    onLogin(username, password)
  }

  return (
    <section className="panel auth-panel">
      <p className="eyebrow">Anmeldung</p>
      <h1>Login</h1>
      <p className="hint">
        Melde dich mit deinem vorhandenen Backend-User an.
      </p>

      <form className="form-stack" onSubmit={handleSubmit}>
        <label className="form-field">
          <span>Username</span>
          <input
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="z. B. finnp"
            required
          />
        </label>

        <label className="form-field">
          <span>Password</span>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Passwort"
            required
          />
        </label>

        {error ? <p className="message error">{error}</p> : null}

        <button disabled={isLoading} type="submit">
          {isLoading ? 'Lade...' : 'Einloggen'}
        </button>
      </form>
    </section>
  )
}

export default Login
