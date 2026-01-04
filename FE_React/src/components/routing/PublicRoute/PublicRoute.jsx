import { useAuth } from '../../../context/AuthContext';
import { Navigate, Outlet } from 'react-router-dom';
import { getHomeRoute } from '../../../utils/authUtils';
import LoadingSpinner from '../../LoadingSpinner';

const PublicRoute = () => {
  const { isAuthenticated, user, loading } = useAuth();

  if (loading) {
    return <div className="h-screen flex items-center justify-center"><LoadingSpinner /></div>;
  }

  // If authenticated, send them to their role-specific home.
  return isAuthenticated ? <Navigate to={getHomeRoute(user)} replace /> : <Outlet />;
};

export default PublicRoute;
