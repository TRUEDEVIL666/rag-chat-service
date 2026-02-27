import React, { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  ChalkboardTeacherIcon,
  BooksIcon,
  CalendarBlankIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  CaretDownIcon
} from '@phosphor-icons/react';
import { useNavigate } from 'react-router-dom';
import courseService from '../../services/courseService';
import Skeleton from '../../components/common/Skeleton';
import { ROUTES } from '../../routes';

const UserClasses = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSemester, setSelectedSemester] = useState('All');
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    fetchClasses(controller.signal);
    return () => controller.abort();
  }, []);

  const fetchClasses = async (signal) => {
    try {
      setLoading(true);
      const data = await courseService.getMyClasses({ signal });
      setClasses(data);
    } catch (error) {
      if (error.code === 'ERR_CANCELED' || error.name === 'AbortError') {
        console.log('Fetch classes aborted');
        return;
      }
      console.error('Failed to fetch classes:', error);
    } finally {
      // Only modify state if not aborted (though unmount cleanup handles logic, a flag is safer)
      if (!signal?.aborted) {
        setLoading(false);
      }
    }
  };

  const uniqueSemesters = useMemo(() => {
    const sems = classes.map(c => c.semester_name).filter(Boolean);
    return ['All', ...new Set(sems)];
  }, [classes]);

  const filteredClasses = classes.filter(cls => {
    const matchesSearch = cls.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (cls.course_name && cls.course_name.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesSemester = selectedSemester === 'All' || cls.semester_name === selectedSemester;

    return matchesSearch && matchesSemester;
  });

  const toggleFilter = () => setIsFilterOpen(!isFilterOpen);
  const selectSemester = (sem) => {
    setSelectedSemester(sem);
    setIsFilterOpen(false);
  };

  return (
    <div className="flex-1 overflow-y-auto bg-slate-50 dark:bg-black/20">
      <div className="max-w-6xl mx-auto px-6 py-10 space-y-8">

        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-extrabold text-slate-800 dark:text-white tracking-tight">
              {t('classes.title', 'My Classes')}
            </h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">
              {t('classes.subtitle', 'Access your course materials and AI assistants')}
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Filter Dropdown */}
            <div className="relative">
              <button
                onClick={toggleFilter}
                className="flex items-center gap-2 px-4 py-2.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
              >
                <FunnelIcon />
                <span className="text-sm font-medium">
                  {selectedSemester === 'All' ? t('classes.all_semesters', 'All Semesters') : selectedSemester}
                </span>
                <CaretDownIcon className={`transition-transform duration-200 ${isFilterOpen ? 'rotate-180' : ''}`} />
              </button>

              {isFilterOpen && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setIsFilterOpen(false)} />
                  <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xl z-20 py-1 max-h-60 overflow-y-auto">
                    {uniqueSemesters.map(sem => (
                      <button
                        key={sem}
                        onClick={() => selectSemester(sem)}
                        className={`w-full text-left px-4 py-2 text-sm transition-colors ${selectedSemester === sem
                          ? 'bg-indigo-50 text-indigo-600 dark:bg-indigo-500/10 dark:text-indigo-400 font-medium'
                          : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800'
                          }`}
                      >
                        {sem === 'All' ? t('classes.all_semesters', 'All Semesters') : sem}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>

            {/* Search */}
            <div className="relative group hidden md:block">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-xl blur opacity-20 group-hover:opacity-40 transition duration-500"></div>
              <div className="relative flex items-center bg-white dark:bg-slate-900 rounded-xl px-4 py-2.5 shadow-sm border border-slate-200 dark:border-slate-800">
                <MagnifyingGlassIcon className="text-slate-400 text-lg mr-3" />
                <input
                  type="text"
                  placeholder={t('classes.search_placeholder', 'Search classes...')}
                  className="bg-transparent border-none outline-none text-sm w-48 text-slate-700 dark:text-slate-200 placeholder:text-slate-400"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 h-48 space-y-4">
                <div className="flex justify-between items-start">
                  <Skeleton className="w-12 h-12 rounded-xl" />
                  <Skeleton className="w-20 h-6 rounded-full" />
                </div>
                <div className="space-y-2 mt-4">
                  <Skeleton className="h-6 w-3/4" />
                  <Skeleton className="h-4 w-1/2" />
                </div>
              </div>
            ))}
          </div>
        ) : filteredClasses.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-fade-in-up">
            {filteredClasses.map((cls) => (
              <div
                key={cls.id}
                onClick={() => navigate(ROUTES.USER.CLASS_DETAIL(cls.id))}
                className="group bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 hover:shadow-xl hover:shadow-indigo-500/10 hover:border-indigo-500/30 dark:hover:border-indigo-500/30 transition-all duration-300 cursor-pointer relative overflow-hidden"
              >
                <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity transform group-hover:scale-110 duration-500">
                  <ChalkboardTeacherIcon size={120} weight="fill" />
                </div>

                <div className="flex justify-between items-start mb-4 relative z-10">
                  <div className="w-12 h-12 rounded-xl bg-indigo-50 dark:bg-indigo-500/10 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
                    <BooksIcon size={24} weight="duotone" />
                  </div>
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-green-50 text-green-600 dark:bg-green-500/10 dark:text-green-400 border border-green-100 dark:border-green-500/20">
                    Active
                  </span>
                </div>

                <div className="relative z-10">
                  <h3 className="text-lg font-bold text-slate-800 dark:text-white line-clamp-1 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                    {cls.name}
                  </h3>
                  <div className="flex items-center gap-2 mt-1 text-sm text-slate-500 dark:text-slate-400">
                    <span className="font-medium">{cls.course_code || 'CS-101'}</span>
                    <span>•</span>
                    <span>{cls.semester_name || 'Current Term'}</span>
                  </div>

                  <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-400 md:opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="flex items-center gap-1.5">
                      <CalendarBlankIcon size={14} />
                      <span>Joined {new Date(cls.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-20 bg-white dark:bg-slate-900/50 rounded-3xl border border-dashed border-slate-300 dark:border-slate-700">
            <div className="text-slate-300 dark:text-slate-600 mb-4 flex justify-center">
              <BooksIcon size={64} weight="thin" />
            </div>
            <h3 className="text-xl font-bold text-slate-700 dark:text-slate-200">No classes found</h3>
            <p className="text-slate-500 dark:text-slate-400 mt-2 max-w-md mx-auto">
              You haven't been enrolled in any classes yet. Please contact your administrator.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserClasses;
