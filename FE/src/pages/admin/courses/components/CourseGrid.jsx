import React from 'react';
import { useTranslation } from 'react-i18next';
import { PlusIcon, TrashIcon, CalendarCheckIcon, GraduationCapIcon } from '@phosphor-icons/react';
import Skeleton from '../../../../components/common/Skeleton';

const CourseGrid = ({
  courses,
  loading,
  selectedSemester,
  onAdd,
  onSelect,
  onDelete
}) => {
  const { t } = useTranslation();

  return (
    <div className="flex-1 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 h-[calc(100vh-8rem)] overflow-y-auto custom-scrollbar">
      {(selectedSemester || loading) ? (
        <>
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-lg font-semibold">
                {selectedSemester ? selectedSemester.name : <Skeleton className="h-6 w-48" />}
              </h2>
              <div className="text-sm text-gray-500">
                {loading ? (
                  <Skeleton className="h-4 w-24 mt-1" />
                ) : (
                  `${courses.length} ${t('courses.count', 'courses')}`
                )}
              </div>
            </div>
            <button
              onClick={onAdd}
              className="btn-primary flex items-center gap-2"
              disabled={!selectedSemester}
            >
              <PlusIcon weight="bold" />
              {t('courses.create', 'New Course')}
            </button>
          </div>

          {/* Courses Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
            {loading ? (
              [...Array(3)].map((_, i) => (
                <div key={i} className="p-4 border rounded-lg bg-gray-50 dark:bg-gray-700/50">
                  <Skeleton className="h-5 w-16 mb-2" />
                  <Skeleton className="h-6 w-3/4 mb-2" />
                  <Skeleton className="h-4 w-1/2" />
                </div>
              ))
            ) : (
              <>
                {courses.length === 0 && (
                  <div className="col-span-full py-10 text-center text-gray-400 flex flex-col items-center gap-2">
                    <GraduationCapIcon size={48} className="opacity-20" />
                    {t('courses.empty', 'No courses yet.')}
                  </div>
                )}
                {courses.map(course => (
                  <div
                    key={course.id}
                    className="group bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600 p-4 hover:shadow-md transition cursor-pointer hover:border-primary-300 dark:hover:border-primary-700 relative"
                    onClick={() => onSelect(course)}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="bg-white dark:bg-gray-600 px-2 py-1 rounded text-xs font-bold text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-500">
                        {course.code}
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDelete && onDelete(course);
                        }}
                        className="p-1.5 -mr-1.5 -mt-1 rounded-full hover:bg-red-50 text-gray-400 hover:text-red-500 transition z-10"
                        title={t('common.delete', 'Delete')}
                      >
                        <TrashIcon weight="bold" size={18} />
                      </button>
                    </div>
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-1 truncate" title={course.name}>
                      {course.name}
                    </h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 min-h-[2.5em]">
                      {course.description || t('courses.manage', 'Manage classes & resources')}
                    </p>
                  </div>
                ))}
              </>
            )}
          </div>
        </>
      ) : (
        <div className="h-full flex flex-col items-center justify-center text-gray-400">
          <CalendarCheckIcon size={64} className="opacity-20 mb-4" />
          <p>{t('courses.select_semester', 'Select a semester to view courses')}</p>
        </div>
      )}
    </div>
  );
};

export default CourseGrid;
