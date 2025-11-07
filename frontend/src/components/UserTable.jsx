import { useNavigate } from 'react-router-dom';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from './ui/table';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { ConsentStatus, getConsentStatusDisplay } from '../constants/enums';

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
 * UserTable Component
 * Displays a table of users with their information
 * 
 * @param {Object} props
 * @param {Array} props.users - Array of user objects
 * @param {Function} props.onUserClick - Callback function when user row is clicked
 */
export default function UserTable({ users = [], onUserClick }) {
  const navigate = useNavigate();

  const handleRowClick = (userId) => {
    if (onUserClick) {
      onUserClick(userId);
    } else {
      navigate(`/operator/users/${userId}`);
    }
  };

  const handleViewDetails = (e, userId) => {
    e.stopPropagation(); // Prevent row click
    handleRowClick(userId);
  };

  // Get 30d persona for a user
  const getPersona30d = (user) => {
    if (user.personas && Array.isArray(user.personas)) {
      const persona30d = user.personas.find((p) => p.window_days === 30);
      return persona30d?.persona_type || null;
    }
    return null;
  };

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Email</TableHead>
            <TableHead>Persona (30d)</TableHead>
            <TableHead>Consent Status</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {users.length === 0 ? (
            <TableRow>
              <TableCell colSpan={5} className="text-center text-gray-500 py-8">
                No users found
              </TableCell>
            </TableRow>
          ) : (
            users.map((user) => {
              const persona30d = getPersona30d(user);
              const consentStatus = user.consent_status;

              return (
                <TableRow
                  key={user.user_id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => handleRowClick(user.user_id)}
                >
                  <TableCell className="font-medium">{user.full_name}</TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>
                    {persona30d ? (
                      <Badge
                        variant="outline"
                        className={getPersonaBadgeColor(persona30d)}
                      >
                        {getPersonaDisplayName(persona30d)}
                      </Badge>
                    ) : (
                      <span className="text-gray-400">N/A</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={
                        consentStatus === ConsentStatus.GRANTED
                          ? 'bg-green-100 text-green-800 border-green-200'
                          : 'bg-gray-100 text-gray-800 border-gray-200'
                      }
                    >
                      {getConsentStatusDisplay(consentStatus)}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => handleViewDetails(e, user.user_id)}
                    >
                      View Details
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })
          )}
        </TableBody>
      </Table>
    </div>
  );
}

