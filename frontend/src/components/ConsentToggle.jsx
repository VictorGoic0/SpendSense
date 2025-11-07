import { useState } from 'react';
import { Switch } from './ui/switch';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { ConsentAction } from '../constants/enums';

/**
 * Format date for display
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date
 */
const formatDate = (dateString) => {
  if (!dateString) return 'Never';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return 'Never';
  }
};

/**
 * ConsentToggle Component
 * Allows users to grant or revoke consent for personalized recommendations
 * 
 * @param {Object} props
 * @param {boolean} props.consentStatus - Current consent status
 * @param {Function} props.onToggle - Callback when toggle is clicked (receives action: 'grant' or 'revoke')
 * @param {boolean} props.loading - Whether an action is in progress
 * @param {string} props.consentGrantedAt - Timestamp when consent was granted (optional)
 * @param {string} props.consentRevokedAt - Timestamp when consent was revoked (optional)
 */
export default function ConsentToggle({
  consentStatus,
  onToggle,
  loading = false,
  consentGrantedAt = null,
  consentRevokedAt = null,
}) {
  const [showGrantDialog, setShowGrantDialog] = useState(false);
  const [showRevokeDialog, setShowRevokeDialog] = useState(false);

  const handleSwitchChange = (checked) => {
    if (loading) return;
    
    if (checked && !consentStatus) {
      // User wants to grant consent
      setShowGrantDialog(true);
    } else if (!checked && consentStatus) {
      // User wants to revoke consent
      setShowRevokeDialog(true);
    }
  };

  const handleGrantConfirm = () => {
    setShowGrantDialog(false);
    onToggle(ConsentAction.GRANT);
  };

  const handleRevokeConfirm = () => {
    setShowRevokeDialog(false);
    onToggle(ConsentAction.REVOKE);
  };

  const lastUpdated = consentStatus ? consentGrantedAt : consentRevokedAt;

  return (
    <>
      <div className="flex items-center gap-4 p-4 border rounded-lg bg-white">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-lg font-semibold text-gray-900">
              Personalized Recommendations
            </h3>
            <Badge
              variant="outline"
              className={consentStatus 
                ? 'bg-green-100 text-green-800 border-green-200' 
                : 'bg-gray-100 text-gray-800 border-gray-200'
              }
            >
              {consentStatus ? 'Enabled' : 'Disabled'}
            </Badge>
          </div>
          <p className="text-sm text-gray-600 mb-1">
            {consentStatus 
              ? 'You are receiving personalized financial recommendations based on your spending patterns.'
              : 'Enable personalized recommendations to get insights tailored to your financial situation.'
            }
          </p>
          {lastUpdated && (
            <p className="text-xs text-gray-500">
              Last updated: {formatDate(lastUpdated)}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-700">
            {consentStatus ? 'On' : 'Off'}
          </span>
          <Switch
            checked={consentStatus}
            onCheckedChange={handleSwitchChange}
            disabled={loading}
          />
        </div>
      </div>

      {/* Grant Consent Dialog */}
      <Dialog open={showGrantDialog} onOpenChange={setShowGrantDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Enable Personalized Recommendations</DialogTitle>
            <DialogDescription>
              By enabling personalized recommendations, you agree to allow SpendSense to analyze your financial data and provide tailored insights.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm text-gray-700 mb-3">
              When you enable recommendations:
            </p>
            <ul className="list-disc list-inside space-y-2 text-sm text-gray-600">
              <li>We'll analyze your spending patterns and financial behavior</li>
              <li>You'll receive personalized recommendations to help improve your financial health</li>
              <li>Recommendations are reviewed by our team before being shown to you</li>
              <li>You can disable this feature at any time</li>
            </ul>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowGrantDialog(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              onClick={handleGrantConfirm}
              disabled={loading}
            >
              {loading ? 'Enabling...' : 'Enable Recommendations'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Revoke Consent Dialog */}
      <Dialog open={showRevokeDialog} onOpenChange={setShowRevokeDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Disable Personalized Recommendations</DialogTitle>
            <DialogDescription>
              Are you sure you want to disable personalized recommendations?
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm text-gray-700 mb-3">
              If you disable recommendations:
            </p>
            <ul className="list-disc list-inside space-y-2 text-sm text-gray-600">
              <li>You will no longer receive new personalized recommendations</li>
              <li>Existing recommendations will be hidden from your view</li>
              <li>We will stop analyzing your data for recommendation purposes</li>
              <li>You can re-enable this feature at any time</li>
            </ul>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowRevokeDialog(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleRevokeConfirm}
              disabled={loading}
            >
              {loading ? 'Disabling...' : 'Disable Recommendations'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

