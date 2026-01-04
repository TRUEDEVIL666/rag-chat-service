import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { ChatProvider } from './context/ChatContext';
import AuthLayout from './components/layout/AuthLayout';
import AdminLayout from './components/layout/AdminLayout';
import UserLayout from './components/layout/UserLayout';

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

// User Portal Pages
import UserHome from './pages/user/Home';
import UserChat from './pages/user/Chat';
import UserDocuments from './pages/user/Documents';
import UserSettings from './pages/user/Settings';
import ChatInterface from './components/chat/ChatInterface';
import ChatHistoryInterface from './components/chat/ChatHistoryInterface';


import PublicRoute from './components/routing/PublicRoute';
import ProtectedRoute from './components/routing/ProtectedRoute';
import { getHomeRoute } from './utils/authUtils';

const RootRedirect = () => {
  const { isAuthenticated, user, loading } = useAuth();

  if (loading) return null;

  if (isAuthenticated) {
    return <Navigate to={getHomeRoute(user)} replace />;
  }

  return <Navigate to="/login" replace />;
};

function App() {
  return (
    <AuthProvider>
      <ChatProvider>
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

              {/* Protected Routes - GENERIC (All authenticated users) */}
              <Route element={<ProtectedRoute />}>

                {/* User Portal */}
                <Route path="/user" element={<UserLayout />}>
                  <Route index element={<Navigate to="home" replace />} />
                  <Route path="home" element={<UserHome />} />
                  <Route path="chat" element={<UserChat />} />
                  <Route path="chat/:sessionId" element={<UserChat />} />
                  <Route path="documents" element={<UserDocuments />} />
                  <Route path="history" element={<ChatHistoryInterface basePath="/user/chat" />} />
                  <Route path="saved" element={<div className="p-10 font-bold text-slate-500">Feature Coming Soon</div>} />
                  <Route path="settings" element={<UserSettings />} />
                </Route>

                {/* Admin Portal - Protected by Role */}
                <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
                  <Route path="/admin" element={<AdminLayout />}>
                    <Route index element={<Navigate to="dashboard" replace />} />
                    <Route path="dashboard" element={<Dashboard />} />
                    <Route path="settings" element={<Settings />} />

                    <Route path="bots" element={<BotList />} />
                    <Route path="bots/create" element={<CreateBot />} />
                    <Route path="bots/edit/:id" element={<EditBot />} />
                    <Route path="bots/:id/kbs" element={<BotKBConfigPage />} />
                    <Route path="chat/:id" element={<Chatbot />} />
                    <Route path="history" element={<ChatHistoryInterface basePath="/admin/chat" />} />
                    <Route path="documents" element={<DocumentList />} />
                    <Route path="documents/upload" element={<UploadDocument />} />
                    <Route path="users" element={<UserList />} />
                    <Route path="users/create" element={<CreateUser />} />
                    <Route path="ai-models" element={<AiProviderModelPage />} />
                    <Route path="*" element={<Navigate to="dashboard" replace />} />
                  </Route>
                </Route>

              </Route>

              {/* Catch-all */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </ThemeProvider>
      </ChatProvider>
    </AuthProvider>
  );
}

export default App;
