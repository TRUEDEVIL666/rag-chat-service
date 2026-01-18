import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { CurrencyDollarIcon, ChatCircleTextIcon, UserPlusIcon, QuestionIcon, FileTextIcon, WarningIcon } from '@phosphor-icons/react';
import { useDashboard } from '../../hooks/useDashboard';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { usePageTour } from '../../hooks/usePageTour';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
  Legend
);

const Dashboard = () => {
  const { t } = useTranslation();
  const { theme } = useTheme();
  const navigate = useNavigate();

  // Data Hooks
  const { stats, loadingStats, error: statsError, fetchSummary } = useDashboard();

  const [recentDocs, setRecentDocs] = useState([]);
  const [timeRange, setTimeRange] = useState('30days'); // '7days', '30days', 'all'

  const [realTimeChartData, setRealTimeChartData] = useState([]);
  const [loadingStream, setLoadingStream] = useState(false);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  useEffect(() => {
    let isMounted = true;
    const controller = new AbortController();

    const streamChartData = async () => {
      setLoadingStream(true);
      setRealTimeChartData([]); // Reset on new range

      try {
        const token = localStorage.getItem('token');
        if (!token) return;

        const response = await fetch(`${import.meta.env.VITE_API_BASE}/analytics/chart?time_range=${timeRange}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          },
          signal: controller.signal
        });

        if (!response.ok) throw new Error('Network response was not ok');

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (isMounted) {
          const { value, done } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;

          const lines = buffer.split('\n\n');
          // Keep the last partial line in the buffer
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const jsonStr = line.substring(6);
              try {
                const newData = JSON.parse(jsonStr);
                // Merge data: chunks are arrays of daily stats
                setRealTimeChartData(prev => {
                  // Merge and sort
                  const merged = [...prev, ...newData];
                  // Basic dedication not strictly needed if backend is ordered, but good safety
                  // Sort by date strings
                  return merged.sort((a, b) => a.period_date.localeCompare(b.period_date));
                });
              } catch (e) {
                console.error("Failed to parse chunk", e);
              }
            }
          }
        }
      } catch (err) {
        if (err.name !== 'AbortError') {
          console.error("Stream failed", err);
        }
      } finally {
        if (isMounted) setLoadingStream(false);
      }
    };

    streamChartData();

    return () => {
      isMounted = false;
      controller.abort();
    };
  }, [timeRange]);



  useEffect(() => {
    if (stats?.recent_documents) {
      setRecentDocs(stats.recent_documents);
    }
  }, [stats]);

  // Process real chart data or fallback to empty
  const chartLabels = React.useMemo(() => {
    if (!realTimeChartData) return [];
    return realTimeChartData.map(item => item.period_date);
  }, [realTimeChartData]);

  const chartValues = React.useMemo(() => {
    if (!realTimeChartData) return [];
    return realTimeChartData.map(item => item.count);
  }, [realTimeChartData]);

  const chartData = {
    labels: chartLabels.length > 0 ? chartLabels : ['No Data'],
    datasets: [
      {
        label: t('admin.dashboard.total_messages'),
        data: chartValues.length > 0 ? chartValues : [0],
        fill: true,
        backgroundColor: (context) => {
          const ctx = context.chart.ctx;
          const gradient = ctx.createLinearGradient(0, 0, 0, 400);
          gradient.addColorStop(0, 'rgba(59, 130, 246, 0.5)');
          gradient.addColorStop(1, 'rgba(59, 130, 246, 0.05)');
          return gradient;
        },
        borderColor: '#3b82f6',
        tension: 0.4,
        pointBackgroundColor: '#fff',
        pointBorderColor: '#3b82f6',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false, // Hide default legend as we have custom one
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(17, 24, 39, 0.9)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        padding: 10,
        displayColors: false,
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
          drawBorder: false,
        },
        ticks: {
          color: '#9ca3af', // gray-400
          font: {
            size: 11
          }
        }
      },
      y: {
        grid: {
          color: 'rgba(243, 244, 246, 0.6)', // gray-100 equivalent
          borderDash: [5, 5],
          drawBorder: false,
        },
        ticks: {
          color: '#9ca3af', // gray-400
          font: {
            size: 11
          },
          padding: 10
        },
        min: 0,
        grace: '5%',
      }
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false
    }
  };

  // Tour Steps
  const tourSteps = [
    { element: '#dashboard-title', popover: { title: t('tour.dashboard.title'), description: t('tour.dashboard.desc'), side: "bottom" } },
    { element: '#time-filters', popover: { title: t('tour.dashboard.filters'), description: t('tour.dashboard.filters_desc'), side: "bottom" } },
    { element: '#stat-cards', popover: { title: t('tour.dashboard.stats'), description: t('tour.dashboard.stats_desc'), side: "bottom" } },
    { element: '#activity-chart', popover: { title: t('tour.dashboard.chart'), description: t('tour.dashboard.chart_desc'), side: "top" } },
    { element: '#recent-activity', popover: { title: t('tour.dashboard.recent'), description: t('tour.dashboard.recent_desc'), side: "left" } },
  ];
  const { startTour } = usePageTour('dashboard', tourSteps);

  const getStatusBadge = (status) => {
    const s = status?.toLowerCase();
    if (s === 'active') return <span className="inline-block px-2 py-0.5 rounded text-xs font-semibold bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400">{t('common.status.active')}</span>;
    if (s === 'closed') return <span className="inline-block px-2 py-0.5 rounded text-xs font-semibold bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400">{t('common.status.closed')}</span>;
    return <span className="inline-block px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">{t(`common.status.${s}`, status || 'Unknown')}</span>;
  };




  return (
    <div className="flex-1 overflow-auto p-6" id="dashboard-content">
      {/* Page Title & Filters */}
      {/* Page Title */}
      <div className="mb-8 flex items-center gap-3" id="dashboard-title">
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white">{t('admin.dashboard.title')}</h1>
        <button
          onClick={startTour}
          className="w-8 h-8 bg-red-600 text-white rounded-full shadow-lg shadow-red-200 flex items-center justify-center hover:bg-red-700 transition"
          title={t('common.startTour', 'Start Tour')}
        >
          <QuestionIcon weight="bold" className="text-lg" />
        </button>
      </div>

      {statsError && (
        <div className="mb-6 bg-red-50 text-red-600 p-4 rounded-lg flex items-center gap-2">
          <WarningIcon size={20} /> {statsError?.message || String(statsError)}
        </div>
      )}

      {/* Stats Cards */}
      <div id="stat-cards" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Total Users */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 flex items-center gap-5">
          <div className="w-14 h-14 rounded-full bg-green-50 dark:bg-green-900/20 flex items-center justify-center text-green-600 dark:text-green-400 text-2xl flex-shrink-0">
            <CurrencyDollarIcon weight="fill" />
          </div>
          <div>
            <p className="text-gray-500 dark:text-gray-400 text-sm font-medium mb-1">{t('admin.dashboard.total_users')}</p>
            {loadingStats ? (
              <div className="h-8 w-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
            ) : (
              <h3 className="text-2xl font-bold text-gray-800 dark:text-white">{stats ? stats.total_users : 0}</h3>
            )}
          </div>
        </div>

        {/* Total Chats */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 flex items-center gap-5">
          <div className="w-14 h-14 rounded-full bg-yellow-50 dark:bg-yellow-900/20 flex items-center justify-center text-yellow-600 dark:text-yellow-400 text-2xl flex-shrink-0">
            <ChatCircleTextIcon weight="fill" />
          </div>
          <div>
            <p className="text-gray-500 dark:text-gray-400 text-sm font-medium mb-1">{t('admin.dashboard.total_chats')}</p>
            {loadingStats ? (
              <div className="h-8 w-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
            ) : (
              <h3 className="text-2xl font-bold text-gray-800 dark:text-white">{stats ? stats.total_chats : 0}</h3>
            )}
          </div>
        </div>

        {/* Total KBs/Documents */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 flex items-center gap-5">
          <div className="w-14 h-14 rounded-full bg-primary-50 dark:bg-primary-900/20 flex items-center justify-center text-primary-600 dark:text-primary-400 text-2xl flex-shrink-0">
            <UserPlusIcon weight="fill" />
          </div>
          <div>
            <p className="text-gray-500 dark:text-gray-400 text-sm font-medium mb-1">{t('admin.dashboard.total_kbs')}</p>
            {loadingStats ? (
              <div className="h-8 w-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
            ) : (
              <h3 className="text-2xl font-bold text-gray-800 dark:text-white">{stats ? stats.total_kbs : 0}</h3>
            )}
          </div>
        </div>

        {/* Total Documents */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 flex items-center gap-5">
          <div className="w-14 h-14 rounded-full bg-purple-50 dark:bg-purple-900/20 flex items-center justify-center text-purple-600 dark:text-purple-400 text-2xl flex-shrink-0">
            <FileTextIcon weight="fill" />
          </div>
          <div>
            <p className="text-gray-500 dark:text-gray-400 text-sm font-medium mb-1">{t('admin.dashboard.total_documents')}</p>
            {loadingStats ? (
              <div className="h-8 w-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
            ) : (
              <h3 className="text-2xl font-bold text-gray-800 dark:text-white">{stats ? stats.total_documents : 0}</h3>
            )}
          </div>
        </div>
      </div>

      {/* Content Grid: Charts & Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart Area (Left - 2/3 width) */}
        <div id="activity-chart" className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 relative">
          {loadingStream && realTimeChartData.length === 0 && (
            <div className="absolute inset-0 bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm flex items-center justify-center z-10 rounded-xl">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
            </div>
          )}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <h3 className="font-bold text-gray-800 dark:text-white">
                {t('admin.dashboard.activity_statistics')}
              </h3>
              {/* Dropdown Filter - Moved to Left */}
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="px-3 py-1 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-sm font-medium text-gray-700 dark:text-gray-300 focus:ring-2 focus:ring-primary-500 focus:outline-none"
              >
                <option value="7days">{t('admin.dashboard.last7Days')}</option>
                <option value="30days">{t('admin.dashboard.last30Days')}</option>
                <option value="all">{t('admin.dashboard.allTime')}</option>
              </select>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-primary-400"></span>
                  <span>{t('admin.dashboard.messages')}</span></span>
              </div>
            </div>
          </div>

          {/* Real Chart using react-chartjs-2 */}
          <div className="h-80 w-full">
            <Line data={chartData} options={chartOptions} />
          </div>
        </div>

        {/* Recent List (Right - 1/3 width) */}
        <div id="recent-activity" className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 flex flex-col relative">
          <h3 className="font-bold text-gray-800 dark:text-white mb-4">{t('admin.dashboard.recent_activity')}</h3>
          <div className="flex-1 overflow-auto -mx-2 px-2">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="text-xs text-gray-400 border-b border-gray-100 dark:border-gray-700">
                  <th className="py-3 font-medium">{t('admin.dashboard.th_doc_name')}</th>
                  <th className="py-3 font-medium text-right">{t('admin.dashboard.th_status')}</th>
                </tr>
              </thead>
              <tbody className="text-sm">
                {loadingStats ? (
                  [1, 2, 3, 4, 5].map((i) => (
                    <tr key={i} className="border-b border-gray-50 dark:border-gray-700 last:border-0">
                      <td className="py-3">
                        <div className="h-4 w-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
                      </td>
                      <td className="py-3 text-right">
                        <div className="h-6 w-16 ml-auto bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <>
                    {recentDocs.map((doc) => (
                      <tr
                        key={doc.id}
                        onClick={() => navigate('/admin/documents', { state: { kbId: doc.knowledgebase_id, kbName: doc.knowledgebases?.name, docId: doc.id } })}
                        className="border-b border-gray-50 dark:border-gray-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-700 transition cursor-pointer"
                      >
                        <td className="py-3 text-gray-500 dark:text-gray-400 font-mono" title={doc.name}>
                          {doc.name.length > 20 ? doc.name.substring(0, 20) + '...' : doc.name}
                        </td>
                        <td className="py-3 text-right">
                          <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${doc.status === 'completed' ? 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400' :
                            doc.status === 'processing' ? 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400' :
                              'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
                            }`}>
                            {t(`common.status.${doc.status}`, doc.status || 'Unknown')}
                          </span>
                        </td>
                      </tr>
                    ))}
                    {!loadingStats && recentDocs.length === 0 && (
                      <tr>
                        <td colSpan="2" className="py-4 text-center text-gray-500">{t('admin.dashboard.no_recent_docs')}</td>
                      </tr>
                    )}
                  </>
                )}
              </tbody>
            </table>
          </div>

          {/* Help Button */}

        </div>
      </div>
    </div>

  );
};

export default Dashboard;
