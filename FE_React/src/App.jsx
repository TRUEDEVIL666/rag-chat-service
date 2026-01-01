import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import AuthLayout from './components/layout/AuthLayout';
import AdminLayout from './components/layout/AdminLayout';
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import Dashboard from './pages/admin/Dashboard';
import Settings from './pages/admin/Settings';
import BotList from './pages/admin/bots/BotList';
import CreateBot from './pages/admin/bots/CreateBot';
import EditBot from './pages/admin/bots/EditBot';
import BotKBConfigPage from './pages/admin/bots/BotKBConfigPage';
import DocumentList from './pages/admin/documents/DocumentList';
import UploadDocument from './pages/admin/documents/UploadDocument';
import UserList from './pages/admin/users/UserList';
import CreateUser from './pages/admin/users/CreateUser';
import Chatbot from './pages/admin/Chatbot';
import AiProviderModelPage from './pages/admin/ai-models/AiProviderModelPage';




import PublicRoute from './components/routing/PublicRoute';
import PrivateRoute from './components/routing/PrivateRoute';

const RootRedirect = () => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return null;
  return isAuthenticated ? <Navigate to="/admin" replace /> : <Navigate to="/login" replace />;
};

function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <BrowserRouter>
          <Toaster position="top-right" />
          <Routes>
            {/* Root Redirect */}
            <Route path="/" element={<RootRedirect />} />

            {/* Public Routes (Guests Only) */}
            <Route element={<PublicRoute />}>
              <Route element={<AuthLayout />}>
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
              </Route>
            </Route>

            {/* Protected Routes (Users Only) */}
            <Route element={<PrivateRoute />}>
              <Route path="/admin" element={<AdminLayout />}>
                <Route index element={<Navigate to="dashboard" replace />} />
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="settings" element={<Settings />} />

                <Route path="bots" element={<BotList />} />
                <Route path="bots/create" element={<CreateBot />} />
                <Route path="bots/edit/:id" element={<EditBot />} />
                <Route path="bots/:id/kbs" element={<BotKBConfigPage />} />
                <Route path="chat/:id" element={<Chatbot />} />
                <Route path="documents" element={<DocumentList />} />
                <Route path="documents/upload" element={<UploadDocument />} />
                <Route path="users" element={<UserList />} />
                <Route path="users/create" element={<CreateUser />} />
                <Route path="ai-models" element={<AiProviderModelPage />} />
                <Route path="*" element={<Navigate to="dashboard" replace />} />
              </Route>
            </Route>

            {/* Catch-all */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </AuthProvider>
  );
}

export default App;
