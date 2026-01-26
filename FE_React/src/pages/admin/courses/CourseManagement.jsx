import { useState, useEffect, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-hot-toast';
import { useNavigate, useOutletContext } from 'react-router-dom';
import { ROUTES } from '../../../routes';
import courseService from '../../../services/courseService';

import CreateSemesterModal from './components/CreateSemesterModal';
import CreateCourseModal from './components/CreateCourseModal';
import SemesterSidebar from './components/SemesterSidebar';
import CourseGrid from './components/CourseGrid';

const CourseManagement = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { setTitle } = useOutletContext();

  // State
  const [semesters, setSemesters] = useState([]);
  const [courses, setCourses] = useState([]);
  // Use Ref for cache to ensure stability and avoid dependency loops
  const coursesCacheRef = useRef({}); // Cache: { semesterId: [courses] }
  const [selectedSemester, setSelectedSemester] = useState(null);
  const [loading, setLoading] = useState(true);
  const [coursesLoading, setCoursesLoading] = useState(false);

  // Modal State
  const [isSemesterModalOpen, setIsSemesterModalOpen] = useState(false);
  const [isCourseModalOpen, setIsCourseModalOpen] = useState(false);

  // Concurrency Refs
  const activeSemesterIdRef = useRef(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    setTitle(t('courses.title', 'Course Management'));
    return () => { mountedRef.current = false; };
  }, [t, setTitle]);

  // Data Loading
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const semData = await courseService.listSemesters();

      if (mountedRef.current) {
        setSemesters(semData);
        if (semData.length > 0) {
          setSelectedSemester(prev => prev || semData[0]);
        }
      }
    } catch (error) {
      if (mountedRef.current) {
        console.error("Error loading data", error);
        toast.error(t('courses.load_error', 'Failed to load data'));
      }
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, []); // Stable: No dependencies

  const loadCourses = useCallback(async (semesterId) => {
    if (!semesterId) return;

    activeSemesterIdRef.current = semesterId;

    // Check Cache Ref (Synchronous, no re-render needed for check)
    if (coursesCacheRef.current[semesterId]) {
      setCourses(coursesCacheRef.current[semesterId]);
      return;
    }

    setCoursesLoading(true);

    try {
      const courseData = await courseService.listCourses({ semester_id: semesterId });

      if (mountedRef.current && activeSemesterIdRef.current === semesterId) {
        setCourses(courseData);
        // Update Cache Ref
        coursesCacheRef.current[semesterId] = courseData;
      }
    } catch (error) {
      if (mountedRef.current) {
        console.error("Error loading courses", error);
        toast.error(t('courses.load_courses_error', 'Failed to load courses'));
      }
    } finally {
      if (mountedRef.current && activeSemesterIdRef.current === semesterId) {
        setCoursesLoading(false);
      }
    }
  }, []); // Stable: No dependencies needed for Ref

  // Initial Load
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Semester Change
  useEffect(() => {
    if (selectedSemester) {
      loadCourses(selectedSemester.id);
    } else {
      setCourses([]);
    }
  }, [selectedSemester, loadCourses]);

  // Handlers
  const handleCreateSemester = useCallback(async (data) => {
    await courseService.createSemester(data);
    toast.success(t('courses.semester_created', 'Semester created!'));
    loadData();
  }, [loadData, t]);

  const handleCreateCourse = useCallback(async (data) => {
    await courseService.createCourse(data);
    toast.success(t('courses.createSuccess', 'Course created!'));

    // Invalidate cache for this semester so we fetch the new course
    if (selectedSemester) {
      const semId = selectedSemester.id;
      if (coursesCacheRef.current[semId]) {
        delete coursesCacheRef.current[semId];
      }
      loadCourses(semId);
    }
  }, [selectedSemester, loadCourses, t]);

  const handleDeleteCourse = async (course) => {
    try {
      // 1. Check validation: Course can be deleted if there's no class.
      // We explicitly check this to prevent accidental orphaned data or backend errors.
      // Assuming listClasses returns array.
      const classes = await courseService.listClasses({ course_id: course.id });

      if (classes.length > 0) {
        toast.error(t('courses.delete_constraint_classes', 'Cannot delete course with active classes. Please delete classes first.'), {
          duration: 5000,
          icon: '⚠️'
        });
        return;
      }

      // 2. Confirm
      if (!window.confirm(t('courses.delete_confirm', `Are you sure you want to delete ${course.name}?`))) {
        return;
      }

      // 3. Delete
      await courseService.deleteCourse(course.id);
      toast.success(t('common.deleted', 'Deleted successfully'));

      // 4. Update Cache & State
      if (selectedSemester) {
        const semId = selectedSemester.id;
        // Remove from cache
        if (coursesCacheRef.current[semId]) {
          // Option A: Just invalidate and reload (Safest)
          delete coursesCacheRef.current[semId];
          loadCourses(semId);
        } else {
          // Just reload to be sure
          loadCourses(semId);
        }
      }

    } catch (error) {
      console.error(error);
      toast.error(t('common.error', 'Action failed'));
    }
  };

  return (
    <div className="flex flex-col md:flex-row h-full gap-6">
      {/* Left Column: Semesters Vertical Bar */}
      <SemesterSidebar
        semesters={semesters}
        selectedSemester={selectedSemester}
        onSelect={setSelectedSemester}
        onAdd={() => setIsSemesterModalOpen(true)}
        loading={loading}
      />

      {/* Right Column: Courses Grid */}
      <CourseGrid
        courses={courses}
        loading={coursesLoading}
        selectedSemester={selectedSemester}
        onAdd={() => setIsCourseModalOpen(true)}
        onSelect={(course) => navigate(ROUTES.ADMIN.COURSES.DETAIL(course.id))}
        onDelete={handleDeleteCourse}
      />

      <CreateSemesterModal
        isOpen={isSemesterModalOpen}
        onClose={() => setIsSemesterModalOpen(false)}
        onCreate={handleCreateSemester}
      />

      <CreateCourseModal
        isOpen={isCourseModalOpen}
        onClose={() => setIsCourseModalOpen(false)}
        onCreate={handleCreateCourse}
        selectedSemester={selectedSemester}
      />
    </div>
  );
};

export default CourseManagement;
