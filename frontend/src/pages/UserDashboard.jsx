import { useParams } from 'react-router-dom';

export default function UserDashboard() {
  const { userId } = useParams();

  return (
    <div className="px-4 py-6 sm:px-0">
      <h1 className="text-3xl font-bold text-gray-900 mb-4">User Dashboard</h1>
      <div className="text-gray-600">
        <p>User ID: {userId}</p>
        <p className="mt-2">Coming soon</p>
      </div>
    </div>
  );
}

