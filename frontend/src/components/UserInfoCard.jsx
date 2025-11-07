import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { ConsentStatus, getConsentStatusDisplay, getUserTypeDisplay } from '../constants/enums';

/**
 * UserInfoCard Component
 * Displays user information in a card format
 * 
 * @param {Object} props
 * @param {Object} props.user - User object with user data
 */
export default function UserInfoCard({ user }) {
  if (!user) {
    return null;
  }

  const formatDate = (dateString) => {
    if (!dateString) return null;
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch  {
      return null;
    }
  };

  const consentStatus = user.consent_status;
  const consentGrantedAt = formatDate(user.consent_granted_at);
  const consentRevokedAt = formatDate(user.consent_revoked_at);

  return (
    <Card>
      <CardHeader>
        <CardTitle>User Information</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label className="text-sm font-medium text-gray-500">Name</label>
          <p className="text-lg font-semibold text-gray-900">{user.full_name}</p>
        </div>

        <div>
          <label className="text-sm font-medium text-gray-500">Email</label>
          <p className="text-base text-gray-900">{user.email}</p>
        </div>

        <div>
          <label className="text-sm font-medium text-gray-500">User Type</label>
          <p className="text-base text-gray-900">{getUserTypeDisplay(user.user_type)}</p>
        </div>

        <div>
          <label className="text-sm font-medium text-gray-500">Consent Status</label>
          <div className="mt-1">
            <Badge
              variant="outline"
              className={
                consentStatus === ConsentStatus.GRANTED
                  ? 'bg-green-100 text-green-800 border-green-200'
                  : 'bg-gray-100 text-gray-800 border-gray-200'
              }
            >
              {getConsentStatusDisplay(consentStatus)}
            </Badge>
          </div>
        </div>

        {consentGrantedAt && (
          <div>
            <label className="text-sm font-medium text-gray-500">Consent Granted</label>
            <p className="text-base text-gray-900">{consentGrantedAt}</p>
          </div>
        )}

        {consentRevokedAt && (
          <div>
            <label className="text-sm font-medium text-gray-500">Consent Revoked</label>
            <p className="text-base text-gray-900">{consentRevokedAt}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

