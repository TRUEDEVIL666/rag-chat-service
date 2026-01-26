import { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import { clsx } from 'clsx';

const AdminLayout = () => {
  const location = useLocation();
  const isChat = location.pathname.includes('/admin/chat/');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [title, setTitle] = useState('');

  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-gray-900 transition-colors duration-300 overflow-hidden">
      <Sidebar isOpen={isSidebarOpen} toggleSidebar={toggleSidebar} />
      <div className="flex-1 md:ml-64 ml-0 flex flex-col min-h-screen transition-all duration-300 relative z-10">
        <Topbar toggleSidebar={toggleSidebar} title={title} />
        <main className={clsx(
          "flex-1 overflow-y-auto",
          isChat ? "p-0" : "p-6"
        )}>
          <Outlet context={{ toggleSidebar, setTitle }} />
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;
