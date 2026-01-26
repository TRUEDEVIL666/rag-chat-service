import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1';

export const quizService = {
  submitAttempt: async (attemptData, options = {}) => {
    try {
      const response = await axios.post(`${API_BASE}/quiz/submit`, attemptData, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        ...options
      });
      return response.data;
    } catch (error) {
      console.error("Error submitting quiz attempt:", error);
      throw error;
    }
  },

  getHistory: async ({ limit = 20, ...options } = {}) => {
    // Extract limit from options if present in first arg, but standard pattern is usually (params, options)
    // The current sig is ({limit}). I'll change to (params, options) or support both.
    // Preserving sig: getHistory({limit, ...options}) where options contains signal
    try {
      const response = await axios.get(`${API_BASE}/quiz/history`, {
        params: { limit },
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        ...options
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching quiz history:", error);
      throw error;
    }
  },
};
