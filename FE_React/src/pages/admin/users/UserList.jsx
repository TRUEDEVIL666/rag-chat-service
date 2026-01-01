import React, { useState, useEffect } from 'react';

import { useNavigate } from 'react-router-dom';
import {
  UserPlusIcon,
  TrashIcon,
  SpinnerIcon,
} from '@phosphor-icons/react';
import { clsx } from 'clsx';
import { useTranslation } from 'react-i18next';
import { useUsers } from '../../../hooks/useUsers';
import { usePageTour } from '../../../hooks/usePageTour';
import TourButton from '../../../components/common/TourButton';

const UserList = () => {
  const { t } = useTranslation(['users', 'translation']);
  const navigate = useNavigate();
  const { users, loading, error, fetchUsers, deleteUser } = useUsers();

  const tourSteps = [
    { element: '#user-header', popover: { title: t('tour.users.title', 'Users'), description: t('tour.users.desc', 'Manage system users and admins.') } },
    { element: '#create-user-btn', popover: { title: t('tour.users.create', 'Create User'), description: t('tour.users.createDesc', 'Add a new user to the system.') } },
    { element: '#user-list-content', popover: { title: t('tour.users.list', 'User List'), description: t('tour.users.listDesc', 'View and manage existing users.') } }
  ];

  const { startTour } = usePageTour('user-list', tourSteps);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleDeleteUser = async (id) => {
    if (!window.confirm(t('deleteConfirm'))) return;

    try {
      await deleteUser(id);
    } catch (err) {
      alert(t('common.deleteError') + ': ' + (err.response?.data?.detail || t('common.actionFailed')));
    }
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden relative bg-white dark:bg-gray-900 transition-colors">
      {/* Header */}
      <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-8">
        <div className="flex items-center gap-3">
          <h1 id="user-header" className="text-xl font-semibold text-gray-800 dark:text-white">{t('title')}</h1>
          <TourButton startTour={startTour} />
        </div>
        <button id="create-user-btn"
          onClick={() => navigate('/admin/users/create')}
          className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 flex items-center gap-2 shadow-sm transition"
        >
          <UserPlusIcon size={20} /> {t('createNew')}
        </button>
      </header>

      {/* Table Content */}
      <div id="user-list-content" className="flex-1 overflow-auto p-8">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead className="bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-700 text-xs uppercase text-gray-500 dark:text-gray-400 font-semibold">
              <tr>
                <th className="px-6 py-4">{t('table.id')}</th>
                <th className="px-6 py-4">{t('table.tenant')}</th>
                <th className="px-6 py-4">{t('table.email')}</th>
                <th className="px-6 py-4">{t('table.role')}</th>
                <th className="px-6 py-4">{t('table.createdAt')}</th>
                <th className="px-6 py-4 text-right">{t('table.actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700 text-sm">
              {loading ? (
                <tr>
                  <td colSpan="6" className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                    <div className="flex flex-col items-center justify-center">
                      <SpinnerIcon size={24} className="animate-spin mb-2" />
                      <span>{t('common.processing')}</span>
                    </div>
                  </td>
                </tr>
              ) : error ? (
                <tr><td colSpan="6" className="px-6 py-8 text-center text-red-500">{t('common.errorOccurred')}: {error?.message || String(error)}</td></tr>
              ) : users.length === 0 ? (
                <tr><td colSpan="6" className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">{t('empty')}</td></tr>
              ) : (
                users.map(user => (
                  <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition">
                    <td className="px-6 py-4 font-mono text-xs text-gray-500 dark:text-gray-400 truncate max-w-[100px]" title={user.id}>
                      {user.id}
                    </td>
                    <td className="px-6 py-4 font-mono text-xs text-gray-500 dark:text-gray-400 truncate max-w-[100px]" title={user.tenant_id || ''}>
                      {user.tenant_id || '-'}
                    </td>
                    <td className="px-6 py-4 font-medium text-gray-900 dark:text-gray-200">
                      {user.email}
                    </td>
                    <td className="px-6 py-4">
                      <span className={clsx(
                        "px-2 py-1 rounded text-xs font-bold border",
                        user.role === 'admin'
                          ? "bg-purple-100 text-purple-700 border-purple-200 dark:bg-purple-900/30 dark:text-purple-300 dark:border-purple-800"
                          : "bg-primary-100 text-primary-700 border-primary-200 dark:bg-primary-900/30 dark:text-primary-300 dark:border-primary-800"
                      )}>
                        {user.role === 'admin' ? t('role.admin') : t('role.user')}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-500 dark:text-gray-400 text-xs">
                      {new Date(user.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => handleDeleteUser(user.id)}
                        className="text-gray-400 dark:text-gray-500 hover:text-red-600 dark:hover:text-red-400 transition"
                        title={t('tooltip.delete')}
                      >
                        <TrashIcon size={18} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default UserList;
