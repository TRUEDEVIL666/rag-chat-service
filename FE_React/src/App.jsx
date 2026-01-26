import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { ChatProvider } from './context/ChatContext';
import AuthLayout from './components/layout/AuthLayout';
import AdminLayout from './components/layout/AdminLayout';
import UserLayout from './components/layout/UserLayout';
import ProtectedRoute from './components/routing/ProtectedRoute';

import Login from './pages/auth/Login';
import Register from './pages/auth/Register';

// Admin Pages
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
import ChatHistory from './pages/admin/ChatHistory';
import AiProviderModelPage from './pages/admin/ai-models/AiProviderModelPage';
import CourseManagement from './pages/admin/courses/CourseManagement';
import CourseDetail from './pages/admin/courses/CourseDetail';
import InstructorClasses from './pages/admin/classes/InstructorClasses';
import ClassDetail from './pages/admin/courses/ClassDetail';

// User Pages
import Home from './pages/user/Home';
import UserSettings from './pages/user/Settings';
import UserChat from './pages/user/Chat';
import UserClasses from './pages/user/Classes';
import UserClassDetail from './pages/user/ClassDetail';
import History from './pages/user/History';

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <ChatProvider>
            <Toaster position="top-right" />
            <Routes>
              {/* Public Routes */}
              <Route element={<AuthLayout />}>
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
              </Route>

              {/* Admin Routes */}
              <Route path="/admin" element={<ProtectedRoute allowedRoles={['admin']} />}>
                <Route element={<AdminLayout />}>
                  <Route index element={<Navigate to="dashboard" replace />} />
                  <Route path="dashboard" element={<Dashboard />} />
                  <Route path="settings" element={<Settings />} />

                  {/* AI Models */}
                  <Route path="ai-models" element={<AiProviderModelPage />} />

                  {/* Bots */}
                  <Route path="bots" element={<BotList />} />
                  <Route path="bots/create" element={<CreateBot />} />
                  <Route path="bots/:id" element={<EditBot />} />
                  <Route path="bots/:id/knowledge" element={<BotKBConfigPage />} />

                  {/* Documents */}
                  <Route path="documents" element={<DocumentList />} />
                  <Route path="documents/upload" element={<UploadDocument />} />

                  {/* Users */}
                  <Route path="users" element={<UserList />} />
                  <Route path="users/create" element={<CreateUser />} />

                  {/* Chat */}
                  <Route path="chat/:botId" element={<Chatbot />} />
                  <Route path="history" element={<ChatHistory />} />

                  {/* Course Management */}
                  <Route path="courses" element={<CourseManagement />} />
                  <Route path="courses/:id" element={<CourseDetail />} />
                  <Route path="classes" element={<InstructorClasses />} />
                  <Route path="classes/:id" element={<ClassDetail />} />
                </Route>
              </Route>

              {/* User Routes */}
              <Route path="/user" element={<ProtectedRoute allowedRoles={['user']} />}>
                <Route element={<UserLayout />}>
                  <Route index element={<Navigate to="home" replace />} />
                  <Route path="home" element={<Home />} />
                  <Route path="classes" element={<UserClasses />} />
                  <Route path="classes/:id" element={<UserClassDetail />} />
                  <Route path="settings" element={<UserSettings />} />
                  <Route path="chat/:botId" element={<UserChat />} />
                  <Route path="history" element={<History />} />
                </Route>
              </Route>

              {/* Redirects */}
              <Route path="/" element={<Navigate to="/login" replace />} />
              <Route path="*" element={<Navigate to="/login" replace />} />
            </Routes>
          </ChatProvider>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;
