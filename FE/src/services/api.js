import axios from 'axios';
import config from '../config';

const api = axios.create({
  baseURL: config.api.baseURL,
});

// Request interceptor for adding the auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    // Automatically extract 'data' from BaseResponse envelope
    if (response.data && response.data.success !== undefined) {
      if (response.data.success) {
        return {
          ...response,
          data: response.data.data
        };
      } else {
        // Handle explicit API errors
        return Promise.reject({
          response: {
            status: 400,
            data: { detail: response.data.error || response.data.message || 'API Error' }
          }
        });
      }
    }
    return response;
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('token');
      if (window.logout) {
        window.logout();
      } else {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
