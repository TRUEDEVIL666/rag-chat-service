export const ROUTES = {
  AUTH: {
    LOGIN: '/login',
    REGISTER: '/register',
  },
  ADMIN: {
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
      LIST: '/admin/knowledge-bases',
      DETAIL: (id) => `/admin/knowledge-bases/${id}`,
      UPLOAD: '/admin/knowledge-bases/upload',
    },
    USERS: {
      LIST: '/admin/users',
      CREATE: '/admin/users/create',
    },
    CHAT: {
      BOT: (botId, sessionId) => sessionId ? `/admin/chat/${botId}?session=${sessionId}` : `/admin/chat/${botId}`,
    },
    HISTORY: '/admin/history',
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
    HOME: '/user/home',
    CHAT: (botId, sessionId) => sessionId ? `/user/chat/${botId}?session=${sessionId}` : `/user/chat/${botId}`,
    CLASSES: '/user/classes',
    CLASS_DETAIL: (id) => `/user/classes/${id}`,
    SETTINGS: '/user/settings',
    HISTORY: '/user/history',
  }
};
