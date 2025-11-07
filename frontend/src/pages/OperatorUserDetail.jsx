import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getUser, getUserProfile, getOperatorUserSignals } from '../lib/apiService';

export default function OperatorUserDetail() {
  const { userId } = useParams();
  
  // State variables
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [signals, setSignals] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch all data on mount
  useEffect(() => {
    const fetchUserData = async () => {
      if (!userId) return;
      
      setLoading(true);
      setError(null);
      
      try {
        // Fetch user, profile, and signals in parallel
        const [userData, profileData, signalsData] = await Promise.all([
          getUser(userId),
          getUserProfile(userId),
          getOperatorUserSignals(userId),
        ]);
        
        // Update state with response data
        setUser(userData);
        setProfile(profileData);
        setSignals(signalsData);
      } catch (err) {
        console.error('Error fetching user data:', err);
        setError(err.response?.data?.detail || err.message || 'Failed to fetch user data');
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, [userId]);

  return (
    <div className="px-4 py-6 sm:px-0">
      <h1 className="text-3xl font-bold text-gray-900 mb-4">User Detail</h1>
      <div className="text-gray-600">
        <p>User ID: {userId}</p>
        {loading && <p className="mt-2">Loading...</p>}
        {error && <p className="mt-2 text-red-600">Error: {error}</p>}
        {!loading && !error && <p className="mt-2">Coming soon</p>}
      </div>
    </div>
  );
}

