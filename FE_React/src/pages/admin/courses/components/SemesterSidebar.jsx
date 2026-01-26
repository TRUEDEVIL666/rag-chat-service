import React from 'react';
import { useTranslation } from 'react-i18next';
import { CalendarCheckIcon, PlusIcon } from '@phosphor-icons/react';
import Skeleton from '../../../../components/common/Skeleton';

const SemesterSidebar = ({
  semesters,
  selectedSemester,
  onSelect,
  onAdd,
  loading
}) => {
  const { t } = useTranslation();

  return (
    <div className="w-full md:w-64 flex-shrink-0 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex justify-between items-center mb-4 pb-2 border-b border-gray-100 dark:border-gray-700">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <CalendarCheckIcon className="text-primary-500" />
          {t('courses.form.semesterLabel', 'Semesters')}
        </h2>
        <button
          onClick={onAdd}
          className="p-1.5 bg-primary-50 hover:bg-primary-100 text-primary-600 rounded-lg text-sm font-medium transition"
          title={t('courses.new_semester')}
        >
          <PlusIcon weight="bold" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
        {loading ? (
          [...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-10 w-full rounded-lg" />
          ))
        ) : (
          <>
            {semesters.length === 0 && (
              <div className="text-gray-400 text-sm italic text-center py-4">
                {t('courses.emptySemesters', 'No semesters found.')}
              </div>
            )}
            {semesters.map(sem => (
              <button
                key={sem.id}
                onClick={() => onSelect(sem)}
                className={`
                  w-full text-left px-4 py-3 rounded-lg text-sm font-medium transition
                  ${selectedSemester?.id === sem.id
                    ? 'bg-primary-600 text-white shadow-md'
                    : 'bg-gray-50 dark:bg-gray-700/50 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }
                `}
              >
                <div className="font-semibold">{sem.name}</div>
                <div className="text-xs opacity-80 mt-1">
                  {sem.start_date ? new Date(sem.start_date).getFullYear() : ''}
                </div>
              </button>
            ))}
          </>
        )}
      </div>
    </div>
  );
};

export default SemesterSidebar;
