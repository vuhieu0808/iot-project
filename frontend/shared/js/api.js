/**
 * GymTag - API Service Layer
 */

export const API_BASE_URL = window.location.origin.includes('5500') || window.location.origin.includes('8080') || window.location.origin.includes('5501') || window.location.origin.includes('127.0.0.1')
  ? 'http://localhost:8000'
  : window.location.origin;

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const defaultHeaders = {
    'Content-Type': 'application/json',
  };

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP Error ${response.status}`);
    }
    if (response.status === 204) {
      return true;
    }
    return await response.json();
  } catch (error) {
    console.error(`API Request Error [${endpoint}]:`, error);
    throw error;
  }
}

export const GymTagAPI = {
  // Occupancy
  getOccupancy: () => request('/api/occupancy'),

  // Environment
  getLatestEnvironment: () => request('/api/environment/latest'),
  getEnvironmentHistory: (limit = 50) => request(`/api/environment/history?limit=${limit}`),

  // Lockers
  getLockers: () => request('/api/lockers'),
  forceReleaseLocker: (lockerNumber) => request(`/api/lockers/${lockerNumber}/force-release`, { method: 'POST' }),
  forceAssignLocker: (lockerNumber, cardId) => request(`/api/lockers/${lockerNumber}/force-assign`, {
    method: 'POST',
    body: JSON.stringify({ card_id: cardId }),
  }),
  setLockerStatus: (lockerNumber, status) => request(`/api/lockers/${lockerNumber}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  }),

  // Logs
  getCheckLogs: (limit = 50, cardId = null) => {
    let url = `/api/logs?limit=${limit}`;
    if (cardId) url += `&card_id=${encodeURIComponent(cardId)}`;
    return request(url);
  },

  // Members (Admin CRUD)
  getMembers: () => request('/api/members'),
  getMemberById: (cardId) => request(`/api/members/${encodeURIComponent(cardId)}`),
  saveMember: (memberData) => request('/api/members', {
    method: 'POST',
    body: JSON.stringify(memberData),
  }),
  deleteMember: (cardId) => request(`/api/members/${encodeURIComponent(cardId)}`, {
    method: 'DELETE',
  }),
};

