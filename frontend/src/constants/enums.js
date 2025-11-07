/**
 * Frontend Enums
 * 
 * Centralized enum definitions for use throughout the frontend application.
 * Always use these enums instead of hardcoding string values to ensure consistency
 * and make refactoring easier.
 */

/**
 * User Type Enum
 * Represents the type of user in the system
 */
export const UserType = {
  CUSTOMER: 'customer',
  OPERATOR: 'operator',
  ALL: 'all', // For filter purposes
};

/**
 * Consent Status Enum
 * Represents the consent status of a user
 */
export const ConsentStatus = {
  GRANTED: true,
  REVOKED: false,
  ALL: 'all', // For filter purposes
};

/**
 * Consent Action Enum
 * Represents actions that can be performed on user consent
 */
export const ConsentAction = {
  GRANT: 'grant',
  REVOKE: 'revoke',
};

/**
 * Helper function to get consent status display value
 * @param {boolean|string} status - Consent status (boolean or 'all')
 * @returns {string} Display string
 */
export const getConsentStatusDisplay = (status) => {
  if (status === ConsentStatus.ALL) return 'All';
  if (status === ConsentStatus.GRANTED) return 'Granted';
  if (status === ConsentStatus.REVOKED) return 'Revoked';
  return 'Unknown';
};

/**
 * Helper function to get user type display value
 * @param {string} userType - User type
 * @returns {string} Display string
 */
export const getUserTypeDisplay = (userType) => {
  if (userType === UserType.ALL) return 'All';
  if (userType === UserType.CUSTOMER) return 'Customer';
  if (userType === UserType.OPERATOR) return 'Operator';
  return 'Unknown';
};

