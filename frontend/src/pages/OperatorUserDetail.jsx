import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getUser, getUserProfile, getOperatorUserSignals, getRecommendations, generateRecommendations } from '../lib/apiService';
import UserInfoCard from '../components/UserInfoCard';
import PersonaDisplay from '../components/PersonaDisplay';
import SignalDisplay from '../components/SignalDisplay';
import { Button } from '../components/ui/button';
import { Alert, AlertTitle, AlertDescription } from '../components/ui/alert';
import { Skeleton } from '../components/ui/skeleton';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import ReactMarkdown from 'react-markdown';
import { Check } from 'lucide-react';

const SIGNAL_TYPES = ['subscriptions', 'savings', 'credit', 'income'];

export default function OperatorUserDetail() {
  const { userId } = useParams();
  const navigate = useNavigate();
  
  // State variables
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [signals, setSignals] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeSignalType, setActiveSignalType] = useState('subscriptions');
  const [expandedContent, setExpandedContent] = useState(new Set());

  // Fetch all data on mount
  useEffect(() => {
    const fetchUserData = async () => {
      if (!userId) return;
      
      setLoading(true);
      setError(null);
      
      try {
        // Fetch user, profile, signals, and recommendations in parallel
        const [userData, profileData, signalsData, recommendationsData] = await Promise.all([
          getUser(userId),
          getUserProfile(userId),
          getOperatorUserSignals(userId),
          getRecommendations(userId).catch(() => ({ recommendations: [] })), // Don't fail if no recommendations
        ]);
        
        // Update state with response data
        setUser(userData);
        setProfile(profileData);
        setSignals(signalsData);
        setRecommendations(recommendationsData.recommendations || recommendationsData || []);
      } catch (err) {
        console.error('Error fetching user data:', err);
        setError(err.response?.data?.detail || err.message || 'Failed to fetch user data');
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, [userId]);

  const handleRetry = () => {
    setError(null);
    setLoading(true);
    const fetchUserData = async () => {
      try {
        const [userData, profileData, signalsData, recommendationsData] = await Promise.all([
          getUser(userId),
          getUserProfile(userId),
          getOperatorUserSignals(userId),
          getRecommendations(userId).catch(() => ({ recommendations: [] })),
        ]);
        setUser(userData);
        setProfile(profileData);
        setSignals(signalsData);
        setRecommendations(recommendationsData.recommendations || recommendationsData || []);
        setError(null);
      } catch (err) {
        setError(err.response?.data?.detail || err.message || 'Failed to fetch user data');
      } finally {
        setLoading(false);
      }
    };
    fetchUserData();
  };

  // Get personas from profile
  const getPersona30d = () => {
    if (!profile?.personas) return null;
    return profile.personas.find(p => p.window_days === 30);
  };

  const getPersona180d = () => {
    if (!profile?.personas) return null;
    return profile.personas.find(p => p.window_days === 180);
  };

  // Handle generate recommendations button click (non-blocking)
  const handleGenerateRecommendations = () => {
    if (!userId) return;
    
    // Fire and forget - no loading state, no blocking
    // Request runs in background; recommendations will appear on page refresh
    generateRecommendations(userId, 30, false)
      .catch((error) => {
        // Silently handle errors - user can retry if needed
        console.error('Error generating recommendations:', error);
      });
  };

  // Loading skeleton
  if (loading) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="mb-6">
          <Skeleton className="h-10 w-32 mb-4" />
          <Skeleton className="h-8 w-64" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-6">
            <Skeleton className="h-64" />
            <Skeleton className="h-48" />
            <Skeleton className="h-48" />
          </div>
          <div className="space-y-6">
            <Skeleton className="h-12" />
            <Skeleton className="h-96" />
            <Skeleton className="h-96" />
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <Button
          variant="outline"
          onClick={() => navigate('/operator/users')}
          className="mb-4"
        >
          ← Back to User List
        </Button>
        <Alert variant="destructive">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <Button onClick={handleRetry} className="mt-4">
          Retry
        </Button>
      </div>
    );
  }

  // Main content
  const signals30d = signals?.['30d_signals'];
  const signals180d = signals?.['180d_signals'];

  return (
    <div className="px-4 py-6 sm:px-0">
      {/* Back button */}
      <Button
        variant="outline"
        onClick={() => navigate('/operator/users')}
        className="mb-6"
      >
        ← Back to User List
      </Button>

      {/* Page header */}
      <h1 className="text-3xl font-bold text-gray-900 mb-6">User Detail</h1>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left column */}
        <div className="space-y-6">
          <UserInfoCard user={user} />
          
          <PersonaDisplay 
            persona={getPersona30d()} 
            title="30-Day Persona"
          />
          
          <PersonaDisplay 
            persona={getPersona180d()} 
            title="180-Day Persona"
          />
        </div>

        {/* Right column */}
        <div className="space-y-6">
          {/* Tab navigation for signal types */}
          <div className="flex gap-2 border-b">
            {SIGNAL_TYPES.map((type) => (
              <button
                key={type}
                onClick={() => setActiveSignalType(type)}
                className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
                  activeSignalType === type
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </button>
            ))}
          </div>

          {/* Signal display for selected tab (30d) */}
          {signals30d && (
            <SignalDisplay
              signals={signals30d}
              signalType={activeSignalType}
              title={`30-Day ${activeSignalType.charAt(0).toUpperCase() + activeSignalType.slice(1)} Signals`}
              profile={profile}
            />
          )}

          {/* Signal display for 180d */}
          {signals180d && (
            <SignalDisplay
              signals={signals180d}
              signalType={activeSignalType}
              title={`180-Day ${activeSignalType.charAt(0).toUpperCase() + activeSignalType.slice(1)} Signals`}
              profile={profile}
            />
          )}
        </div>
      </div>

      {/* Recommendations section */}
      <div className="mt-8">
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>Recommendations</CardTitle>
              <Button variant="outline" size="sm" onClick={handleGenerateRecommendations}>
                Generate Recommendations
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {recommendations && recommendations.length > 0 ? (
              <div className="space-y-4">
                {recommendations.map((rec) => {
                  const isExpanded = expandedContent.has(rec.recommendation_id);
                  const isProduct = rec.content_type === 'partner_offer';
                  
                  // For products, show short_description initially
                  // For education, show content
                  const initialContent = isProduct 
                    ? (rec.short_description || '')
                    : (typeof rec.content === 'string' ? rec.content : '');
                  
                  const isTruncated = initialContent.length > 200;
                  const displayContent = isExpanded || !isTruncated 
                    ? initialContent 
                    : initialContent.substring(0, 200) + '...';
                  
                  // Parse benefits if it's a product
                  let benefitsList = [];
                  if (isProduct && rec.benefits) {
                    if (Array.isArray(rec.benefits)) {
                      benefitsList = rec.benefits;
                    } else if (typeof rec.benefits === 'string') {
                      try {
                        benefitsList = JSON.parse(rec.benefits || '[]');
                      } catch (e) {
                        console.error('Error parsing benefits:', e);
                        benefitsList = [];
                      }
                    }
                  }
                  
                  return (
                    <div key={rec.recommendation_id} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold text-gray-900">
                            {isProduct ? (rec.product_name || rec.title) : rec.title}
                          </h4>
                          {isProduct && (
                            <Badge
                              variant="outline"
                              className="bg-purple-100 text-purple-800 border-purple-200"
                            >
                              Partner Offer
                            </Badge>
                          )}
                        </div>
                        <Badge
                          variant="outline"
                          className={
                            rec.status === 'approved'
                              ? 'bg-green-100 text-green-800 border-green-200'
                              : rec.status === 'pending_approval'
                              ? 'bg-yellow-100 text-yellow-800 border-yellow-200'
                              : 'bg-gray-100 text-gray-800 border-gray-200'
                          }
                        >
                          {rec.status?.replace('_', ' ')}
                        </Badge>
                      </div>
                      
                      {/* Initial content (short_description for products, content for education) */}
                      <div className="text-sm text-gray-600">
                        <ReactMarkdown>{displayContent}</ReactMarkdown>
                      </div>
                      
                      {/* Expanded product details */}
                      {isProduct && isExpanded && (
                        <div className="mt-4 space-y-3 pt-3 border-t">
                          {rec.partner_name && (
                            <p className="text-sm text-gray-600">
                              <span className="font-semibold">Partner:</span> {rec.partner_name}
                            </p>
                          )}
                          {rec.typical_apy_or_fee && (
                            <p className="text-sm text-gray-600">
                              <span className="font-semibold">Rate/Fee:</span> {rec.typical_apy_or_fee}
                            </p>
                          )}
                          {benefitsList && benefitsList.length > 0 && (
                            <div>
                              <p className="text-sm font-semibold text-gray-700 mb-2">Benefits:</p>
                              <ul className="space-y-1">
                                {benefitsList.map((benefit, index) => (
                                  <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
                                    <Check className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                                    <span>{benefit}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {rec.disclosure && (
                            <p className="text-xs text-gray-500 italic mt-2">
                              {rec.disclosure}
                            </p>
                          )}
                        </div>
                      )}
                      
                      {/* Show more/less button */}
                      {(isTruncated || (isProduct && !isExpanded)) && (
                        <button
                          onClick={() => {
                            const newExpanded = new Set(expandedContent);
                            if (isExpanded) {
                              newExpanded.delete(rec.recommendation_id);
                            } else {
                              newExpanded.add(rec.recommendation_id);
                            }
                            setExpandedContent(newExpanded);
                          }}
                          className="text-sm text-blue-600 hover:text-blue-800 hover:underline mt-1"
                        >
                          {isExpanded ? 'Show less' : 'Show more'}
                        </button>
                      )}
                      
                      {/* Rationale */}
                      {rec.rationale && (
                        <div className="mt-3 pt-3 border-t">
                          <p className="text-xs font-semibold text-gray-700 mb-1">Rationale:</p>
                          <p className="text-sm text-gray-600">
                            <ReactMarkdown>{rec.rationale}</ReactMarkdown>
                          </p>
                        </div>
                      )}
                      
                      {rec.generated_at && (
                        <p className="text-xs text-gray-500 mt-2">
                          Generated: {new Date(rec.generated_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-gray-500">No recommendations yet. Click "Generate Recommendations" to create some.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
