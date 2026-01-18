import React, { useState, useEffect } from 'react';

import { useNavigate } from 'react-router-dom';
import {
  UserPlusIcon,
  TrashIcon,
  SpinnerIcon,
  MagnifyingGlassIcon,
  UploadSimpleIcon,
} from '@phosphor-icons/react';
import { clsx } from 'clsx';
import { useTranslation } from 'react-i18next';
import { useUsers } from '../../../hooks/useUsers';
import { usePageTour } from '../../../hooks/usePageTour';
import TourButton from '../../../components/common/TourButton';
import BatchCreateUserDialog from './BatchCreateUserDialog';

const UserList = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { users, loading, error, hasMore, fetchUsers, deleteUser, deleteUsersBatch } = useUsers();

  const tourSteps = [
    { element: '#user-header', popover: { title: t('tour.users.title'), description: t('tour.users.desc') } },
    { element: '#create-user-btn', popover: { title: t('tour.users.create'), description: t('tour.users.createDesc') } },
    { element: '#user-list-content', popover: { title: t('tour.users.list'), description: t('tour.users.listDesc') } }
  ];

  const { startTour } = usePageTour('user-list', tourSteps);

  useEffect(() => {
    fetchUsers();
  }, []); // Initial load only

  // Local state for debouncing
  const [filterValues, setFilterValues] = useState({});
  const [isBatchDialogOpen, setIsBatchDialogOpen] = useState(false);
  const [selectedUserIds, setSelectedUserIds] = useState(new Set());

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedUserIds(new Set(users.map(u => u.id)));
    } else {
      setSelectedUserIds(new Set());
    }
  };

  const handleSelectUser = (id) => {
    const newSet = new Set(selectedUserIds);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
    setSelectedUserIds(newSet);
  };

  const handleBatchDelete = async () => {
    if (selectedUserIds.size === 0) return;
    if (!window.confirm(t('admin.users.batchDeleteConfirm', `Are you sure you want to delete ${selectedUserIds.size} users?`))) return;

    try {
      await deleteUsersBatch(Array.from(selectedUserIds));
      setSelectedUserIds(new Set());
    } catch (err) {
      alert(t('common.deleteError') + ': ' + (err.response?.data?.detail || t('common.actionFailed')));
    }
  };

  const allSelected = users.length > 0 && selectedUserIds.size === users.length;
  const isIndeterminate = selectedUserIds.size > 0 && selectedUserIds.size < users.length;

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      // Only fetch if filters actually changed (handled by hook usually, but good to be explicit or just call it)
      // We pass 'filterValues' to fetchUsers, which treats it as 'newFilters'
      // But we need to avoid the initial double-fetch if possible.
      // Actually, initial load is empty filters.
      if (Object.keys(filterValues).length > 0 || filterValues.query === '') {
        fetchUsers(false, filterValues);
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [filterValues, fetchUsers]);

  const handleFilterChange = (key, value) => {
    setFilterValues(prev => ({ ...prev, [key]: value || undefined }));
  };

  const handleDeleteUser = async (id) => {
    if (!window.confirm(t('admin.users.deleteConfirm'))) return;

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
          <h1 id="user-header" className="text-xl font-semibold text-gray-800 dark:text-white">{t('admin.users.title')}</h1>
          <TourButton startTour={startTour} />
        </div>
        <div className="flex items-center gap-3">
          {selectedUserIds.size > 0 && (
            <button
              onClick={handleBatchDelete}
              className="bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded-lg hover:bg-red-100 flex items-center gap-2 shadow-sm transition animate-fadeIn"
            >
              <TrashIcon size={20} />
              <span>{t('admin.users.deleteSelected')} ({selectedUserIds.size})</span>
            </button>
          )}
          <button
            onClick={() => setIsBatchDialogOpen(true)}
            className="bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 border border-gray-300 dark:border-gray-600 px-4 py-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 flex items-center gap-2 shadow-sm transition"
          >
            <UploadSimpleIcon size={20} /> {t('admin.users.import', 'Import')}
          </button>
          <button id="create-user-btn"
            onClick={() => navigate('/admin/users/create')}
            className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 flex items-center gap-2 shadow-sm transition"
          >
            <UserPlusIcon size={20} /> {t('admin.users.createNew')}
          </button>
        </div>
      </header>

      {/* Filters */}
      <div className="px-8 py-4 grid grid-cols-1 md:grid-cols-4 gap-4 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
        {/* Search */}
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="text"
            placeholder={t('admin.users.searchPlaceholder', 'Search by name or email...')}
            className="w-full pl-10 pr-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors"
            onChange={(e) => handleFilterChange('query', e.target.value)}
          />
        </div>

        {/* Role Filter */}
        <div>
          <select
            className="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors appearance-none"
            onChange={(e) => handleFilterChange('role', e.target.value)}
          >
            <option value="">{t('admin.users.filter.allRoles', 'All Roles')}</option>
            <option value="user">{t('admin.users.role.user')}</option>
            <option value="admin">{t('admin.users.role.admin')}</option>
          </select>
        </div>

        {/* Date From */}
        <div>
          <input
            type="date"
            className="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors"
            onChange={(e) => handleFilterChange('date_from', e.target.value)}
            placeholder="From Date"
          />
        </div>

        {/* Date To */}
        <div>
          <input
            type="date"
            className="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors"
            onChange={(e) => handleFilterChange('date_to', e.target.value)}
            placeholder="To Date"
          />
        </div>
      </div>

      {/* Table Content */}
      <div id="user-list-content" className="flex-1 overflow-auto p-8">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead className="bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-700 text-xs uppercase text-gray-500 dark:text-gray-400 font-semibold">
              <tr>
                <th className="px-6 py-3 text-left">
                  <input
                    type="checkbox"
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 w-4 h-4 cursor-pointer"
                    checked={allSelected}
                    ref={input => { if (input) input.indeterminate = isIndeterminate; }}
                    onChange={handleSelectAll}
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 hover:text-gray-700 dark:text-gray-400 uppercase tracking-wider">
                  {t('users.list.tenant', 'Tenant')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 hover:text-gray-700 dark:text-gray-400 uppercase tracking-wider">
                  {t('users.list.email', 'Email')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 hover:text-gray-700 dark:text-gray-400 uppercase tracking-wider">
                  {t('users.list.role', 'Role')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 hover:text-gray-700 dark:text-gray-400 uppercase tracking-wider">
                  {t('users.list.created_at', 'Created At')}
                </th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 hover:text-gray-700 dark:text-gray-400 uppercase tracking-wider">
                  {t('users.list.action', 'Action')}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700 text-sm">
              {loading && users.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                    <div className="flex flex-col items-center justify-center">
                      <SpinnerIcon size={24} className="animate-spin mb-2" />
                      <span>{t('common.processing')}</span>
                    </div>
                  </td>
                </tr>
              ) : error ? (
                <tr><td colSpan="6" className="px-6 py-8 text-center text-red-500">{t('common.errorOccurred')}: {error?.message || String(error)}</td></tr>
              ) : users.length === 0 ? (
                <tr><td colSpan="6" className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">{t('admin.users.empty')}</td></tr>
              ) : (
                users.map(user => (
                  <tr key={user.id} className={clsx("hover:bg-gray-50 dark:hover:bg-gray-700 transition", selectedUserIds.has(user.id) && "bg-blue-50 dark:bg-blue-900/20")}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="checkbox"
                        className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 w-4 h-4 cursor-pointer"
                        checked={selectedUserIds.has(user.id)}
                        onChange={() => handleSelectUser(user.id)}
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      <span className="flex items-center gap-2">
                        {/* Using Building Icon if imported, else just text */}
                        {user.tenants?.name || 'N/A'}
                      </span>
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
                        {user.role === 'admin' ? t('admin.users.role.admin') : t('admin.users.role.user')}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-500 dark:text-gray-400 text-xs">
                      {new Date(user.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => handleDeleteUser(user.id)}
                        className="text-gray-400 dark:text-gray-500 hover:text-red-600 dark:hover:text-red-400 transition"
                        title={t('admin.users.tooltip.delete')}
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
      {/* Load More Button */}
      {hasMore && (
        <div className="mt-4 flex justify-center">
          <button
            onClick={() => fetchUsers(true)}
            disabled={loading}
            className="px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            {loading ? "Loading..." : "Load More"}
          </button>
        </div>
      )}

      <BatchCreateUserDialog
        isOpen={isBatchDialogOpen}
        onClose={() => setIsBatchDialogOpen(false)}
        onSuccess={(refresh) => {
          if (refresh) fetchUsers();
        }}
      />
    </div>
  );
};

export default UserList;
