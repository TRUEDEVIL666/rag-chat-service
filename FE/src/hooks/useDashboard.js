import { useState, useCallback } from 'react';
import { dashboardService } from '../services/dashboardService';

export const useDashboard = () => {
  const [stats, setStats] = useState(null);
  
  // New Bento States
  const [activity, setActivity] = useState([]);
  const [topics, setTopics] = useState([]);
  const [engagement, setEngagement] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [chartData, setChartData] = useState([]);

  // Granular Loading States
  const [loadingStats, setLoadingStats] = useState(false);
  const [loadingActivity, setLoadingActivity] = useState(false);
  const [loadingTopics, setLoadingTopics] = useState(false);
  const [loadingEngagement, setLoadingEngagement] = useState(false);
  const [loadingFeedback, setLoadingFeedback] = useState(false);
  const [loadingChart, setLoadingChart] = useState(false);

  // Global error for critical failures, or we could have granular errors
  const [error, setError] = useState(null);

  const fetchDashboardData = useCallback((withLoading = true, signal, range = '7days') => {
    const options = { signal };

    // Helper to fetch independent logic
    const fetchData = async (setter, loader, serviceCall, params = null) => {
      if (withLoading) loader(true);
      try {
        const data = params ? await serviceCall(params, options) : await serviceCall(options);
        if (!signal?.aborted) setter(data);
      } catch (err) {
        if (!signal?.aborted && err.name !== 'CanceledError' && err.code !== 'ERR_CANCELED') {
           console.error(`Failed to fetch dashboard component`, err);
        }
      } finally {
        if (withLoading && !signal?.aborted) loader(false);
      }
    };

    // Trigger all fetches in parallel independently
    fetchData(setStats, setLoadingStats, dashboardService.getStatsSummary);
    fetchData(setActivity, setLoadingActivity, dashboardService.getRecentActivity);
    fetchData(setTopics, setLoadingTopics, dashboardService.getTrendingTopics);
    fetchData(setEngagement, setLoadingEngagement, dashboardService.getEngagementStats);
    fetchData(setFeedback, setLoadingFeedback, dashboardService.getFeedbackSummary);
    fetchData(setChartData, setLoadingChart, dashboardService.getChartData, range);
    
  }, []);

  return {
    stats,
    activity,
    topics,
    engagement,
    feedback,
    chartData,
    loadingStats,
    loadingActivity,
    loadingTopics,
    loadingEngagement,
    loadingFeedback,
    loadingChart,
    loading: loadingStats || loadingActivity || loadingTopics || loadingEngagement || loadingFeedback || loadingChart, // aggregated for backward compat
    error,
    fetchDashboardData
  };
};
