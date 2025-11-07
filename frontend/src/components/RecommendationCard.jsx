import { Card, CardHeader, CardTitle, CardContent, CardFooter } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Checkbox } from './ui/checkbox';

/**
 * Helper function to get persona display name
 * @param {string} personaType - Persona type from backend
 * @returns {string} Display name
 */
const getPersonaDisplayName = (personaType) => {
  if (!personaType) return 'N/A';
  return personaType
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

/**
 * Helper function to get persona badge color
 * @param {string} personaType - Persona type
 * @returns {string} Tailwind color classes
 */
const getPersonaBadgeColor = (personaType) => {
  const colors = {
    high_utilization: 'bg-red-100 text-red-800 border-red-200',
    variable_income: 'bg-orange-100 text-orange-800 border-orange-200',
    subscription_heavy: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    savings_builder: 'bg-green-100 text-green-800 border-green-200',
    wealth_builder: 'bg-blue-100 text-blue-800 border-blue-200',
  };
  return colors[personaType] || 'bg-gray-100 text-gray-800 border-gray-200';
};

/**
 * Helper function to get status badge color
 * @param {string} status - Recommendation status
 * @returns {string} Tailwind color classes
 */
const getStatusBadgeColor = (status) => {
  const colors = {
    pending_approval: 'bg-blue-100 text-blue-800 border-blue-200',
    approved: 'bg-green-100 text-green-800 border-green-200',
    overridden: 'bg-amber-100 text-amber-800 border-amber-200',
    rejected: 'bg-red-100 text-red-800 border-red-200',
  };
  return colors[status] || 'bg-gray-100 text-gray-800 border-gray-200';
};

/**
 * Format date for display
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date
 */
const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
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
    return 'N/A';
  }
};

/**
 * Truncate text to specified length
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated text
 */
const truncateText = (text, maxLength = 150) => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

/**
 * RecommendationCard Component
 * Displays a recommendation in the approval queue
 * 
 * @param {Object} props
 * @param {Object} props.recommendation - Recommendation object
 * @param {Function} props.onApprove - Callback when approve button clicked
 * @param {Function} props.onReject - Callback when reject button clicked
 * @param {Function} props.onOverride - Callback when override button clicked
 * @param {Function} props.onSelect - Callback when checkbox clicked
 * @param {boolean} props.isSelected - Whether this recommendation is selected
 * @param {boolean} props.isLoading - Whether an action is in progress
 */
export default function RecommendationCard({
  recommendation,
  onApprove,
  onReject,
  onOverride,
  onSelect,
  isSelected = false,
  isLoading = false,
}) {
  const {
    recommendation_id,
    user_name,
    user_id,
    title,
    content,
    rationale,
    status,
    persona_type,
    generated_at,
  } = recommendation;

  const contentPreview = truncateText(content, 150);
  const rationalePreview = truncateText(rationale, 100);

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex items-start gap-4">
          {/* Checkbox for selection */}
          <div className="pt-1">
            <Checkbox
              checked={isSelected}
              onCheckedChange={(checked) => onSelect(recommendation_id, checked)}
              disabled={isLoading}
            />
          </div>
          
          {/* Main content */}
          <div className="flex-1">
            <div className="flex items-start justify-between mb-2">
              <CardTitle className="text-xl font-bold text-gray-900 pr-4">
                {title}
              </CardTitle>
              <div className="flex gap-2 flex-shrink-0">
                <Badge
                  variant="outline"
                  className={getStatusBadgeColor(status)}
                >
                  {status.replace('_', ' ').toUpperCase()}
                </Badge>
              </div>
            </div>
            
            {/* User and persona info */}
            <div className="flex items-center gap-3 mb-3">
              <span className="text-sm font-medium text-gray-700">
                {user_name || user_id}
              </span>
              <Badge
                variant="outline"
                className={getPersonaBadgeColor(persona_type)}
              >
                {getPersonaDisplayName(persona_type)}
              </Badge>
              <span className="text-xs text-gray-500">
                {formatDate(generated_at)}
              </span>
            </div>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        {/* Content preview */}
        <div className="mb-4">
          <h4 className="text-sm font-semibold text-gray-700 mb-1">Content:</h4>
          <p className="text-sm text-gray-600 whitespace-pre-wrap">
            {contentPreview}
          </p>
        </div>
        
        {/* Rationale preview */}
        {rationalePreview && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-1">Rationale:</h4>
            <p className="text-sm text-gray-600">
              {rationalePreview}
            </p>
          </div>
        )}
      </CardContent>
      
      <CardFooter className="flex justify-end gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onOverride(recommendation)}
          disabled={isLoading || status === 'approved'}
        >
          Override
        </Button>
        <Button
          variant="destructive"
          size="sm"
          onClick={() => onReject(recommendation)}
          disabled={isLoading || status === 'approved'}
        >
          Reject
        </Button>
        <Button
          variant="default"
          size="sm"
          onClick={() => onApprove(recommendation)}
          disabled={isLoading || status === 'approved'}
        >
          Approve
        </Button>
      </CardFooter>
    </Card>
  );
}

