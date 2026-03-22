import { useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import Skeleton from '../../common/Skeleton';
import {
  MonitorPlayIcon,
  SquaresFourIcon,
  RobotIcon,
  FilesIcon,
  UsersIcon,
  GearIcon,
  SignOutIcon,
  BrainIcon,
  ClockCounterClockwiseIcon,
  XIcon,
  CaretDownIcon,
  TrashIcon,
  GraduationCapIcon,
  ChatCircleTextIcon as ChatIcon,
  LightningIcon,
  FileTextIcon,
  MoonIcon,
  SunIcon,
  Globe as GlobeIcon
} from '@phosphor-icons/react';

import { useAuth } from '../../../context/AuthContext';
import { useTheme } from '../../../context/ThemeContext';
import { useChat } from '../../../context/ChatContext';
import { useTranslation } from 'react-i18next';
import clsx from 'clsx';

const Sidebar = ({ isOpen, toggleSidebar }) => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { i18n, t } = useTranslation();
  const navigate = useNavigate();
  useChat();

  const currentLang = i18n.language;
  const toggleLanguage = () => {
    i18n.changeLanguage(currentLang === 'vi' ? 'en' : 'vi');
  };

  const handleLogout = (e) => {
    if (e) e.preventDefault();
    if (confirm(t('common.logoutConfirm', 'Are you sure you want to log out?'))) {
      logout();
      navigate('/login');
    }
  };

  // User details
  const displayName = user?.username || user?.email || 'Admin';
  const displayRole = user?.app_metadata?.role || user?.role || t('topbar.superAdmin', 'Vai trò');
  const avatarName = displayName.replace(/ /g, '+');

  const NavItem = ({ to, icon: Icon, label, exact = false }) => (
    <NavLink end={exact}
      to={to}
      onClick={() => {
        if (window.innerWidth < 768 && toggleSidebar) {
          toggleSidebar();
        }
      }}
      className={({ isActive }) => clsx(
        "flex items-center gap-3 px-4 py-2.5 transition rounded-xl font-semibold text-[13px] group mb-1",
        isActive
          ? "bg-blue-50 text-blue-600 dark:bg-primary-900/10 dark:text-primary-400"
          : "text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800/50 hover:text-gray-900 dark:hover:text-gray-100"
      )}
    >
      {({ isActive }) => (
        <>
          <Icon size={20} weight={isActive ? "fill" : "regular"} className={clsx(isActive ? "text-blue-600" : "text-gray-400 group-hover:text-gray-600")} />
          <span>{label}</span>
        </>
      )}
    </NavLink>
  );

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-gray-900/50 z-40 md:hidden backdrop-blur-sm transition-opacity"
          onClick={toggleSidebar}
        />
      )}

      <aside className={clsx(
        "w-64 bg-white dark:bg-gray-800 border-r border-gray-100 dark:border-gray-700 flex flex-col flex-shrink-0 h-full fixed left-0 top-0 z-50 transition-transform duration-300 md:translate-x-0",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        {/* Logo Section - Lincoln High Theme */}
        <div className="px-6 pt-4 pb-6 flex items-center gap-3">
          <div className="w-11 h-11 bg-blue-700 rounded-xl flex items-center justify-center shadow-lg shadow-blue-200 dark:shadow-none">
            <GraduationCapIcon size={26} weight="fill" className="text-white" />
          </div>
          <div>
            <h1 className="text-[15px] font-bold text-gray-900 dark:text-white leading-tight">Lincoln High</h1>
            <p className="text-[11px] font-medium text-gray-400 dark:text-gray-500 tracking-wide capitalize">{displayRole}</p>
          </div>
        </div>

        {/* Menu Sections */}
        <nav className="flex-1 px-4 py-2 space-y-6 overflow-y-auto custom-scrollbar">
          {/* MENU Section */}
          <div>
            <p className="px-4 text-[11px] font-bold text-slate-400 dark:text-slate-500 mb-3 tracking-widest uppercase">Menu</p>
            <NavItem to="/admin/dashboard" icon={SquaresFourIcon} label={t('sidebar.dashboard', 'Overview')} exact />
            <NavItem to="/admin/history" icon={ChatIcon} label={t('sidebar.history', 'Conversations')} />
            <NavItem to="/admin/knowledge-bases" icon={FilesIcon} label={t('sidebar.documents', 'Knowledge Base')} />
          </div>

          {/* ADMINISTRATION Section */}
          <div>
            <p className="px-4 text-[11px] font-bold text-slate-400 dark:text-slate-500 mb-3 tracking-widest uppercase">Administration</p>
            <NavItem to="/admin/bots" icon={RobotIcon} label={t('sidebar.chatbots', 'Chatbots')} />
            <NavItem to="/admin/users" icon={UsersIcon} label={t('sidebar.users', 'Students')} />
            <NavItem to="/admin/courses" icon={MonitorPlayIcon} label={t('sidebar.courses', 'Courses')} />
            <NavItem to="/admin/classes" icon={UsersIcon} label={t('sidebar.classes', 'Classes')} />
            <NavItem to="/admin/ai-models" icon={BrainIcon} label={t('sidebar.aiModels', 'AI Models')} />
            <NavItem to="/admin/settings" icon={GearIcon} label={t('sidebar.settings', 'Settings')} />
          </div>
        </nav>

        {/* System Controls & Profile Section */}
        <div className="mt-auto p-4 border-t border-gray-100 dark:border-gray-700 bg-slate-50/30 dark:bg-gray-800/30">
          <div className="flex items-center justify-between px-2 mb-4">
            <button
              onClick={toggleTheme}
              className="p-2 text-gray-500 hover:bg-white dark:hover:bg-gray-700 rounded-xl transition shadow-sm border border-transparent hover:border-gray-200 dark:hover:border-gray-600"
              title={t('common.toggle_theme', 'Toggle Theme')}
            >
              {theme === 'dark' ? <SunIcon size={20} /> : <MoonIcon size={20} />}
            </button>
            <button
              onClick={toggleLanguage}
              className="flex items-center gap-2 px-3 py-1.5 text-[10px] font-bold text-gray-600 dark:text-gray-300 hover:bg-white dark:hover:bg-gray-700 rounded-xl transition shadow-sm border border-transparent hover:border-gray-200 dark:hover:border-gray-600 uppercase tracking-tighter"
            >
              <GlobeIcon size={16} />
              {currentLang === 'vi' ? 'VN' : 'EN'}
            </button>
          </div>

          <div className="flex items-center gap-3 p-2 rounded-2xl bg-white dark:bg-gray-800 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className="w-10 h-10 rounded-full bg-slate-200 dark:bg-gray-700 flex items-center justify-center overflow-hidden border-2 border-white dark:border-gray-600 shadow-sm">
              <img
                src={`https://ui-avatars.com/api/?name=${avatarName}&background=2563eb&color=fff`}
                alt="Avatar"
                className="w-full h-full object-cover"
              />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-bold text-gray-900 dark:text-white truncate" title={displayName}>{displayName}</p>
              <button
                onClick={handleLogout}
                className="text-[10px] font-bold text-red-500 hover:text-red-600 transition uppercase tracking-wider text-left"
              >
                Log Out
              </button>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
