import { useState, useEffect, useRef, useCallback } from 'react';
import { getUsers } from '../lib/apiService';
import { UserType, ConsentStatus } from '../constants/enums';
import UserFilters from '../components/UserFilters';
import UserTable from '../components/UserTable';
import UserTableSkeleton from '../components/UserTableSkeleton';
import Pagination from '../components/Pagination';
import { Alert, AlertTitle, AlertDescription } from '../components/ui/alert';
import { Button } from '../components/ui/button';

export default function OperatorUserList() {
  const [users, setUsers] = useState([]);
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');
  const debounceTimeoutRef = useRef(null);
  
  const [filters, setFilters] = useState({
    userType: UserType.ALL,
    consentStatus: ConsentStatus.ALL,
  });
  const [pagination, setPagination] = useState({
    limit: 25,
    offset: 0,
    total: 0,
  });

  // Debounce search input
  useEffect(() => {
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    debounceTimeoutRef.current = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, 300);

    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, [searchTerm]);

  // Filter users locally by name or email
  useEffect(() => {
    if (!debouncedSearchTerm.trim()) {
      setFilteredUsers(users);
      return;
    }

    const searchLower = debouncedSearchTerm.toLowerCase().trim();
    const filtered = users.filter((user) => {
      const nameMatch = user.full_name?.toLowerCase().includes(searchLower);
      const emailMatch = user.email?.toLowerCase().includes(searchLower);
      return nameMatch || emailMatch;
    });

    setFilteredUsers(filtered);
  }, [users, debouncedSearchTerm]);

  const fetchUsers = useCallback(async () => {
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
  }, [filters, pagination.limit, pagination.offset]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  // Handle filter changes
  const handleFilterChange = (newFilters) => {
    setFilters(prev => ({
      ...prev,
      ...newFilters,
    }));
    // Reset to first page when filters change
    setPagination(prev => ({
      ...prev,
      offset: 0,
    }));
  };

  // Handle pagination changes
  const handlePageChange = (page) => {
    const newOffset = (page - 1) * pagination.limit;
    setPagination(prev => ({
      ...prev,
      offset: newOffset,
    }));
  };

  // Handle search input change
  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  // Handle refresh button click
  const handleRefresh = () => {
    fetchUsers();
  };

  // Calculate current page and total pages for Pagination component
  // Use filteredUsers length for local search, otherwise use server total
  const displayUsers = debouncedSearchTerm.trim() ? filteredUsers : users;
  const currentPage = Math.floor(pagination.offset / pagination.limit) + 1;
  const totalPages = debouncedSearchTerm.trim() 
    ? Math.ceil(filteredUsers.length / pagination.limit)
    : Math.ceil(pagination.total / pagination.limit);

  return (
    <div className="px-4 py-6 sm:px-0">
      {/* Page Header with Search */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <h1 className="text-3xl font-bold text-gray-900">User List</h1>
        
        {/* Search Input */}
        <div className="flex-1 max-w-md">
          <input
            type="text"
            placeholder="Search by name or email..."
            value={searchTerm}
            onChange={handleSearchChange}
            className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
          />
        </div>
      </div>

      {/* Filters */}
      <UserFilters filters={filters} onFilterChange={handleFilterChange} />

      {/* Loading State */}
      {loading && <UserTableSkeleton />}

      {/* Error State */}
      {error && !loading && (
        <Alert className="mb-4 border-red-200 bg-red-50">
          <AlertTitle className="text-red-800">Error Loading Users</AlertTitle>
          <AlertDescription className="text-red-700 mt-2">
            {error}
          </AlertDescription>
          <div className="mt-4">
            <Button onClick={handleRefresh} variant="outline" size="sm">
              Retry
            </Button>
          </div>
        </Alert>
      )}

      {/* User Table */}
      {!loading && !error && (
        <>
          {displayUsers.length === 0 ? (
            <div className="text-center py-12 border rounded-md bg-gray-50">
              <p className="text-gray-500 text-lg mb-2">No users found</p>
              <p className="text-gray-400 text-sm">
                {debouncedSearchTerm.trim() 
                  ? 'Try adjusting your search or filters'
                  : 'No users match the current filters'}
              </p>
            </div>
          ) : (
            <>
              <UserTable users={displayUsers} />
              
              {/* Pagination */}
              {totalPages > 1 && (
                <Pagination
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={handlePageChange}
                />
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}

