import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeftIcon, PlusIcon, TrashIcon, BookOpenIcon, RobotIcon, CalendarCheckIcon, ChalkboardTeacherIcon, FilesIcon } from '@phosphor-icons/react';
import { toast } from 'react-hot-toast';
import { ROUTES } from '../../../routes';
import courseService from '../../../services/courseService';
import { kbsService } from '../../../services/kbsService';
import { userService } from '../../../services/userService';
import Skeleton from '../../../components/common/Skeleton';
import CreateClassModal from './components/CreateClassModal';

const CourseDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { t } = useTranslation();

  // State
  const [course, setCourse] = useState(null);
  const [classes, setClasses] = useState([]);
  const [instructors, setInstructors] = useState([]);
  const [allKbs, setAllKbs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isClassModalOpen, setIsClassModalOpen] = useState(false);

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    setLoading(true);
    try {
      // Optimized: Fetch course, classes, users, and KBs in parallel
      const [courseData, classesData, usersData, kbsData] = await Promise.all([
        courseService.getCourse(id),
        courseService.listClasses({ course_id: id }),
        userService.getUsers(100), // Fetch potential instructors
        kbsService.getKnowledgeBases()
      ]);

      setCourse(courseData);
      setClasses(classesData);
      setInstructors(usersData.items || []); // Assuming paginated response with 'items'
      setAllKbs(Array.isArray(kbsData) ? kbsData : (kbsData?.data || []));
    } catch (error) {
      console.error(error);
      toast.error(t('courses.load_error', "Failed to load course details"));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateClass = async (data) => {
    try {
      await courseService.createClass({
        course_id: id,
        semester_id: course.semester_id,
        section: data.section,
        instructor_id: data.instructor_id,
        max_students: 50 // Default
      });
      toast.success(t('courses.class.createSuccess', "Class created!"));
      setIsClassModalOpen(false);
      loadData();
    } catch (error) {
      console.error(error);
      toast.error(t('courses.create_failed', "Failed to create class"));
    }
  };

  const handleDeleteClass = async (cls) => {
    try {
      // 1. Check constraints: Class can be deleted if there's no students.
      const students = await courseService.getClassStudents(cls.id);

      if (students.length > 0) {
        toast.error(t('courses.delete_constraint_students', 'Cannot delete class with enrolled students. Please remove them first.'), {
          duration: 5000,
          icon: '⚠️'
        });
        return;
      }

      // 2. Confirm
      if (!window.confirm(t('courses.class_delete_confirm', `Are you sure you want to delete class ${cls.name}?`))) {
        return;
      }

      // 3. Delete
      await courseService.deleteClass(cls.id);
      toast.success(t('common.deleted', 'Deleted successfully'));
      loadData(); // Reload to remove from list

    } catch (error) {
      console.error(error);
      toast.error(t('common.error', 'Action failed'));
    }
  };

  // Helper to map IDs to Names (Returns Objects now)
  const getKbObjects = () => {
    if (!course?.kb_ids || !allKbs.length) return [];
    return course.kb_ids.map(kbId => {
      const found = allKbs.find(k => k.id === kbId);
      return found ? { id: found.id, name: found.name } : { id: kbId, name: kbId };
    });
  };

  if (loading && !course) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-6 w-32" />
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-100 dark:border-gray-700">
          <Skeleton className="h-8 w-1/2 mb-2" />
          <Skeleton className="h-4 w-1/4" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-32 w-full rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  if (!course) return <div className="p-10">{t('courses.not_found', "Course not found")}</div>;

  return (
    <div className="p-6 space-y-6">
      <button onClick={() => navigate(ROUTES.ADMIN.COURSES.LIST)} className="flex items-center text-gray-500 hover:text-primary-600 transition">
        <ArrowLeftIcon className="mr-2" /> {t('courses.detail.backToList', "Back to Courses")}
      </button>

      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-100 dark:border-gray-700">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
              <BookOpenIcon className="text-primary-500" />
              {course.code}: {course.name}
            </h1>
            <p className="text-gray-500 flex items-center gap-2 mt-1">
              <CalendarCheckIcon weight="fill" className="text-gray-400" />
              {t('courses.semester')}: {course.semester_name || course.semester_id || t('courses.semester_unknown', 'Unknown Semester')}
            </p>

            {/* Knowledge Bases Badge Section */}
            <div className="mt-3 flex items-center gap-2 flex-wrap">
              <FilesIcon className="text-gray-400" />
              <span className="text-gray-500">{t('courses.knowledgeBases', 'Knowledge Bases')}:</span>
              {getKbObjects().length > 0 ? (
                getKbObjects().map((kbData, idx) => (
                  <button
                    key={idx}
                    onClick={() => navigate(ROUTES.ADMIN.DOCUMENTS.LIST, {
                      state: { kbId: kbData.id, kbName: kbData.name }
                    })}
                    className="bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 px-2 py-0.5 rounded text-sm border border-blue-100 dark:border-blue-800 hover:bg-blue-100 hover:underline cursor-pointer transition select-none"
                    title={t('courses.view_kb_content', 'View Knowledge Base Content')}
                  >
                    {kbData.name}
                  </button>
                ))
              ) : (
                <span className="text-gray-400 italic text-sm">{t('common.none', 'None')}</span>
              )}
            </div>
          </div>
          <button
            onClick={() => setIsClassModalOpen(true)}
            className="btn-primary flex items-center gap-2"
          >
            <PlusIcon weight="bold" />
            {t('courses.detail.addClass', 'New Class')}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {classes.length === 0 && (
          <div className="col-span-full py-8 text-center text-gray-500 italic">
            {t('courses.emptyClasses', "No classes created yet.")}
          </div>
        )}
        {classes.map(cls => (
          <div
            key={cls.id}
            onClick={() => navigate(ROUTES.ADMIN.CLASSES.DETAIL(cls.id))}
            className="bg-white dark:bg-gray-800 p-5 rounded-xl border border-gray-200 dark:border-gray-700 hover:shadow-lg transition cursor-pointer group"
          >
            <div className="flex justify-between items-center mb-4">
              <span className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300 px-3 py-1 rounded-full text-sm font-bold">
                {cls.name}
              </span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteClass(cls);
                }}
                className="p-2 -mr-2 rounded-full hover:bg-red-50 text-gray-400 hover:text-red-500 transition"
                title={t('common.delete', 'Delete')}
              >
                <TrashIcon size={20} />
              </button>
            </div>
            <div className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
              <p className="flex items-center gap-2">
                <ChalkboardTeacherIcon size={16} />
                {t('courses.class.instructor', 'Instructor')}: {instructors.find(u => u.id === cls.instructor_id)?.email || t('common.unknown', 'Unknown')}
              </p>

              <p className="flex items-center gap-2">
                <RobotIcon size={16} />
                {cls.bot_id ? t('courses.class.bots', "Bot Assigned") : t('courses.class.noBots', "No Bot")}
              </p>
            </div>
          </div>
        ))}
      </div>

      <CreateClassModal
        isOpen={isClassModalOpen}
        onClose={() => setIsClassModalOpen(false)}
        onCreate={handleCreateClass}
        instructors={instructors}
      />
    </div>
  );
};

export default CourseDetail;
