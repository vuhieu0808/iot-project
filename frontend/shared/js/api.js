/**
 * GymTag - Tiered API Service Layer
 */

export const API_BASE_URL = window.location.origin.includes('5500') || window.location.origin.includes('8080') || window.location.origin.includes('5501') || window.location.origin.includes('127.0.0.1')
  ? 'http://localhost:8000'
  : window.location.origin;

function getAuthToken(useUserAuth = false) {
  if (useUserAuth) {
    return sessionStorage.getItem('gymtag_user_token');
  }
  return sessionStorage.getItem('gymtag_admin_token') || sessionStorage.getItem('gymtag_user_token');
}

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const defaultHeaders = {
    'Content-Type': 'application/json',
  };

  const token = getAuthToken(options.useUserAuth);
  if (token && !options.skipAuth) {
    defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

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
  // === 1. Public Tier ===
  getPublicStatus: () => request('/api/public/status', { skipAuth: true }),
  getPublicLockers: () => request('/api/public/lockers', { skipAuth: true }),

  // === 2. User Personal Tier (Authenticated User Portal) ===
  userLogin: (cardId, password) => request('/api/user/login', {
    method: 'POST',
    body: JSON.stringify({ card_id: cardId, password }),
    skipAuth: true,
  }),

  userChangePassword: (oldPassword, newPassword) => request('/api/user/change-password', {
    method: 'POST',
    body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
    useUserAuth: true,
  }),

  getUserMeProfile: () => request('/api/user/me/profile', { useUserAuth: true }),
  getUserMeHistory: (limit = 50) => request(`/api/user/me/history?limit=${limit}`, { useUserAuth: true }),
  getUserMeLocker: () => request('/api/user/me/locker', { useUserAuth: true }),
  getUserMeStats: () => request('/api/user/me/stats', { useUserAuth: true }),

  // Legacy/Public UID Lookup (optional fallback)
  getUserProfile: (cardId) => request(`/api/user/${encodeURIComponent(cardId)}/profile`, { skipAuth: true }),
  getUserHistory: (cardId, limit = 50) => request(`/api/user/${encodeURIComponent(cardId)}/history?limit=${limit}`, { skipAuth: true }),
  getUserLocker: (cardId) => request(`/api/user/${encodeURIComponent(cardId)}/locker`, { skipAuth: true }),
  getUserStats: (cardId) => request(`/api/user/${encodeURIComponent(cardId)}/stats`, { skipAuth: true }),

  // === 3. Admin Management Tier ===
  adminLogin: (username, password) => request('/api/admin/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
    skipAuth: true,
  }),

  getAdminActivityLogs: (limit = 100, cardId = null) => {
    let url = `/api/admin/activity?limit=${limit}`;
    if (cardId) url += `&card_id=${encodeURIComponent(cardId)}`;
    return request(url);
  },

  getAdminLockers: () => request('/api/admin/lockers'),
  forceReleaseLocker: (lockerNumber) => request(`/api/admin/lockers/${lockerNumber}/force-release`, { method: 'POST' }),
  forceAssignLocker: (lockerNumber, cardId) => request(`/api/admin/lockers/${lockerNumber}/force-assign`, {
    method: 'POST',
    body: JSON.stringify({ card_id: cardId }),
  }),
  setLockerStatus: (lockerNumber, status) => request(`/api/admin/lockers/${lockerNumber}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  }),

  getAdminMembers: () => request('/api/admin/members'),
  getAdminMemberById: (cardId) => request(`/api/admin/members/${encodeURIComponent(cardId)}`),
  saveAdminMember: (memberData) => request('/api/admin/members', {
    method: 'POST',
    body: JSON.stringify(memberData),
  }),
  toggleAdminMemberActive: (cardId, isActive = null) => {
    let url = `/api/admin/members/${encodeURIComponent(cardId)}/toggle-active`;
    if (isActive !== null) url += `?is_active=${isActive}`;
    return request(url, { method: 'POST' });
  },
  resetAdminMemberPassword: (cardId) => request(`/api/admin/members/${encodeURIComponent(cardId)}/reset-password`, {
    method: 'POST',
  }),
  deleteAdminMember: (cardId) => request(`/api/admin/members/${encodeURIComponent(cardId)}`, {
    method: 'DELETE',
  }),

  getAdminEnvironmentHistory: (limit = 50) => request(`/api/admin/environment/history?limit=${limit}`),
  controlAdminFan: (command) => request('/api/admin/environment/fan', {
    method: 'POST',
    body: JSON.stringify({ command }),
  }),

  // === Threshold Settings ===
  getEnvironmentThresholds: () => request('/api/admin/environment/thresholds'),
  updateEnvironmentThresholds: (tempThreshold, humidityThreshold) => request('/api/admin/environment/thresholds', {
    method: 'PUT',
    body: JSON.stringify({
      temp_threshold: tempThreshold,
      humidity_threshold: humidityThreshold,
    }),
  }),
};

