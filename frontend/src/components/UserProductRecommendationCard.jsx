import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import ReactMarkdown from 'react-markdown';
import { ExternalLink, Check } from 'lucide-react';

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
 * UserProductRecommendationCard Component
 * Displays a product recommendation in the user dashboard (read-only)
 * Designed as a taller card for side-by-side display
 * 
 * @param {Object} props
 * @param {Object} props.recommendation - Recommendation object with product data
 */
export default function UserProductRecommendationCard({ recommendation }) {
  const {
    product_name,
    partner_name,
    short_description,
    benefits,
    typical_apy_or_fee,
    partner_link,
    disclosure,
    rationale,
    persona_type,
    generated_at,
  } = recommendation;

  const [rationaleExpanded, setRationaleExpanded] = useState(false);

  // Parse benefits if it's a string
  let benefitsList = [];
  if (benefits) {
    if (Array.isArray(benefits)) {
      benefitsList = benefits;
    } else if (typeof benefits === 'string') {
      try {
        benefitsList = JSON.parse(benefits || '[]');
      } catch (e) {
        console.error('Error parsing benefits:', e);
        benefitsList = [];
      }
    }
  }

  const rationalePreview = truncateText(rationale, 150);
  const isRationaleTruncated = typeof rationale === 'string' && rationale.length > 150;

  return (
    <Card className="hover:shadow-md transition-shadow bg-gradient-to-br from-blue-50 to-purple-50 border-blue-200">
      <CardHeader className="relative pb-6 pt-6">
        {/* Persona badge in top right */}
        {persona_type && (
          <div className="absolute top-4 right-4">
            <Badge
              variant="outline"
              className={getPersonaBadgeColor(persona_type)}
            >
              {getPersonaDisplayName(persona_type)}
            </Badge>
          </div>
        )}
        {/* Centered content */}
        <div className="text-center pt-2">
          <Badge
            variant="outline"
            className="bg-purple-100 text-purple-800 border-purple-200 mb-2"
          >
            Partner Offer
          </Badge>
          <CardTitle className="text-xl font-bold text-gray-900">
            {product_name || 'Product Recommendation'}
          </CardTitle>
          {partner_name && (
            <p className="text-sm text-gray-600 mt-1">
              by {partner_name}
            </p>
          )}
          {generated_at && (
            <p className="text-xs text-gray-500 mt-2">
              {formatDate(generated_at)}
            </p>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Short Description */}
        {short_description && (
          <div>
            <p className="text-sm text-gray-700">
              {short_description}
            </p>
          </div>
        )}

        {/* APY or Fee */}
        {typical_apy_or_fee && (
          <div className="bg-white rounded-lg p-3 border border-blue-200">
            <p className="text-sm font-semibold text-gray-700 mb-1">Rate/Fee</p>
            <p className="text-lg font-bold text-blue-600">
              {typical_apy_or_fee}
            </p>
          </div>
        )}

        {/* Benefits List */}
        {benefitsList && benefitsList.length > 0 && (
          <div className="bg-white rounded-lg p-4 border border-blue-200">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Key Benefits</h4>
            <ul className="space-y-2">
              {benefitsList.map((benefit, index) => (
                <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                  <Check className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>{benefit}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Learn More Button */}
        {partner_link && (
          <Button
            variant="default"
            className="w-full"
            onClick={() => window.open(partner_link, '_blank', 'noopener,noreferrer')}
          >
            Learn More
            <ExternalLink className="h-4 w-4 ml-2" />
          </Button>
        )}

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

        {/* Disclosure */}
        {disclosure && (
          <div className="pt-2 border-t border-gray-200">
            <p className="text-xs text-gray-500 italic">
              {disclosure}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

