import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import ReactMarkdown from 'react-markdown';

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
  if (!text || typeof text !== 'string') return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

/**
 * UserRecommendationCard Component
 * Displays a recommendation in the user dashboard (read-only)
 * 
 * @param {Object} props
 * @param {Object} props.recommendation - Recommendation object
 */
export default function UserRecommendationCard({ recommendation }) {
  const {
    title,
    content,
    rationale,
    persona_type,
    generated_at,
  } = recommendation;

  const [contentExpanded, setContentExpanded] = useState(false);
  const [rationaleExpanded, setRationaleExpanded] = useState(false);

  const contentPreview = truncateText(content, 150);
  const rationalePreview = truncateText(rationale, 150);
  
  // Check if content/rationale is actually truncated
  const isContentTruncated = typeof content === 'string' && content.length > 150;
  const isRationaleTruncated = typeof rationale === 'string' && rationale.length > 150;

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between mb-2">
          <CardTitle className="text-xl font-bold text-gray-900 pr-4">
            {title}
          </CardTitle>
          {persona_type && (
            <Badge
              variant="outline"
              className={getPersonaBadgeColor(persona_type)}
            >
              {getPersonaDisplayName(persona_type)}
            </Badge>
          )}
        </div>
        {generated_at && (
          <p className="text-xs text-gray-500">
            {formatDate(generated_at)}
          </p>
        )}
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Content */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Recommendation</h4>
          <div className="text-sm text-gray-700 prose prose-sm max-w-none">
            <ReactMarkdown>
              {contentExpanded || !isContentTruncated 
                ? (typeof content === 'string' ? content : '') 
                : contentPreview}
            </ReactMarkdown>
          </div>
          {isContentTruncated && (
            <button
              onClick={() => setContentExpanded(!contentExpanded)}
              className="text-sm text-blue-600 hover:text-blue-800 hover:underline mt-2"
            >
              {contentExpanded ? 'Show less' : 'Show more'}
            </button>
          )}
        </div>
        
        {/* Rationale */}
        {rationale && (
          <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded">
            <h4 className="text-sm font-semibold text-blue-900 mb-2">Why this recommendation?</h4>
            <div className="text-sm text-blue-800 prose prose-sm max-w-none">
              <ReactMarkdown>
                {rationaleExpanded || !isRationaleTruncated
                  ? (typeof rationale === 'string' ? rationale : '')
                  : rationalePreview}
              </ReactMarkdown>
            </div>
            {isRationaleTruncated && (
              <button
                onClick={() => setRationaleExpanded(!rationaleExpanded)}
                className="text-sm text-blue-700 hover:text-blue-900 hover:underline mt-2"
              >
                {rationaleExpanded ? 'Show less' : 'Show more'}
              </button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

