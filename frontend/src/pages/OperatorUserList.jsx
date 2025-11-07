import { useState, useEffect } from 'react';
import { getUsers } from '../lib/apiService';
import { UserType, ConsentStatus } from '../constants/enums';

export default function OperatorUserList() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    userType: UserType.ALL,
    consentStatus: ConsentStatus.ALL,
  });
  const [pagination, setPagination] = useState({
    limit: 25,
    offset: 0,
    total: 0,
  });

  useEffect(() => {
    const fetchUsers = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const params = {
          limit: pagination.limit,
          offset: pagination.offset,
        };

        if (filters.userType !== UserType.ALL) {
          params.user_type = filters.userType;
        }

        if (filters.consentStatus !== ConsentStatus.ALL) {
          params.consent_status = filters.consentStatus === ConsentStatus.GRANTED;
        }

        const response = await getUsers(params);
        
        setUsers(response.users || response.items || []);
        setPagination(prev => ({
          ...prev,
          total: response.total || response.count || 0,
        }));
      } catch (err) {
        setError(err.message || 'Failed to fetch users');
        console.error('Error fetching users:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, [filters, pagination.limit, pagination.offset]);

  return (
    <div className="px-4 py-6 sm:px-0">
      <h1 className="text-3xl font-bold text-gray-900 mb-4">User List</h1>
      <div className="text-gray-600">
        <p>Coming soon</p>
      </div>
    </div>
  );
}

