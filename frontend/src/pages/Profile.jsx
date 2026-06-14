import { useEffect, useState } from 'react'
import {
  getProfile,
  updateClanTag,
} from '../services/api.js'

function Profile({ onUnauthorized, token, onDashboardInvalidate }) {
  const [profile, setProfile] = useState(null)
  const [clanTag, setClanTag] = useState('')

  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    let isActive = true

    async function loadProfile() {
      try {
        const data = await getProfile(token)

        if (!isActive) {
          return
        }

        setProfile(data)
        setClanTag(data.clan_tag || '')
      } catch (loadError) {
        if (!isActive) {
          return
        }

        if (loadError.status === 401) {
          onUnauthorized()
          return
        }

        setError(loadError.message)
      } finally {
        if (isActive) {
          setIsLoading(false)
        }
      }
    }

    setError('')
    setSuccessMessage('')
    setIsLoading(true)

    loadProfile()

    return () => {
      isActive = false
    }
  }, [onUnauthorized, token])

  async function handleSubmit(event) {
    event.preventDefault()
    setIsSaving(true)
    setError('')
    setSuccessMessage('')

    try {
      const trimmedClanTag = clanTag.trim().toUpperCase()
      const normalizedClanTag = trimmedClanTag.startsWith('#')
        ? trimmedClanTag
        : `#${trimmedClanTag}`
      const shouldUpdateClanTag =
        trimmedClanTag !== '' &&
        (
          normalizedClanTag !== (profile?.clan_tag || '') ||
          !profile?.location_id ||
          !profile?.location
        )

      if (!shouldUpdateClanTag) {
        setSuccessMessage('Keine Änderungen zum Speichern.')
        return
      }

      let nextProfile = profile
      const savedFields = []

      if (shouldUpdateClanTag) {
        const clanData = await updateClanTag(token, normalizedClanTag)
        nextProfile = {
          ...nextProfile,
          clan_tag: clanData.clan_tag,
          location_id: clanData.location_id,
          location: clanData.location,
        }
        setClanTag(clanData.clan_tag)
        savedFields.push('Clan-Tag und Location')
      }

      setProfile(nextProfile)
      setSuccessMessage(`${savedFields.join(' und ')} gespeichert.`)
      onDashboardInvalidate()
    } catch (saveError) {
      if (saveError.status === 401) {
        onUnauthorized()
        return
      }

      setError(saveError.message)
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return <section className="panel">Profile wird geladen...</section>
  }

  return (
    <>
      <section className="page-stack">
        <div className="panel">
          <p className="eyebrow">Profile</p>
          <h2>Settings</h2>
          <p className="hint">
            Hier kannst du den Clan-Tag setzen. Die Location wird automatisch
            aus den Clash-Royale-Clandaten übernommen.
          </p>
        </div>

        <div className="panel profile-info">
          <p>
            <strong>Username:</strong> {profile?.username}
          </p>
          <p>
            <strong>Email:</strong> {profile?.email}
          </p>
          <p>
            <strong>Gespeicherter Clan-Tag:</strong>{' '}
            {profile?.clan_tag || 'Noch nicht gesetzt'}
          </p>
          <p>
            <strong>Gespeicherte Location:</strong>{' '}
            {profile?.location || 'Noch nicht gesetzt'}
          </p>
        </div>

        <form className="panel form-stack" onSubmit={handleSubmit}>
          <label className="form-field">
            <span>Clan Tag</span>
            <input
              value={clanTag}
              onChange={(event) => setClanTag(event.target.value)}
              placeholder="#ABCD123"
            />
          </label>

          {error ? <p className="message error">{error}</p> : null}
          {successMessage ? <p className="message success">{successMessage}</p> : null}

          <button disabled={isSaving} type="submit">
            {isSaving ? 'Speichert...' : 'Profil speichern'}
          </button>
        </form>
      </section>
    </>
  )
}

export default Profile
