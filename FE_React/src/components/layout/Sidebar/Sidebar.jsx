import { NavLink } from 'react-router-dom';
import {
  MonitorPlayIcon,
  SquaresFourIcon,
  RobotIcon,
  FilesIcon,
  UsersIcon,
  GearIcon,
  SignOutIcon,
  BrainIcon
} from '@phosphor-icons/react';

import { useAuth } from '../../../context/AuthContext';
import { useTranslation } from 'react-i18next';
import clsx from 'clsx';

const Sidebar = () => {
  const { logout } = useAuth();
  const { t } = useTranslation();

  const handleLogout = (e) => {
    e.preventDefault();
    if (confirm(t('common.logoutConfirm', 'Are you sure you want to log out?'))) {
      logout();
    }
  };

  const NavItem = ({ to, icon: Icon, label }) => (
    <NavLink end
      to={to}
      className={({ isActive }) => clsx(
        "flex items-center gap-3 px-4 py-3 rounded-lg transition font-medium text-sm group",
        isActive
          ? "bg-blue-50 text-blue-600 dark:bg-primary-900/10 dark:text-primary-400"
          : "text-gray-500 dark:text-gray-400 hover:bg-primary-50 dark:hover:bg-primary-900/10 hover:text-primary-600 dark:hover:text-primary-400"
      )}
    >
      {({ isActive }) => (
        <>
          <Icon size={24} weight={isActive ? "fill" : "regular"} className={clsx(isActive ? "" : "group-hover:text-primary-600 dark:group-hover:text-primary-400")} />
          <span>{label}</span>
        </>
      )}
    </NavLink>
  );

  return (
    <aside className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col flex-shrink-0 h-full fixed left-0 top-0 z-50 transition-colors duration-300">
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-gray-100 dark:border-gray-700">
        <div className="flex items-center gap-2 text-primary-600 font-bold text-xl uppercase tracking-wider">
          <MonitorPlayIcon size={24} weight="fill" />
          <span>{t('common.adminPortal', 'Admin Portal')}</span>
        </div>
      </div>

      {/* Menu */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        <NavItem to="/admin/dashboard" icon={SquaresFourIcon} label={t('sidebar.dashboard')} />
        <NavItem to="/admin/ai-models" icon={BrainIcon} label={t('sidebar.aiModels', 'AI Models')} />
        <NavItem to="/admin/bots" icon={RobotIcon} label={t('sidebar.chatbots')} />
        <NavItem to="/admin/documents" icon={FilesIcon} label={t('sidebar.documents')} />
        <NavItem to="/admin/users" icon={UsersIcon} label={t('sidebar.users')} />

        <div className="pt-4 mt-4 border-t border-gray-100 dark:border-gray-700">
          <p className="px-4 text-xs font-semibold text-gray-400 uppercase mb-2">{t('sidebar.system', 'System')}</p>
          <NavItem to="/admin/settings" icon={GearIcon} label={t('sidebar.settings')} />
        </div>
      </nav>

      <div className="p-4 border-t border-gray-100 dark:border-gray-700">
        <button onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-3 text-gray-500 dark:text-gray-400 hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600 dark:hover:text-red-400 rounded-lg transition font-medium text-sm cursor-pointer group">
          <SignOutIcon size={24} className="group-hover:text-red-600" />
          <span>{t('topbar.logout', 'Sign Out')}</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
