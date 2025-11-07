import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Badge } from './ui/badge';

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
 * @returns {string} Tailwind color class
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
 * PersonaDisplay Component
 * Displays persona information in a card format
 * 
 * @param {Object} props
 * @param {Object} props.persona - Persona object with type, confidence_score, assigned_at, window_days
 * @param {string} props.title - Optional title for the card (e.g., "30-Day Persona")
 */
export default function PersonaDisplay({ persona, title }) {
  if (!persona || !persona.persona_type) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title || 'Persona'}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-500">No persona assigned</p>
        </CardContent>
      </Card>
    );
  }

  const formatDate = (dateString) => {
    if (!dateString) return null;
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
      return null;
    }
  };

  const formatConfidence = (confidence) => {
    if (confidence === null || confidence === undefined) return 'N/A';
    return `${(confidence * 100).toFixed(1)}%`;
  };

  const personaType = persona.persona_type;
  const confidence = persona.confidence_score;
  const assignedAt = formatDate(persona.assigned_at);
  const windowDays = persona.window_days;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title || `${windowDays}-Day Persona`}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label className="text-sm font-medium text-gray-500">Persona Type</label>
          <div className="mt-2">
            <Badge
              variant="outline"
              className={`${getPersonaBadgeColor(personaType)} text-lg px-4 py-2`}
            >
              {getPersonaDisplayName(personaType)}
            </Badge>
          </div>
        </div>

        <div>
          <label className="text-sm font-medium text-gray-500">Confidence Score</label>
          <p className="text-2xl font-semibold text-gray-900 mt-1">
            {formatConfidence(confidence)}
          </p>
        </div>

        {assignedAt && (
          <div>
            <label className="text-sm font-medium text-gray-500">Assigned Date</label>
            <p className="text-base text-gray-900 mt-1">{assignedAt}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

