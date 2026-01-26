import api from './api';

export const dashboardService = {

  getStatsSummary: async (options = {}) => {
    const response = await api.get('/analytics/stats', options);
    return response.data;
  },

  getChartData: async (timeRange = '30days', options = {}) => {
    const response = await api.get('/analytics/chart', {
      params: { time_range: timeRange },
      ...options
    });
    return response.data;
  },

  getRecentActivity: async (options = {}) => {
    const response = await api.get('/analytics/activity', options);
    return response.data;
  },

  getTrendingTopics: async (options = {}) => {
    const response = await api.get('/analytics/topics', options);
    return response.data;
  },

  getEngagementStats: async (options = {}) => {
    const response = await api.get('/analytics/engagement', options);
    return response.data;
  },

  getFeedbackSummary: async (options = {}) => {
    const response = await api.get('/analytics/feedback', options);
    return response.data;
  }
};
