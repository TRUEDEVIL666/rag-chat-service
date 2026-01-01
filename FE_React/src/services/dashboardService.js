import api from './api';

export const dashboardService = {
  getStats: async (timeRange = '30days') => {
    const response = await api.get('/analytics/summary', {
      params: { time_range: timeRange }
    });
    return response.data;
  }
};
