import api from './api';

export const authService = {
  login: async (email, password) => {
    const response = await api.post('/login', { email, password });
    return response.data;
  },

  register: async (userData) => {
    const response = await api.post('/register', userData);
    return response.data;
  },

  getCurrentUser: async () => {
    // Assuming there's an endpoint to get current user details if needed, 
    // otherwise just rely on decoded token in the AuthContext.
    // For now, this might not be strictly necessary if we just use the token.
    return null; 
  }
};
