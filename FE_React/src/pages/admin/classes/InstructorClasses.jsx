import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useOutletContext } from 'react-router-dom';
import { UsersIcon, ChalkboardTeacherIcon, CalendarCheckIcon, MagnifyingGlassIcon } from '@phosphor-icons/react';
import courseService from '../../../services/courseService';
import Skeleton from '../../../components/common/Skeleton';
import { toast } from 'react-hot-toast';

const InstructorClasses = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { setTitle } = useOutletContext();

  const [classes, setClasses] = useState([]);
  const [semesters, setSemesters] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSemesterId, setSelectedSemesterId] = useState('all');

  useEffect(() => {
    setTitle(t('courses.instructor_classes', 'My Classes'));
  }, [t, setTitle]);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const [classesData, semestersData] = await Promise.all([
        courseService.getMyClasses(),
        courseService.listSemesters()
      ]);
      setClasses(classesData || []);
      setSemesters(semestersData || []);
    } catch (error) {
      console.error("Error loading data", error);
      toast.error(t('classes.load_error', 'Failed to load classes'));
    } finally {
      setLoading(false);
    }
  };

  // Filter logic
  const filteredClasses = classes.filter(cls => {
    const matchesSearch =
      cls.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      cls.course_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      cls.course_name?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesSemester = selectedSemesterId === 'all' || cls.semester_id === selectedSemesterId;

    return matchesSearch && matchesSemester;
  });

  return (
    <div className="p-6">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <ChalkboardTeacherIcon size={24} className="text-primary-500" />
            {t('classes.assigned_classes', 'Classes Assigned to Me')}
          </h2>

          <div className="flex flex-col sm:flex-row items-center gap-3">
            {/* Search Bar */}
            <div className="relative w-full sm:w-64">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
              <input
                type="text"
                placeholder={t('classes.search_placeholder', 'Search classes...')}
                className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-200 dark:border-gray-600 dark:bg-gray-700 focus:ring-2 focus:ring-primary-500 transition-all outline-none"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            {/* Semester Filter */}
            <select
              className="w-full sm:w-48 px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600 dark:bg-gray-700 focus:ring-2 focus:ring-primary-500 outline-none"
              value={selectedSemesterId}
              onChange={(e) => setSelectedSemesterId(e.target.value)}
            >
              <option value="all">{t('classes.all_semesters', 'All Semesters')}</option>
              {semesters.map(sem => (
                <option key={sem.id} value={sem.id}>{sem.name}</option>
              ))}
            </select>
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="p-4 border rounded-lg bg-gray-50 dark:bg-gray-700/50">
                <Skeleton className="h-6 w-3/4 mb-2" />
                <Skeleton className="h-4 w-1/2 mb-2" />
                <Skeleton className="h-4 w-1/4" />
              </div>
            ))}
          </div>
        ) : (
          <>
            {filteredClasses.length === 0 ? (
              <div className="text-center py-10 text-gray-500">
                <ChalkboardTeacherIcon size={48} className="mx-auto text-gray-300 mb-2" />
                <p>{searchTerm || selectedSemesterId !== 'all' ? t('classes.no_results', 'No classes match your search.') : t('classes.no_classes', 'You are not assigned to any classes.')}</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredClasses.map(cls => (
                  <div
                    key={cls.id}
                    className="group bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600 p-4 hover:shadow-md transition cursor-pointer hover:border-primary-300 dark:hover:border-primary-700"
                    onClick={() => navigate(`/admin/classes/${cls.id}`)}
                  >
                    <div className="flex justify-between items-start mb-3">
                      {cls.course_code && (
                        <span className="bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 px-2 py-1 rounded text-xs font-bold">
                          {cls.course_code}
                        </span>
                      )}
                      {cls.semester_name && (
                        <span className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-800 px-2 py-1 rounded border border-gray-200 dark:border-gray-600">
                          <CalendarCheckIcon />
                          {cls.semester_name}
                        </span>
                      )}
                    </div>
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-1 text-lg line-clamp-2" title={cls.name}>
                      {cls.name}
                    </h3>
                    {cls.course_name && (
                      <p className="text-sm text-gray-600 dark:text-gray-300 mb-4 truncate" title={cls.course_name}>
                        {cls.course_name}
                      </p>
                    )}

                    <div className="flex items-center text-xs text-gray-500 dark:text-gray-400 border-t border-gray-200 dark:border-gray-600 pt-3 mt-auto">
                      <UsersIcon size={16} className="mr-1.5" />
                      <span>{t('classes.manage_students_bots')}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default InstructorClasses;
