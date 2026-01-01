import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import { clsx } from 'clsx';

const AdminLayout = () => {
  const location = useLocation();
  const isChat = location.pathname.includes('/admin/chat/');

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-gray-900 transition-colors duration-300">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col min-h-screen">
        <Topbar />
        <main className={clsx(
          "flex-1 overflow-y-auto",
          isChat ? "p-0" : "p-6"
        )}>
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;
