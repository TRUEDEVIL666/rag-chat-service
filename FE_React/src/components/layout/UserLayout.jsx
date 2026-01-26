import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { UserSidebar } from './Sidebar';
import Topbar from './Topbar/Topbar';
import '../../styles/user-custom.css';

const UserLayout = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);

  return (
    <div className="user-portal-root text-slate-700 h-screen flex overflow-hidden bg-[url('https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=2564&auto=format&fit=crop')] bg-cover bg-center dark:text-gray-100 transition-colors duration-500">
      {/* Privacy Layer overlay */}
      <div className="absolute inset-0 bg-white/40 dark:bg-slate-950/90 z-0 transition-colors duration-500"></div>

      {/* SIDEBAR */}
      <aside
        className={`w-64 bg-white/70 backdrop-blur-md border-r border-slate-200 dark:bg-slate-900 dark:border-slate-800 h-full relative z-20 transition-all duration-300 ${isSidebarOpen ? 'fixed inset-0 z-50 flex' : 'hidden md:flex'}`}
        id="sidebar"
      >
        <UserSidebar isOpen={isSidebarOpen} toggleSidebar={toggleSidebar} />
      </aside>

      {/* MAIN CONTAINER */}
      <div className="flex-1 flex flex-col h-full relative z-10 overflow-hidden">
        <Topbar toggleSidebar={toggleSidebar} />
        {/* Pass toggle function to children via Outlet context if needed, or handle header in pages */}
        <Outlet context={{ toggleSidebar }} />
      </div>
    </div>
  );
};

export default UserLayout;
