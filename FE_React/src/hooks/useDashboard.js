import { useState, useCallback } from 'react';
import { dashboardService } from '../services/dashboardService';

export const useDashboard = () => {
  const [stats, setStats] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [loadingStats, setLoadingStats] = useState(false);
  const [loadingChart, setLoadingChart] = useState(false);
  const [error, setError] = useState(null);

  const fetchSummary = useCallback(async () => {
    setLoadingStats(true);
    try {
      const data = await dashboardService.getStatsSummary();
      setStats(data);
      setError(null);
    } catch (err) {
      setError(err);
      console.error("Failed to fetch dashboard summary", err);
    } finally {
      setLoadingStats(false);
    }
  }, []);

  const fetchChart = useCallback(async (timeRange) => {
    setLoadingChart(true);
    try {
      const data = await dashboardService.getChartData(timeRange);
      setChartData(data);
    } catch (err) {
      console.error("Failed to fetch chart data", err);
    } finally {
      setLoadingChart(false);
    }
  }, []);

  const fetchAll = useCallback(async (timeRange) => {
    fetchSummary();
    fetchChart(timeRange);
  }, [fetchSummary, fetchChart]);

  return {
    stats,
    chartData,
    loadingStats,
    loadingChart,
    error,
    fetchSummary,
    fetchChart,
    fetchAll
  };
};
