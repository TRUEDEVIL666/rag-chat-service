import { UserCircle, LockKey } from '@phosphor-icons/react';
import { useAuth } from '../../context/AuthContext';
import { useTranslation } from 'react-i18next';

const Settings = () => {
  const { t } = useTranslation(['settings', 'translation']);
  const { user } = useAuth();

  return (
    <div className="max-w-3xl space-y-8">
      <header className="mb-6">
        <h1 className="text-xl font-semibold dark:text-white">{t('title')}</h1>
      </header>

      {/* Profile Information */}
      <div className="card">
        <h2 className="text-lg font-bold text-gray-800 dark:text-white mb-6 flex items-center gap-2">
          <UserCircle size={24} className="text-primary-600" weight="fill" />
          {t('account.title')}
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{t('account.email')}</label>
            <input
              type="text"
              disabled
              className="input-field bg-gray-50 dark:bg-gray-800 cursor-not-allowed text-gray-600 dark:text-gray-300"
              value={user?.email || user?.sub || "Unknown"}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{t('account.role')}</label>
            <div className="w-full">
              <span className="bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 px-3 py-2 rounded-lg text-sm font-bold border border-purple-200 dark:border-purple-800 inline-block w-full text-center uppercase tracking-wider">
                {user?.role || user?.app_metadata?.role || "user"}
              </span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{t('account.tenant')}</label>
            <input
              type="text"
              disabled
              className="input-field bg-gray-50 dark:bg-gray-800 cursor-not-allowed text-gray-500 font-mono text-sm"
              value={user?.tenant_id || t('common.na')}
            />
          </div>
        </div>
      </div>

      {/* Change Password */}
      <div className="card relative overflow-hidden">
        <div className="absolute top-0 right-0 p-4">
          <span className="bg-yellow-100 text-yellow-700 px-2 py-1 rounded text-xs font-bold border border-yellow-200">
            {t('password.inDev')}
          </span>
        </div>

        <h2 className="text-lg font-bold text-gray-800 dark:text-white mb-6 flex items-center gap-2">
          <LockKey size={24} className="text-orange-600" weight="fill" />
          {t('password.title')}
        </h2>

        <form onSubmit={(e) => { e.preventDefault(); alert(t('password.notSupported')); }} className="space-y-4 max-w-md">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('password.current')}</label>
            <input type="password" className="input-field" disabled />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('password.new')}</label>
            <input type="password" className="input-field" disabled />
          </div>
          <button type="submit" className="btn-primary opacity-50 cursor-not-allowed" disabled>
            {t('common.saveChanges')}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Settings;
