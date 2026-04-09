const API_BASE_URL = 'http://127.0.0.1:8000'

async function parseResponse(response) {
  const text = await response.text()
  let data = null

  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }
  }

  if (!response.ok) {
    const message =
      (typeof data === 'object' && data?.detail) ||
      (typeof data === 'string' && data) ||
      `Request failed with status ${response.status}`
    const error = new Error(message)
    error.status = response.status
    throw error
  }

  return data
}

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options)
  return parseResponse(response)
}

function createAuthHeaders(token, extraHeaders = {}) {
  return {
    Authorization: `Bearer ${token}`,
    ...extraHeaders,
  }
}

export async function loginUser(username, password) {
  return apiRequest('/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
      username,
      password,
    }),
  })
}

export async function getDashboard(token) {
  return apiRequest('/dashboard', {
    headers: createAuthHeaders(token),
  })
}

export async function getProfile(token) {
  return apiRequest('/profile', {
    headers: createAuthHeaders(token),
  })
}

export async function updateClanTag(token, clanTag) {
  return apiRequest('/profile/clan_tag', {
    method: 'PUT',
    headers: createAuthHeaders(token, {
      'Content-Type': 'application/json',
    }),
    body: JSON.stringify({
      clan_tag: clanTag,
    }),
  })
}

export async function getLocations(token) {
  return apiRequest('/locations', {
    headers: createAuthHeaders(token),
  })
}

export async function updateLocation(token, locationId) {
  return apiRequest('/profile/location', {
    method: 'PUT',
    headers: createAuthHeaders(token, {
      'Content-Type': 'application/json',
    }),
    body: JSON.stringify({
      location_id: locationId,
    }),
  })
}

// export async function getCurrentRiverRace(token) {
//   return apiRequest('/dashboard/current-riverrace', {
//     headers: createAuthHeaders(token),
//   })
// }

export { API_BASE_URL, apiRequest }
