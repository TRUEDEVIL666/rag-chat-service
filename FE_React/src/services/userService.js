import api from './api';

export const userService = {
  getUsers: async (limit = 20, cursor_timestamp = null, filters = {}) => {
    const params = { limit, ...filters };
    if (cursor_timestamp) {
      params.cursor_timestamp = cursor_timestamp;
    }
    const response = await api.get('/users', { params });
    return response.data;
  },

  createUser: async (userData) => {
    const response = await api.post('/users', userData);
    return response.data;
  },

  updateUser: async (id, userData) => {
    const response = await api.put(`/users/${id}`, userData);
    return response.data;
  },

  deleteUser: async (id) => {
    const response = await api.delete(`/users/${id}`);
    return response.data;
  }
};
