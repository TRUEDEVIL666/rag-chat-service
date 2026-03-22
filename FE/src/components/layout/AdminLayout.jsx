import { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import { clsx } from 'clsx';

const AdminLayout = () => {
  const location = useLocation();
  const isChat = location.pathname.includes('/admin/chat/');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-gray-900 transition-colors duration-300 overflow-hidden">
      <Sidebar isOpen={isSidebarOpen} toggleSidebar={toggleSidebar} />
      <div className="flex-1 md:ml-64 ml-0 flex flex-col min-h-screen transition-all duration-300 relative z-10">
        <main className={clsx(
          "flex-1 overflow-y-auto px-4 lg:px-8 py-4 lg:py-4",
          isChat && "p-0"
        )}>
          <Outlet context={{ toggleSidebar }} />
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;
