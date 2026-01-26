import { useState, useCallback } from 'react';
import { dashboardService } from '../services/dashboardService';

export const useDashboard = () => {
  const [stats, setStats] = useState(null);
  const [chartData, setChartData] = useState(null);
  
  // New Bento States
  const [activity, setActivity] = useState([]);
  const [topics, setTopics] = useState([]);
  const [engagement, setEngagement] = useState(null);
  const [feedback, setFeedback] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchDashboardData = useCallback(async (withLoading = true, signal) => {
    if (withLoading) setLoading(true);
    try {
      const options = { signal };
      const [
        statsData, 
        activityData, 
        topicsData, 
        engagementData, 
        feedbackData
      ] = await Promise.all([
        dashboardService.getStatsSummary(options),
        dashboardService.getRecentActivity(options),
        dashboardService.getTrendingTopics(options),
        dashboardService.getEngagementStats(options),
        dashboardService.getFeedbackSummary(options)
      ]);

      if (signal?.aborted) return;

      setStats(statsData);
      setActivity(activityData);
      setTopics(topicsData);
      setEngagement(engagementData);
      setFeedback(feedbackData);
      setError(null);
    } catch (err) {
      if (err.code === 'ERR_CANCELED' || err.name === 'AbortError') return;
      setError(err);
      console.error("Failed to fetch dashboard data", err);
    } finally {
      if (withLoading && !signal?.aborted) setLoading(false);
    }
  }, []);

  return {
    stats,
    activity,
    topics,
    engagement,
    feedback,
    loading,
    error,
    fetchDashboardData
  };
};
