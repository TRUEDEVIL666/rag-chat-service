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

// Response interceptor for handling 401 errors
api.interceptors.response.use(
  (response) => response,
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
