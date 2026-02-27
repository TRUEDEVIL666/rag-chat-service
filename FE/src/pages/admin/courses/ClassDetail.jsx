import { useState, useEffect } from 'react';
import { useParams, useNavigate, useOutletContext } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeftIcon, RobotIcon, Trash } from '@phosphor-icons/react';
import { toast } from 'react-hot-toast';
import courseService from '../../../services/courseService';
import Skeleton from '../../../components/common/Skeleton';
import AddBotsModal from './components/AddBotsModal';
import AddStudentsModal from './components/AddStudentsModal';

const ClassDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { setTitle } = useOutletContext() || {};

  const [cls, setCls] = useState(null);
  const [students, setStudents] = useState([]);
  const [bots, setBots] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modal states
  const [showBotsModal, setShowBotsModal] = useState(false);
  const [showStudentsModal, setShowStudentsModal] = useState(false);

  useEffect(() => {
    loadClassInfo();
    loadStudents();
    loadBots();
  }, [id]);

  const loadClassInfo = async () => {
    try {
      const data = await courseService.getClass(id);
      setCls(data);
      if (setTitle && data) {
        setTitle(data.name);
      }
    } catch (error) {
      console.error(error);
      toast.error(t('courses.load_error', "Failed to load class data"));
    } finally {
      setLoading(false);
    }
  };

  const loadStudents = async () => {
    try {
      const data = await courseService.getClassStudents(id);
      setStudents(data);
    } catch (error) {
      console.error(error);
    }
  };

  const loadBots = async () => {
    try {
      const data = await courseService.getClassBots(id);
      setBots(data || []);
    } catch (error) {
      console.error(error);
    }
  };

  const handleRemoveBot = async (botId) => {
    if (!window.confirm(t('courses.class.remove_bot_confirm', 'Are you sure you want to remove this bot?'))) return;
    try {
      await courseService.removeBotFromClass(id, botId);
      toast.success(t('courses.class.bot_removed', 'Bot removed successfully'));
      // Optimistic update
      setBots(prev => prev.filter(b => b.id !== botId));
    } catch (error) {
      console.error(error);
      toast.error(t('courses.class.remove_bot_error', 'Failed to remove bot'));
      loadBots(); // Revert on error
    }
  };

  const handleRemoveStudent = async (userId) => {
    if (!window.confirm(t('courses.class.remove_student_confirm', 'Are you sure you want to unenroll this student?'))) return;
    try {
      await courseService.removeStudentFromClass(id, userId);
      toast.success(t('courses.class.student_removed', 'Student unenrolled successfully'));
      // Optimistic update
      setStudents(prev => prev.filter(s => s.user_id !== userId));
    } catch (error) {
      console.error(error);
      toast.error(t('courses.class.remove_student_error', 'Failed to unenroll student'));
      loadStudents(); // Revert on error
    }
  };

  if (loading && !cls) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-6 w-24" />
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-100 dark:border-gray-700 shadow-sm">
          <div className="border-l-4 border-primary-500 pl-4 space-y-2">
            <Skeleton className="h-8 w-1/3" />
            <Skeleton className="h-4 w-1/4" />
          </div>
        </div>
      </div>
    );
  }

  if (!cls) return <div className="p-10">{t('courses.class.notFound', "Class not found")}</div>;

  return (
    <div className="p-6 space-y-6">
      <button onClick={() => navigate(-1)} className="flex items-center text-gray-500 hover:text-primary-600 transition">
        <ArrowLeftIcon className="mr-2" /> {t('common.back', "Back")}
      </button>

      {/* Two Tables Side by Side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-4">
        {/* Bots Table */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-100 dark:border-gray-700 shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 flex items-center gap-2">
              <RobotIcon className="text-primary-500" size={20} />
              {t('courses.class.assigned_bots', 'Assigned Bots')} ({bots.length})
            </h2>
            <button
              onClick={() => setShowBotsModal(true)}
              className="px-3 py-1.5 bg-primary-600 hover:bg-primary-700 text-white rounded-lg text-sm font-medium transition flex items-center gap-1"
            >
              + {t('common.add', 'Add')}
            </button>
          </div>

          <div className="overflow-x-auto max-h-[400px] custom-scrollbar">
            <table className="w-full text-left border-collapse relative">
              <thead className="sticky top-0 bg-gray-50 dark:bg-gray-700/50 text-xs uppercase text-gray-500 dark:text-gray-400 font-semibold z-10 backdrop-blur-sm">
                <tr>
                  <th className="px-4 py-3">{t('list.table.name', 'Name')}</th>
                  <th className="px-4 py-3">{t('list.table.description', 'Description')}</th>
                  <th className="px-4 py-3 text-right">{t('common.actions', 'Actions')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700 text-sm">
                {bots.length === 0 ? (
                  <tr>
                    <td colSpan="3" className="px-4 py-8 text-center text-gray-500">
                      {t('courses.class.noBots', 'No bots assigned.')}
                    </td>
                  </tr>
                ) : (
                  bots.map((bot) => (
                    <tr key={bot.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">
                        {bot.name}
                      </td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">
                        {bot.description || t('common.na')}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => handleRemoveBot(bot.id)}
                          className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-all"
                          title={t('common.remove', 'Remove')}
                        >
                          <Trash size={18} />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Students Table */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-100 dark:border-gray-700 shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
              {t('courses.class.students', 'Enrolled Students')} ({students.length})
            </h2>
            <button
              onClick={() => setShowStudentsModal(true)}
              className="px-3 py-1.5 bg-primary-600 hover:bg-primary-700 text-white rounded-lg text-sm font-medium transition flex items-center gap-1"
            >
              + {t('common.add', 'Add')}
            </button>
          </div>

          <div className="overflow-x-auto max-h-[400px] custom-scrollbar">
            {students.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                {t('courses.class.noStudents', 'No students enrolled.')}
              </div>
            ) : (
              <table className="w-full text-left border-collapse relative">
                <thead className="sticky top-0 bg-gray-50 dark:bg-gray-700/50 text-xs uppercase text-gray-500 dark:text-gray-400 font-semibold z-10 backdrop-blur-sm">
                  <tr>
                    <th className="px-4 py-3">{t('list.table.name', 'Name')}</th>
                    <th className="px-4 py-3">{t('list.table.email', 'Email')}</th>
                    <th className="px-4 py-3">{t('list.table.dateAdded', 'Added')}</th>
                    <th className="px-4 py-3 text-right">{t('common.actions', 'Actions')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700 text-sm">
                  {students.map((student) => (
                    <tr key={student.user_id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">
                        {student.name || t('common.na')}
                      </td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">
                        {student.email}
                      </td>
                      <td className="px-4 py-3 text-gray-500 dark:text-gray-400">
                        {new Date(student.enrolled_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => handleRemoveStudent(student.user_id)}
                          className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-all"
                          title={t('common.remove', 'Remove')}
                        >
                          <Trash size={18} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>

      <AddBotsModal
        isOpen={showBotsModal}
        onClose={() => setShowBotsModal(false)}
        onSuccess={loadBots}
        classId={id}
        assignedBots={bots}
      />

      <AddStudentsModal
        isOpen={showStudentsModal}
        onClose={() => setShowStudentsModal(false)}
        onSuccess={loadStudents}
        classId={id}
        enrolledStudents={students}
      />
    </div >
  );
};

export default ClassDetail;
