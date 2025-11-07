import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import OperatorDashboard from './pages/OperatorDashboard';
import OperatorUserList from './pages/OperatorUserList';
import OperatorUserDetail from './pages/OperatorUserDetail';
import OperatorApprovalQueue from './pages/OperatorApprovalQueue';
import UserDashboard from './pages/UserDashboard';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/operator/dashboard" replace />} />
          <Route path="/operator/dashboard" element={<OperatorDashboard />} />
          <Route path="/operator/users" element={<OperatorUserList />} />
          <Route path="/operator/users/:userId" element={<OperatorUserDetail />} />
          <Route path="/operator/approval-queue" element={<OperatorApprovalQueue />} />
          <Route path="/user/:userId/dashboard" element={<UserDashboard />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
