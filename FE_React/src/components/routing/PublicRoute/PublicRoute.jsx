import { useAuth } from '../../../context/AuthContext';
import { Navigate, Outlet } from 'react-router-dom';
import LoadingSpinner from '../../LoadingSpinner';

const PublicRoute = () => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div className="h-screen flex items-center justify-center"><LoadingSpinner /></div>;
  }

  // If authenticated, send them to admin. Otherwise, let them see the public page.
  return isAuthenticated ? <Navigate to="/admin" replace /> : <Outlet />;
};

export default PublicRoute;
