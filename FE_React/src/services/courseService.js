import api from './api';

const courseService = {
  // Semesters
  listSemesters: async (options = {}) => {
    const response = await api.get('/semesters', options);
    return response.data;
  },

  createSemester: async (data, options = {}) => {
    // data: { name, start_date, end_date }
    const response = await api.post('/semesters', data, options);
    return response.data;
  },

  // Courses
  listCourses: async (params, options = {}) => {
    // params: { semester_id, tenant_id }
    const response = await api.get('/courses', { params, ...options });
    return response.data;
  },

  getCourse: async (id, options = {}) => {
    const response = await api.get(`/courses/${id}`, options);
    return response.data;
  },

  createCourse: async (data, options = {}) => {
    // data: { code, name, semester_id, tenant_id }
    const response = await api.post('/courses', data, options);
    return response.data;
  },

  // Classes
  listClasses: async (params, options = {}) => {
    // params: { semester_id, course_id, min_size, etc }
    const response = await api.get('/classes', { params, ...options });
    return response.data;
  },

  getClass: async (id, options = {}) => {
    const response = await api.get(`/classes/${id}`, options);
    return response.data;
  },

  createClass: async (data, options = {}) => {
    // data: { course_id, section, schedule, max_students }
    const response = await api.post('/classes', data, options);
    return response.data;
  },

  enrollStudent: async (classId, studentId, options = {}) => {
    const response = await api.post(`/classes/${classId}/enroll`, {}, options);
    return response.data;
  },

  getMyClasses: async (options = {}) => {
    const response = await api.get('/my-classes', options);
    return response.data;
  },

  getMyClassBots: async (options = {}) => {
    const response = await api.get('/my-class-bots', options);
    return response.data;
  },

  getClassStudents: async (id, options = {}) => {
    const response = await api.get(`/classes/${id}/students`, options);
    return response.data;
  },

  addStudentsToClass: async (classId, userIds, options = {}) => {
    const response = await api.post(`/classes/${classId}/students`, { user_ids: userIds }, options);
    return response.data;
  },

  getClassBots: async (id, options = {}) => {
    const response = await api.get(`/classes/${id}/bots`, options);
    return response.data;
  },

  addBotsToClass: async (classId, botIds, options = {}) => {
    const response = await api.post(`/classes/${classId}/bots`, { bot_ids: botIds }, options);
    return response.data;
  },

  getClassKBs: async (id, options = {}) => {
    const response = await api.get(`/classes/${id}/kbs`, options);
    return response.data;
  },

  getClassDocuments: async (id, options = {}) => {
    const response = await api.get(`/classes/${id}/documents`, options);
    return response.data;
  },

  getDocumentViewUrl: async (docId, options = {}) => {
    const response = await api.get(`/documents/${docId}/download`, options);
    return response.data;
  },

  removeStudentFromClass: async (classId, userId, options = {}) => {
    const response = await api.delete(`/classes/${classId}/students/${userId}`, options);
    return response.data;
  },

  removeBotFromClass: async (classId, botId, options = {}) => {
    const response = await api.delete(`/classes/${classId}/bots/${botId}`, options);
    return response.data;
  },

  deleteCourse: async (id, options = {}) => {
    const response = await api.delete(`/courses/${id}`, options);
    return response.data;
  },

  deleteClass: async (id, options = {}) => {
    const response = await api.delete(`/classes/${id}`, options);
    return response.data;
  }
};

export default courseService;
