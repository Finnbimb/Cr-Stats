import { useEffect, useState } from 'react'
import {
  getLocations,
  getProfile,
  updateClanTag,
  updateLocation,
} from '../services/api.js'

function Profile({ onUnauthorized, token }) {
  const [profile, setProfile] = useState(null)
  const [clanTag, setClanTag] = useState('')
  const [locations, setLocations] = useState([])
  const [selectedLocationId, setSelectedLocationId] = useState('')

  const [error, setError] = useState('')
  const [locationsError, setLocationsError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingLocations, setIsLoadingLocations] = useState(true)
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
        setSelectedLocationId(data.location_id ? String(data.location_id) : '')
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

    async function loadLocations() {
      try {
        const data = await getLocations(token)

        if (!isActive) {
          return
        }

        const locationOptions = Array.isArray(data) ? data : []
        setLocations(locationOptions)
      } catch (loadError) {
        if (!isActive) {
          return
        }

        if (loadError.status === 401) {
          onUnauthorized()
          return
        }

        setLocationsError(loadError.message)
      } finally {
        if (isActive) {
          setIsLoadingLocations(false)
        }
      }
    }

    setError('')
    setLocationsError('')
    setSuccessMessage('')
    setIsLoading(true)
    setIsLoadingLocations(true)

    loadProfile()
    loadLocations()

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
      const normalizedClanTag = clanTag.trim()
      const currentLocationId = profile?.location_id ? String(profile.location_id) : ''
      const shouldUpdateClanTag =
        normalizedClanTag !== '' && normalizedClanTag !== (profile?.clan_tag || '')
      const shouldUpdateLocation =
        selectedLocationId !== '' && selectedLocationId !== currentLocationId

      if (!shouldUpdateClanTag && !shouldUpdateLocation) {
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
        }
        setClanTag(clanData.clan_tag)
        savedFields.push('Clan-Tag')
      }

      if (shouldUpdateLocation) {
        const locationData = await updateLocation(token, Number(selectedLocationId))
        nextProfile = {
          ...nextProfile,
          location_id: locationData.location_id,
          location: locationData.location,
        }
        setSelectedLocationId(String(locationData.location_id))
        savedFields.push('Location')
      }

      setProfile(nextProfile)
      setSuccessMessage(`${savedFields.join(' und ')} gespeichert.`)
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
    <section className="page-stack">
      <div className="panel">
        <p className="eyebrow">Profile</p>
        <h2>Settings</h2>
        <p className="hint">
          Hier kannst du den Clan-Tag setzen. Die Locations werden beim
          Öffnen der Seite automatisch geladen.
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
        <p className="hint">
          Das Backend setzt das `#` automatisch, falls du es weglaesst.
        </p>
        <div className="form-field">
          <span>Location</span>
          <select
            value={selectedLocationId}
            onChange={(event) => setSelectedLocationId(event.target.value)}
            disabled={isLoadingLocations || locations.length === 0}
          >
            <option value="">
              {isLoadingLocations ? 'Locations werden geladen...' : 'Bitte auswählen'}
            </option>
            {locations.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </div>

        {error ? <p className="message error">{error}</p> : null}
        {locationsError ? <p className="message error">{locationsError}</p> : null}
        {successMessage ? <p className="message success">{successMessage}</p> : null}

        <button disabled={isSaving} type="submit">
          {isSaving ? 'Speichert...' : 'Profil speichern'}
        </button>
      </form>
    </section>
  )
}

export default Profile
