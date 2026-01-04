import api from './api';

export const dashboardService = {

  getStatsSummary: async () => {
    const response = await api.get('/analytics/stats');
    return response.data;
  },

  getChartData: async (timeRange = '30days') => {
    const response = await api.get('/analytics/chart', {
      params: { time_range: timeRange }
    });
    return response.data;
  }
};
