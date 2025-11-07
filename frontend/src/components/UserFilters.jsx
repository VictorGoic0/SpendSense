import { UserType, ConsentStatus, getUserTypeDisplay, getConsentStatusDisplay } from '../constants/enums';

/**
 * UserFilters Component
 * Provides filter controls for user type and consent status
 * 
 * @param {Object} props
 * @param {Object} props.filters - Current filter values { userType, consentStatus }
 * @param {Function} props.onFilterChange - Callback when filters change { userType?, consentStatus? }
 */
export default function UserFilters({ filters, onFilterChange }) {
  const handleUserTypeChange = (e) => {
    const value = e.target.value;
    onFilterChange({ userType: value });
  };

  const handleConsentStatusChange = (e) => {
    const value = e.target.value;
    // Convert string back to boolean or 'all'
    let consentStatus;
    if (value === 'all') {
      consentStatus = ConsentStatus.ALL;
    } else if (value === 'true') {
      consentStatus = ConsentStatus.GRANTED;
    } else {
      consentStatus = ConsentStatus.REVOKED;
    }
    onFilterChange({ consentStatus });
  };

  // Convert consent status enum to string value for select
  const getConsentStatusValue = () => {
    if (filters.consentStatus === ConsentStatus.ALL) return 'all';
    if (filters.consentStatus === ConsentStatus.GRANTED) return 'true';
    return 'false';
  };

  return (
    <div className="flex flex-wrap gap-4 items-end mb-6">
      {/* User Type Filter */}
      <div className="flex flex-col gap-2 min-w-[180px]">
        <label htmlFor="user-type-filter" className="text-sm font-medium text-gray-700">
          User Type
        </label>
        <select
          id="user-type-filter"
          value={filters.userType || UserType.ALL}
          onChange={handleUserTypeChange}
          className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
        >
          <option value={UserType.ALL}>{getUserTypeDisplay(UserType.ALL)}</option>
          <option value={UserType.CUSTOMER}>{getUserTypeDisplay(UserType.CUSTOMER)}</option>
          <option value={UserType.OPERATOR}>{getUserTypeDisplay(UserType.OPERATOR)}</option>
        </select>
      </div>

      {/* Consent Status Filter */}
      <div className="flex flex-col gap-2 min-w-[180px]">
        <label htmlFor="consent-status-filter" className="text-sm font-medium text-gray-700">
          Consent Status
        </label>
        <select
          id="consent-status-filter"
          value={getConsentStatusValue()}
          onChange={handleConsentStatusChange}
          className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
        >
          <option value="all">{getConsentStatusDisplay(ConsentStatus.ALL)}</option>
          <option value="true">{getConsentStatusDisplay(ConsentStatus.GRANTED)}</option>
          <option value="false">{getConsentStatusDisplay(ConsentStatus.REVOKED)}</option>
        </select>
      </div>
    </div>
  );
}

