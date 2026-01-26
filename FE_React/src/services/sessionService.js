import api from './api';

export const sessionService = {
  getSessions: async (limit = 10, cursorTimestamp = null, options = {}) => {
    const response = await api.get('/sessions', {
      params: { 
        limit, 
        cursor_timestamp: cursorTimestamp 
      },
      ...options
    });
    return response.data;
  },

  deleteSession: async (sessionId, options = {}) => {
    const response = await api.delete(`/sessions/${sessionId}`, options);
    return response.data;
  },

  getSessionMessages: async (sessionId, limit = 50, cursorTimestamp = null, options = {}) => {
    const response = await api.get(`/sessions/${sessionId}/messages`, {
      params: { 
        limit,
        cursor_timestamp: cursorTimestamp 
      },
      ...options
    });
    return response.data;
  }
};
