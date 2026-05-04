const API_BASE_URL = '/api'

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

export async function registerUser(username, email, password) {
  return apiRequest('/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password }),
  })
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

export async function getMembers(token) {
  return apiRequest('/members', {
    headers: createAuthHeaders(token),
  })
}

export async function getWarPerformers(token) {
  return apiRequest('/war-performers', {
    headers: createAuthHeaders(token),
  })
}

export async function getWarParticipants(token) {
  return apiRequest('/war-participants', {
    headers: createAuthHeaders(token),
  })
}

export async function getRankingsHistory(token) {
  return apiRequest('/rankings/history', {
    headers: createAuthHeaders(token),
  })
}

export async function getWarLog(token) {
  return apiRequest('/rankings/war-log', {
    headers: createAuthHeaders(token),
  })
}

// export async function getCurrentRiverRace(token) {
//   return apiRequest('/dashboard/current-riverrace', {
//     headers: createAuthHeaders(token),
//   })
// }

export { API_BASE_URL, apiRequest }
