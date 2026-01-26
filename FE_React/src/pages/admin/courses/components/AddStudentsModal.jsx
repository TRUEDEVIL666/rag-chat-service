import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { MagnifyingGlassIcon, X } from '@phosphor-icons/react';
import { toast } from 'react-hot-toast';
import courseService from '../../../../services/courseService';
import { userService } from '../../../../services/userService';
import Skeleton from '../../../../components/common/Skeleton';

const AddStudentsModal = ({ isOpen, onClose, onSuccess, classId, enrolledStudents = [] }) => {
  const { t } = useTranslation();
  const [availableUsers, setAvailableUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedUserIds, setSelectedUserIds] = useState([]);

  useEffect(() => {
    if (isOpen) {
      loadAvailableUsers();
      setSearch('');
      setSelectedUserIds([]);
    }
  }, [isOpen]);

  const loadAvailableUsers = async () => {
    setLoading(true);
    try {
      const response = await userService.getUsers(100);
      const enrolledIds = enrolledStudents.map(s => s.user_id);
      const available = (response.items || []).filter(u => !enrolledIds.includes(u.id));
      setAvailableUsers(available);
    } catch (error) {
      console.error("Error loading users", error);
      toast.error(t('courses.class.load_users_error', 'Failed to load users'));
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    try {
      await courseService.addStudentsToClass(classId, selectedUserIds);
      toast.success(t('courses.class.students_added', 'Students added successfully'));
      onSuccess();
      onClose();
    } catch (error) {
      console.error(error);
      toast.error(t('courses.class.add_students_error', 'Failed to add students'));
    }
  };

  const toggleSelection = (userId) => {
    setSelectedUserIds(prev =>
      prev.includes(userId)
        ? prev.filter(id => id !== userId)
        : [...prev, userId]
    );
  };

  const filteredUsers = availableUsers.filter(user =>
    user.name?.toLowerCase().includes(search.toLowerCase()) ||
    user.email?.toLowerCase().includes(search.toLowerCase())
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4 backdrop-blur-sm md:pl-64">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col">
        {/* Modal Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
            {t('courses.class.add_students', 'Add Students')}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X size={24} />
          </button>
        </div>

        {/* Search Bar */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder={t('courses.class.search_students', 'Search students...')}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 outline-none"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        {/* Students List */}
        <div className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              {t('courses.class.no_users_found', 'No users found')}
            </div>
          ) : (
            <div className="space-y-2">
              {filteredUsers.map((user) => (
                <label
                  key={user.id}
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer border border-gray-200 dark:border-gray-600"
                >
                  <input
                    type="checkbox"
                    checked={selectedUserIds.includes(user.id)}
                    onChange={() => toggleSelection(user.id)}
                    className="w-4 h-4 text-primary-600 rounded focus:ring-2 focus:ring-primary-500"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-gray-900 dark:text-white">{user.name}</div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">{user.email}</div>
                  </div>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex justify-end gap-3 p-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
          >
            {t('common.cancel', 'Cancel')}
          </button>
          <button
            onClick={handleAdd}
            disabled={selectedUserIds.length === 0}
            className="px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg transition"
          >
            {t('common.add', 'Add')} ({selectedUserIds.length})
          </button>
        </div>
      </div>
    </div>
  );
};

export default AddStudentsModal;
