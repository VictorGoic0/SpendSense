import api from './api';
import { ConsentAction } from '../constants/enums';

/**
 * Get list of users
 * @param {Object} params - Query parameters
 * @returns {Promise} API response
 */
export async function getUsers(params = {}) {
  const response = await api.get('/users', { params });
  return response.data;
}

/**
 * Get user by ID
 * @param {string|number} userId - User ID
 * @returns {Promise} API response
 */
export async function getUser(userId) {
  const response = await api.get(`/users/${userId}`);
  return response.data;
}

/**
 * Get user profile with features and personas
 * @param {string|number} userId - User ID
 * @param {number} window - Time window in days (optional)
 * @returns {Promise} API response
 */
export async function getUserProfile(userId, window = null) {
  const params = window ? { window } : {};
  const response = await api.get(`/profile/${userId}`, { params });
  return response.data;
}

/**
 * Get recommendations for a user
 * @param {string|number} userId - User ID
 * @param {string} status - Recommendation status filter (optional)
 * @returns {Promise} API response
 */
export async function getRecommendations(userId, status = null) {
  const params = status ? { status } : {};
  const response = await api.get(`/recommendations/${userId}`, { params });
  return response.data;
}

/**
 * Get operator dashboard data
 * @returns {Promise} API response
 */
export async function getOperatorDashboard() {
  const response = await api.get('/operator/dashboard');
  return response.data;
}

/**
 * Get user signals for operator view
 * @param {string|number} userId - User ID
 * @returns {Promise} API response
 */
export async function getOperatorUserSignals(userId) {
  const response = await api.get(`/operator/users/${userId}/signals`);
  return response.data;
}

/**
 * Get approval queue
 * @param {string} status - Status filter (optional)
 * @returns {Promise} API response
 */
export async function getApprovalQueue(status = null) {
  const params = status ? { status } : {};
  const response = await api.get('/operator/review', { params });
  return response.data;
}

/**
 * Approve a recommendation
 * @param {string|number} recId - Recommendation ID
 * @param {string|number} operatorId - Operator ID
 * @param {string} notes - Approval notes (optional)
 * @returns {Promise} API response
 */
export async function approveRecommendation(recId, operatorId, notes = '') {
  const response = await api.post(`/recommendations/${recId}/approve`, {
    operator_id: operatorId,
    notes,
  });
  return response.data;
}

/**
 * Bulk approve recommendations
 * @param {string|number} operatorId - Operator ID
 * @param {Array<string|number>} recIds - Array of recommendation IDs
 * @returns {Promise} API response
 */
export async function bulkApprove(operatorId, recIds) {
  const response = await api.post('/recommendations/bulk-approve', {
    operator_id: operatorId,
    recommendation_ids: recIds,
  });
  return response.data;
}

/**
 * Update user consent
 * @param {string|number} userId - User ID
 * @param {string} action - Consent action (use ConsentAction enum: ConsentAction.GRANT or ConsentAction.REVOKE)
 * @returns {Promise} API response
 */
export async function updateConsent(userId, action) {
  const response = await api.post('/consent', {
    user_id: userId,
    action,
  });
  return response.data;
}

/**
 * Get user consent status
 * @param {string|number} userId - User ID
 * @returns {Promise} API response
 */
export async function getConsent(userId) {
  const response = await api.get(`/consent/${userId}`);
  return response.data;
}

/**
 * Override a recommendation
 * @param {string|number} recId - Recommendation ID
 * @param {string|number} operatorId - Operator ID
 * @param {string} reason - Reason for override (required)
 * @param {string} newTitle - New title (optional)
 * @param {string} newContent - New content (optional)
 * @returns {Promise} API response
 */
export async function overrideRecommendation(recId, operatorId, reason, newTitle = null, newContent = null) {
  const payload = {
    operator_id: operatorId,
    reason,
  };
  if (newTitle) payload.new_title = newTitle;
  if (newContent) payload.new_content = newContent;
  
  const response = await api.post(`/recommendations/${recId}/override`, payload);
  return response.data;
}

/**
 * Reject a recommendation
 * @param {string|number} recId - Recommendation ID
 * @param {string|number} operatorId - Operator ID
 * @param {string} reason - Reason for rejection (required)
 * @returns {Promise} API response
 */
export async function rejectRecommendation(recId, operatorId, reason) {
  const response = await api.post(`/recommendations/${recId}/reject`, {
    operator_id: operatorId,
    reason,
  });
  return response.data;
}

/**
 * Generate recommendations for a user
 * @param {string|number} userId - User ID
 * @param {number} windowDays - Time window in days (optional, default: 30)
 * @param {boolean} forceRegenerate - Force regeneration even if recommendations exist (optional, default: false)
 * @returns {Promise} API response
 */
export async function generateRecommendations(userId, windowDays = 30, forceRegenerate = false) {
  const params = {
    window_days: windowDays,
    force_regenerate: forceRegenerate,
  };
  const response = await api.post(`/recommendations/generate/${userId}`, null, { params });
  return response.data;
}

