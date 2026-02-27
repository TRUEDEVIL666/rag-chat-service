import React from 'react';
import { RobotIcon } from '@phosphor-icons/react';
import { useTranslation } from 'react-i18next';

const CourseCard = ({ course, onClick }) => {
  const { t } = useTranslation();
  return (
    <div
      onClick={onClick}
      className="bg-white/80 dark:bg-slate-800/80 p-5 rounded-2xl border border-gray-100 dark:border-slate-700/50 hover:shadow-lg hover:border-indigo-500/30 dark:hover:border-indigo-500/30 transition-all duration-300 cursor-pointer flex justify-between items-center group relative overflow-hidden backdrop-blur-sm"
    >
      {/* Hover Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-transparent to-indigo-500/5 dark:to-indigo-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

      <div className="relative z-10">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-bold px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-300 border border-indigo-100 dark:border-indigo-500/20">
            {course.course_code}
          </span>
          {course.section && (
            <span className="text-xs px-2 py-0.5 rounded-md bg-slate-100 text-slate-500 dark:bg-slate-700/50 dark:text-slate-400">
              {t('courses.class.section', 'Sec')} {course.section}
            </span>
          )}
        </div>
        <h3 className="font-bold text-lg text-gray-800 dark:text-gray-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
          {course.course_name}
        </h3>
        {course.semester && (
          <p className="text-xs text-slate-400 mt-1">{course.semester.name}</p>
        )}
      </div>

      <div className="relative z-10 p-3 bg-indigo-50 dark:bg-indigo-500/10 rounded-xl group-hover:bg-indigo-600 group-hover:text-white dark:group-hover:bg-indigo-500 transition-all duration-300 shadow-sm">
        <RobotIcon
          className="text-indigo-600 dark:text-indigo-400 group-hover:text-white transition-colors duration-300"
          size={24}
          weight="duotone"
        />
      </div>
    </div>
  );
};

export default CourseCard;
