import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getUser, getConsent, getRecommendations, updateConsent } from '../lib/apiService';
import ConsentToggle from '../components/ConsentToggle';
import UserRecommendationCard from '../components/UserRecommendationCard';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { Button } from '../components/ui/button';
import { ConsentAction } from '../constants/enums';
import { AlertCircle, Sparkles, RefreshCw } from 'lucide-react';

export default function UserDashboard() {
  const { userId } = useParams();
  const [user, setUser] = useState(null);
  const [consent, setConsent] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [consentLoading, setConsentLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch all data on mount
  useEffect(() => {
    if (!userId) {
      setError('User ID is required');
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch user, consent, and recommendations in parallel
        const [userData, consentData, recommendationsData] = await Promise.all([
          getUser(userId),
          getConsent(userId),
          getRecommendations(userId, 'approved').catch(() => ({ recommendations: [], total: 0 })),
        ]);

        setUser(userData);
        setConsent(consentData);
        
        // Only set recommendations if consent is granted
        if (consentData.consent_status) {
          setRecommendations(recommendationsData.recommendations || []);
        } else {
          setRecommendations([]);
        }
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError(err.response?.data?.detail || err.message || 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [userId]);

  // Handle consent toggle
  const handleConsentToggle = async (action) => {
    try {
      setConsentLoading(true);
      setError(null);

      const response = await updateConsent(userId, action);
      
      // Update consent state
      setConsent(response);
      
      // If granting consent, fetch recommendations immediately
      if (action === ConsentAction.GRANT) {
        try {
          const recsData = await getRecommendations(userId, 'approved');
          setRecommendations(recsData.recommendations || []);
        } catch (recErr) {
          console.error('Error fetching recommendations after consent grant:', recErr);
          // Don't show error to user, recommendations will come later
        }
      } else if (action === ConsentAction.REVOKE) {
        // Clear recommendations when consent is revoked
        setRecommendations([]);
      }
    } catch (err) {
      console.error('Error updating consent:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to update consent');
    } finally {
      setConsentLoading(false);
    }
  };

  // Refresh recommendations
  const handleRefreshRecommendations = async () => {
    if (!consent?.consent_status) return;
    
    try {
      setLoading(true);
      const recsData = await getRecommendations(userId, 'approved');
      setRecommendations(recsData.recommendations || []);
    } catch (err) {
      console.error('Error refreshing recommendations:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to refresh recommendations');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !user) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error && !user) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  const consentStatus = consent?.consent_status || false;
  const hasRecommendations = recommendations.length > 0;

  return (
    <div className="px-4 py-6 sm:px-0 max-w-6xl mx-auto">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {user?.full_name || `User ${userId}`}
        </h1>
        <p className="text-gray-600">
          Your personalized financial recommendations dashboard
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert className="mb-6 border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertTitle className="text-red-800">Error</AlertTitle>
          <AlertDescription className="text-red-700">{error}</AlertDescription>
        </Alert>
      )}

      {/* Consent Toggle */}
      <div className="mb-8">
        <ConsentToggle
          consentStatus={consentStatus}
          onToggle={handleConsentToggle}
          loading={consentLoading}
          consentGrantedAt={consent?.consent_granted_at}
          consentRevokedAt={consent?.consent_revoked_at}
        />
      </div>

      {/* No Consent State */}
      {!consentStatus && (
        <Card className="border-2 border-dashed border-gray-300">
          <CardHeader>
            <div className="flex items-center gap-3 mb-2">
              <Sparkles className="h-6 w-6 text-blue-600" />
              <CardTitle className="text-xl">Enable Personalized Recommendations</CardTitle>
            </div>
            <CardDescription>
              Get insights tailored to your financial situation
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p className="text-gray-700">
                By enabling personalized recommendations, you'll receive:
              </p>
              <ul className="list-disc list-inside space-y-2 text-gray-600">
                <li>Actionable insights based on your spending patterns</li>
                <li>Personalized advice to improve your financial health</li>
                <li>Recommendations reviewed by our financial experts</li>
                <li>Regular updates as your financial situation evolves</li>
              </ul>
              <p className="text-sm text-gray-500 mt-4">
                Use the toggle above to enable recommendations and get started!
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recommendations Section */}
      {consentStatus && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                Your Personalized Recommendations
              </h2>
              <p className="text-gray-600 mt-1">
                {hasRecommendations 
                  ? `${recommendations.length} recommendation${recommendations.length !== 1 ? 's' : ''} available`
                  : 'Recommendations are being prepared for you'
                }
              </p>
            </div>
            {hasRecommendations && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefreshRecommendations}
                disabled={loading}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            )}
          </div>

          {/* Recommendations List */}
          {hasRecommendations ? (
            <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
              {recommendations.slice(0, 5).map((recommendation) => (
                <UserRecommendationCard
                  key={recommendation.recommendation_id}
                  recommendation={recommendation}
                />
              ))}
            </div>
          ) : (
            <Card className="border-2 border-dashed border-gray-300">
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <Sparkles className="h-6 w-6 text-blue-600" />
                  <CardTitle className="text-xl">Recommendations Coming Soon</CardTitle>
                </div>
                <CardDescription>
                  We're preparing personalized recommendations for you
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <p className="text-gray-700">
                    Our team is analyzing your financial data and preparing personalized recommendations. 
                    This process typically takes a few hours.
                  </p>
                  <p className="text-sm text-gray-500">
                    Check back soon, or we'll notify you when your recommendations are ready!
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
