export const ROUTES = {
  HOME: '/',
  AUTH: {
    LOGIN: '/login',
    REGISTER: '/register',
  },
  ADMIN: {
    ROOT: '/admin',
    DASHBOARD: '/admin/dashboard',
    SETTINGS: '/admin/settings',
    AI_MODELS: '/admin/ai-models',
    BOTS: {
      LIST: '/admin/bots',
      CREATE: '/admin/bots/create',
      EDIT: (id) => `/admin/bots/${id}`,
      KNOWLEDGE: (id) => `/admin/bots/${id}/knowledge`,
    },
    DOCUMENTS: {
      LIST: '/admin/documents',
      UPLOAD: '/admin/documents/upload',
    },
    USERS: {
      LIST: '/admin/users',
      CREATE: '/admin/users/create',
    },
    CHAT: {
      BOT: (botId, sessionId) => `/admin/chat/${botId}${sessionId ? `?sessionId=${sessionId}` : ''}`,
      HISTORY: '/admin/history',
    },
    COURSES: {
      LIST: '/admin/courses',
      DETAIL: (id) => `/admin/courses/${id}`,
    },
    CLASSES: {
      LIST: '/admin/classes',
      DETAIL: (id) => `/admin/classes/${id}`,
    }
  },
  USER: {
    ROOT: '/user',
    HOME: '/user/home',
    CLASSES: '/user/classes',
    CLASS_DETAIL: (id) => `/user/classes/${id}`,
    SETTINGS: '/user/settings',
    CHAT: (botId, sessionId) => `/user/chat/${botId}${sessionId ? `?sessionId=${sessionId}` : ''}`,
    HISTORY: '/user/history',
  }
};
