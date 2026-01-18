import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1';

export const quizService = {
  submitAttempt: async (attemptData) => {
    try {
      const response = await axios.post(`${API_BASE}/quiz/submit`, attemptData, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });
      return response.data;
    } catch (error) {
      console.error("Error submitting quiz attempt:", error);
      throw error;
    }
  },

  getHistory: async ({ limit = 20 } = {}) => {
    try {
      const response = await axios.get(`${API_BASE}/quiz/history`, {
        params: { limit },
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching quiz history:", error);
      throw error;
    }
  },
};
