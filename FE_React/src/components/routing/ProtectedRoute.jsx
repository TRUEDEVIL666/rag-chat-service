import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import LoadingSpinner from '../LoadingSpinner';
import { getHomeRoute } from '../../utils/authUtils';

const ProtectedRoute = ({ allowedRoles = [] }) => {
  const { isAuthenticated, user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  // 1. Not Authenticated -> Redirect to Login (save location)
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  // 2. Authenticated but check roles (if any specified)
  if (allowedRoles.length > 0) {
    const userRole = user?.app_metadata?.role;
    if (!allowedRoles.includes(userRole)) {
      // Role mismatch -> Redirect to their appropriate home
      return <Navigate to={getHomeRoute(user)} replace />;
    }
  }

  // 3. Authorized -> Render content
  return <Outlet />;
};

export default ProtectedRoute;
