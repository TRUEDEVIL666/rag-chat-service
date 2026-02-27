import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { UserSidebar } from './Sidebar';
import Topbar from './Topbar/Topbar';

const UserLayout = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);

  return (
    <div className="user-portal-root h-screen flex overflow-hidden bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 transition-colors duration-500">


      <aside
        className={`w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 h-full relative z-20 transition-all duration-300 ${isSidebarOpen ? 'fixed inset-0 z-50 flex' : 'hidden md:flex'}`}
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
