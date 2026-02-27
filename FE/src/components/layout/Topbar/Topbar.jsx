import React from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useTheme } from '../../../context/ThemeContext';
import { MoonIcon, SunIcon, BellIcon, SignOutIcon, ListIcon, RobotIcon, Globe as GlobeIcon } from '@phosphor-icons/react';
import { useNavigate, useLocation, matchPath } from 'react-router-dom';
import { useChat } from '../../../context/ChatContext';
import { useTranslation } from 'react-i18next';
import clsx from 'clsx';

const Topbar = ({ toggleSidebar, title }) => {
  const { theme, toggleTheme } = useTheme();
  const { i18n, t } = useTranslation();
  const { user, logout } = useAuth();
  const { activeSession } = useChat();
  const navigate = useNavigate();
  const location = useLocation();

  const currentLang = i18n.language;

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
  };

  const toggleLanguage = () => {
    changeLanguage(currentLang === 'vi' ? 'en' : 'vi');
  };

  const getPageTitle = () => {
    if (title) return title; // Priority to prop
    if (matchPath('/user/home', location.pathname)) return t('nav.home', 'Dashboard');
    if (matchPath('/user/documents', location.pathname)) return t('nav.documents', 'Documents');
    if (matchPath('/user/history', location.pathname)) return t('nav.history', 'History');
    if (matchPath('/user/settings', location.pathname)) return t('nav.settings', 'Settings');
    if (matchPath('/user/chat/*', location.pathname) || matchPath('/admin/chat/*', location.pathname)) {
      const title = activeSession?.botName || activeSession?.title || t('chatbot.chat_title', 'Chat');
      return (
        <div className="flex items-center gap-2">
          <RobotIcon size={24} className="text-indigo-600 dark:text-indigo-400" />
          <span>{title}</span>
        </div>
      );
    }
    return '';
  };

  const pageTitle = getPageTitle();

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed', error);
    }
  };

  // Get display values
  const displayName = user?.username || user?.email || t('topbar.adminUser', 'Tên người dùng');
  const displayRole = user?.app_metadata?.role || user?.role || t('topbar.superAdmin', 'Vai trò');
  const avatarName = displayName.replace(/ /g, '+');

  return (
    <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-6 sticky top-0 z-40 transition-colors shadow-sm">
      <button onClick={toggleSidebar} className="md:hidden p-2 text-slate-500 hover:bg-white/50 rounded-lg">
        <ListIcon className="text-2xl" />
      </button>

      {/* Page Title (Desktop) */}
      <div className="hidden md:block text-xl font-semibold text-slate-800 dark:text-white ml-4">
        {pageTitle}
      </div>

      <div className="flex-1 md:hidden"></div>

      {/* Right Actions */}
      <div className="flex items-center gap-4 ml-auto">
        {/* Language Switch */}
        {/* Language Switch - Flip Switch Style */}
        <button
          onClick={toggleLanguage}
          className="relative inline-flex h-8 w-16 items-center rounded-full bg-[#1e2230] transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 border border-slate-700 p-1"
          title={t('topbar.switchLanguage')}
        >
          <span className="sr-only">{t('topbar.switchLanguage')}</span>

          {/* The Sliding Knob with the Flag inside */}
          <span
            className={`${currentLang === 'en' ? 'translate-x-8' : 'translate-x-0'
              } flex h-6 w-6 transform items-center justify-center rounded-full bg-white transition-transform duration-200 ease-in-out overflow-hidden shadow-sm`}
          >
            <img
              src={currentLang === 'en' ? "https://flagcdn.com/w80/us.png" : "https://flagcdn.com/w80/vn.png"}
              alt={currentLang === 'en' ? "English" : "Vietnamese"}
              className="h-full w-full object-cover scale-125" // Scale-125 helps hide flag edges for a cleaner look
            />
          </span>
        </button>

        {/* Theme Switcher */}
        <button
          onClick={toggleTheme}
          className="p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
          title={t('toggleTheme', 'Toggle Theme')}
        >
          {theme === 'dark' ? (
            <SunIcon size={24} className="text-gray-300" />
          ) : (
            <MoonIcon size={24} />
          )}
        </button>

        <div className="h-6 w-px bg-gray-200 dark:bg-gray-700 mx-2"></div>

        {/* Notification */}
        <button className="relative text-gray-500 hover:text-primary-600 dark:text-gray-400 dark:hover:text-primary-400 transition">
          <BellIcon size={24} weight="fill" />
          <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full border border-white dark:border-gray-800"></span>
        </button>

        {/* User Profile */}
        <div className="relative group z-50">
          <div className="flex items-center gap-3 pl-2 cursor-pointer">
            <div className="text-right hidden sm:block w-32">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-200 truncate" title={displayName}>{displayName}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 truncate capitalize" title={displayRole}>{displayRole}</p>
            </div>
            <img src={`https://ui-avatars.com/api/?name=${avatarName}&background=2563eb&color=fff`} alt="User"
              className="w-9 h-9 rounded-full hover:ring-2 hover:ring-primary-100 transition" />
          </div>
        </div>
      </div>
    </header>
  );
};

export default Topbar;
