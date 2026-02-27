import api from './api';

export const userService = {
  getUsers: async (limit = 20, cursor_timestamp = null, filters = {}, options = {}) => {
    const params = { limit, ...filters };
    if (cursor_timestamp) {
      params.cursor_timestamp = cursor_timestamp;
    }
    const response = await api.get('/users', { params, ...options });
    return response.data;
  },

  createUser: async (userData, options = {}) => {
    const response = await api.post('/users', userData, options);
    return response.data;
  },

  createUsersBatch: async (users, options = {}) => {
    const response = await api.post('/users/batch', { users }, options);
    return response.data;
  },

  updateUser: async (id, userData, options = {}) => {
    const response = await api.put(`/users/${id}`, userData, options);
    return response.data;
  },

  deleteUser: async (id, options = {}) => {
    const response = await api.delete(`/users/${id}`, options);
    return response.data;
  },

  deleteUsersBatch: async (ids, options = {}) => {
    const response = await api.delete('/users', { data: ids, ...options });
    return response.data;
  }
};
