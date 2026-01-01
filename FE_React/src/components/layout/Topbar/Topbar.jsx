import { useAuth } from '../../../context/AuthContext';
import { useTheme } from '../../../context/ThemeContext';
import { Moon, Sun, Bell } from '@phosphor-icons/react';
import { useTranslation } from 'react-i18next';

const Topbar = () => {
  const { theme, toggleTheme } = useTheme();
  const { i18n, t } = useTranslation();
  const { user } = useAuth();

  const toggleLang = () => {
    const nextLang = i18n.language === 'en' ? 'vi' : 'en';
    i18n.changeLanguage(nextLang);
  };

  const currentLang = i18n.language || 'vi';

  // Get display values
  const displayName = user?.full_name || user?.username || user?.email || t('topbar.adminUser', 'Tên người dùng');
  const displayRole = user?.app_metadata?.role || user?.role || t('topbar.superAdmin', 'Vai trò');
  const avatarName = displayName.replace(/ /g, '+');

  return (
    <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-end px-6 sticky top-0 z-40 transition-colors">
      {/* Right Actions */}
      <div className="flex items-center gap-4">
        {/* Language Switcher */}
        <button
          onClick={toggleLang}
          className="relative w-14 h-8 bg-gray-200 dark:bg-gray-700 rounded-full transition-colors focus:outline-none"
          title={t('topbar.switchLanguage', 'Switch Language')}
        >
          <div className={`absolute top-1 left-1 w-6 h-6 bg-white dark:bg-gray-800 rounded-full shadow-md transform transition-transform duration-300 flex items-center justify-center overflow-hidden ${(currentLang === 'en' || currentLang.startsWith('en')) ? 'translate-x-6' : ''}`}>
            <img
              src={(currentLang === 'en' || currentLang.startsWith('en')) ? 'https://flagcdn.com/w40/us.png' : 'https://flagcdn.com/w40/vn.png'}
              alt={currentLang}
              className="w-full h-full object-cover"
            />
          </div>
        </button>

        {/* Theme Switcher */}
        <button
          onClick={toggleTheme}
          className="p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
          title="Toggle Theme"
        >
          {theme === 'dark' ? (
            <Sun size={24} className="text-gray-300" />
          ) : (
            <Moon size={24} />
          )}
        </button>

        <div className="h-6 w-px bg-gray-200 dark:bg-gray-700 mx-2"></div>

        {/* Notification */}
        <button className="relative text-gray-500 hover:text-primary-600 dark:text-gray-400 dark:hover:text-primary-400 transition">
          <Bell size={24} weight="fill" />
          <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full border border-white dark:border-gray-800"></span>
        </button>

        {/* User Profile */}
        <div className="flex items-center gap-3 pl-2">
          <div className="text-right hidden sm:block w-32">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-200 truncate" title={displayName}>{displayName}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400 truncate capitalize" title={displayRole}>{displayRole}</p>
          </div>
          <img src={`https://ui-avatars.com/api/?name=${avatarName}&background=2563eb&color=fff`} alt="User"
            className="w-9 h-9 rounded-full cursor-pointer hover:ring-2 hover:ring-primary-100 transition" />
        </div>
      </div>
    </header>
  );
};

export default Topbar;
