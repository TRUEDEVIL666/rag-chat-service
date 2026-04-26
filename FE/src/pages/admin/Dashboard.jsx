
import React, { useState, useEffect } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import {
  CurrencyDollarIcon, UserPlusIcon,
  FileTextIcon, WarningIcon, LightningIcon, PlusIcon,
  UsersIcon, UploadIcon, RobotIcon, TrendUpIcon,
  ThumbsUpIcon, ThumbsDownIcon, HeartbeatIcon, CheckCircleIcon,
  SquaresFourIcon, GraduationCapIcon, MonitorPlayIcon, BrainIcon,
  GearIcon, ChatCircleTextIcon as ChatIcon
} from '@phosphor-icons/react';
import { useDashboard } from '../../hooks/useDashboard';
import { useTranslation } from 'react-i18next';
import { ROUTES } from '../../routes';
import Skeleton from '../../components/common/Skeleton';
import { useAuth } from '../../context/AuthContext';
import ReactWordcloud from '../../components/common/WordCloud';
import clsx from 'clsx';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell, PieChart, Pie
} from 'recharts';

const WelcomeHeader = ({ t, user, stats }) => (
  <div className="col-span-1 md:col-span-2 lg:col-span-2 p-6 rounded-3xl bg-gradient-to-r from-primary-600 to-primary-800 text-white shadow-xl relative overflow-hidden">
    <div className="relative z-10">
      <h1 className="text-3xl font-bold mb-2">
        {t('admin.dashboard.welcome', 'Welcome back, {{name}}!', { name: user?.name || 'Admin' })}
      </h1>
      <p className="text-primary-100 mb-6 max-w-lg">
        {t('admin.dashboard.subtitle', 'Here is what’s happening in your digital classroom today.')}
      </p>
      <div className="flex gap-3">
        <div className="flex items-center gap-2 bg-white/20 backdrop-blur-md px-4 py-2 rounded-xl text-sm font-medium">
          <CheckCircleIcon size={18} weight="fill" className="text-green-300" />
          <span>{t('admin.dashboard.systems_operational', 'All Systems Operational')}</span>
        </div>
        <div className="flex items-center gap-2 bg-white/20 backdrop-blur-md px-4 py-2 rounded-xl text-sm font-medium">
          <UsersIcon size={18} weight="fill" className="text-blue-300" />
          <span>{t('admin.dashboard.active_learners', '{{count}} Active Learners', { count: stats?.total_users || 0 })}</span>
        </div>
      </div>
    </div>
    {/* Decorative Background */}
    <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/4 blur-3xl"></div>
    <div className="absolute bottom-0 right-20 w-40 h-40 bg-primary-400/20 rounded-full translate-y-1/2 blur-2xl"></div>
  </div>
);

const QuickActionTile = ({ title, icon: Icon, color, onClick }) => (
  <button
    onClick={onClick}
    className={`group p-4 rounded-2xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 shadow-sm hover:shadow-md transition-all flex flex-col items-center justify-center gap-3 h-full`}
  >
    <div className={`w-12 h-12 rounded-xl ${color} flex items-center justify-center text-white text-xl group-hover:scale-110 transition-transform`}>
      <Icon weight="bold" />
    </div>
    <span className="font-semibold text-gray-700 dark:text-gray-200 text-sm">{title}</span>
  </button>
);

const StatCard = ({ title, value, icon: Icon, colorClass, loading }) => (
  <div className="p-5 rounded-2xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 shadow-sm flex items-center gap-4">
    <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl ${colorClass}`}>
      <Icon weight="duotone" />
    </div>
    <div>
      <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">{title}</p>
      <h3 className="text-2xl font-bold text-gray-900 dark:text-white mt-0.5">
        {loading ? <Skeleton className="h-8 w-16" /> : value}
      </h3>
    </div>
  </div>
);

const ActivityFeed = ({ t, activity, loading }) => (
  <div className="bg-white dark:bg-gray-800 rounded-[2rem] border border-gray-100 dark:border-gray-700 p-8 shadow-sm flex flex-col h-[500px]">
    <div className="flex items-center justify-between mb-8">
      <h3 className="font-bold text-lg text-gray-900 dark:text-gray-100 flex items-center gap-3">
        <div className="p-2 bg-indigo-500 rounded-xl text-white shadow-md shadow-indigo-100 dark:shadow-none">
          <LightningIcon className="text-white" weight="fill" size={20} />
        </div>
        {t('admin.dashboard.live_activity', 'System Activity')}
      </h3>
    </div>

    <div className="flex-1 overflow-y-auto custom-scrollbar -mr-4 pr-4 space-y-6">
      {loading ? (
        [...Array(5)].map((_, i) => (
          <div key={i} className="flex gap-4">
            <Skeleton className="w-10 h-10 rounded-full flex-shrink-0" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
            </div>
          </div>
        ))
      ) : activity && activity.length > 0 ? (
        activity.map(item => (
          <div key={item.id} className="relative pl-6 border-l-2 border-slate-100 dark:border-gray-700 last:border-0 pb-6">
            <div className="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-white dark:bg-gray-800 border-2 border-indigo-500 shadow-sm"></div>
            <div className="mb-1 flex items-center justify-between">
              <span className="text-sm font-bold text-gray-900 dark:text-white">{item.time}</span>
              <span className="text-[10px] font-bold text-indigo-500 uppercase tracking-widest">{item.type}</span>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
              {item.type === 'query' && (
                <><span className="font-bold text-gray-900 dark:text-white">{item.user}</span> asked <span className="text-indigo-600 dark:text-indigo-400 font-bold">{item.bot}</span></>
              )}
              {item.type === 'enrollment' && (
                <><span className="font-bold text-gray-900 dark:text-white">{item.user}</span> joined <span className="text-emerald-600 dark:text-emerald-400 font-bold">{item.class}</span></>
              )}
              {item.type === 'upload' && (
                <><span className="font-bold text-gray-900 dark:text-white">{item.user}</span> synced Knowledge Base</>
              )}
            </p>
          </div>
        ))
      ) : (
        <div className="text-center text-gray-400 py-10 mt-10">
          <HeartbeatIcon size={48} className="mx-auto mb-2 opacity-20" />
          <p>No recent signals</p>
        </div>
      )}
    </div>
  </div>
);

const TrendingWidget = ({ t, topics, loading }) => (
  <div className="bg-white dark:bg-gray-800 rounded-3xl border border-gray-100 dark:border-gray-700 p-6 shadow-sm h-[300px] flex flex-col">
    <h3 className="font-bold text-gray-800 dark:text-gray-100 mb-4 flex items-center gap-2">
      <TrendUpIcon className="text-red-500" weight="fill" />
      {t('admin.dashboard.trending_topics', 'Trending Topics')}
    </h3>
    <div className="flex-1 w-full h-full relative flex items-center justify-center">
      {loading ? (
        <Skeleton className="h-full w-full rounded-xl" />
      ) : topics?.length > 0 ? (
        <ReactWordcloud
          words={topics}
          width={400}
          height={200}
        />
      ) : (
        <p className="text-sm text-gray-400 italic w-full text-center py-10">No trending topics yet.</p>
      )}
    </div>
  </div>
);

const EngagementWidget = ({ t, engagement, navigate, loading }) => {
  return (
    <div className="col-span-1 lg:col-span-2 bg-white dark:bg-gray-800 rounded-3xl border border-gray-100 dark:border-gray-700 p-6 shadow-sm">
      <h3 className="font-bold text-gray-800 dark:text-gray-100 mb-6 flex items-center justify-between">
        <span className="flex items-center gap-2">
          <UsersIcon className="text-indigo-500" weight="fill" />
          {t('admin.dashboard.engagement.title', 'Engagement Pulse')}
        </span>
        <button
          onClick={() => navigate(ROUTES.ADMIN.USERS.LIST)}
          className="text-xs text-primary-600 font-bold hover:underline"
        >
          {t('admin.dashboard.view_all_users', 'VIEW ALL USERS')}
        </button>
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <h4 className="text-xs font-bold uppercase text-gray-400 mb-3">{t('admin.dashboard.most_engaging_users', 'Most Engaging Users')}</h4>
          <div className="space-y-3">
            {loading ? (
              [...Array(3)].map((_, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-gray-50 dark:bg-gray-900/50">
                  <div className="flex items-center gap-3 w-full">
                    <Skeleton className="w-8 h-8 rounded-lg" />
                    <div className="space-y-1 w-full">
                      <Skeleton className="h-4 w-1/2" />
                      <Skeleton className="h-3 w-1/4" />
                    </div>
                  </div>
                </div>
              ))
            ) : engagement?.top_users?.length > 0 ? (
              engagement.top_users.map((u, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-gray-50 dark:bg-gray-900/50">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 flex items-center justify-center font-bold text-xs">{i + 1}</div>
                    <div className="relative">
                      {u.avatar ? (
                        <img src={u.avatar} alt={u.name} className="w-8 h-8 rounded-full object-cover absolute -left-10 opacity-0" /> // Placeholder logic for avatar if we want to show it
                      ) : null}
                      {/* For now keeping list style consistent with previous, maybe add avatar later if UI supports it well in this list item */}
                      <div>
                        <p className="font-bold text-sm text-gray-800 dark:text-gray-200 line-clamp-1">{u.name}</p>
                        <p className="text-xs text-gray-500 line-clamp-1">{u.email}</p>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-primary-600">{u.queries}</p>
                    <p className="text-[10px] text-gray-400 uppercase">{t('admin.dashboard.queries', 'Queries')}</p>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-400 italic">No user activity data.</p>
            )}
          </div>
        </div>

        <div>
          <h4 className="text-xs font-bold uppercase text-red-400 mb-3">{t('admin.dashboard.needs_attention', 'Needs Attention (At Risk)')}</h4>
          <div className="space-y-3">
            {loading ? (
              [...Array(3)].map((_, i) => (
                <div key={i} className="flex items-center gap-3 p-3 rounded-xl border border-red-50 dark:border-red-900/20 bg-red-50/50 dark:bg-red-900/10">
                  <Skeleton className="w-2 h-2 rounded-full" />
                  <div className="flex-1 space-y-1">
                    <Skeleton className="h-4 w-1/2" />
                    <Skeleton className="h-3 w-1/3" />
                  </div>
                </div>
              ))
            ) : engagement?.at_risk_students?.length > 0 ? (
              engagement.at_risk_students.map((s, i) => (
                <div key={i} className="flex items-center gap-3 p-3 rounded-xl border border-red-50 dark:border-red-900/20 bg-red-50/50 dark:bg-red-900/10">
                  <div className="w-2 h-2 rounded-full bg-red-500"></div>
                  <div className="flex-1">
                    <p className="font-medium text-sm text-gray-800 dark:text-gray-200">{s.name}</p>
                    <p className="text-xs text-red-500">{t('admin.dashboard.inactive_for', 'Inactive for {{time}}', { time: s.last_active })}</p>
                  </div>
                  <button className="px-3 py-1 bg-white dark:bg-gray-800 shadow-sm text-xs font-bold text-gray-600 rounded-lg hover:bg-gray-50">
                    {t('admin.dashboard.ping', 'Ping')}
                  </button>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-400 italic">No at-risk students.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const FeedbackWidget = ({ t, feedback, loading }) => (
  <div className="bg-white dark:bg-gray-800 rounded-3xl border border-gray-100 dark:border-gray-700 p-6 shadow-sm flex flex-col justify-center min-h-[200px]">
    <h3 className="font-bold text-gray-800 dark:text-gray-100 mb-6 text-center text-xl">{t('admin.dashboard.student_feedback', 'Student Feedback')}</h3>
    {loading ? (
      <div className="flex items-center justify-center gap-8">
        <div className="text-center">
          <Skeleton className="w-20 h-20 rounded-2xl mx-auto mb-3" />
          <Skeleton className="h-10 w-16 mx-auto" />
        </div>
        <div className="h-16 w-px bg-gray-200 dark:bg-gray-700"></div>
        <div className="text-center">
          <Skeleton className="w-20 h-20 rounded-2xl mx-auto mb-3" />
          <Skeleton className="h-10 w-16 mx-auto" />
        </div>
      </div>
    ) : feedback ? (() => {
      const total = feedback.total || 0;
      const posPct = total > 0 ? Math.round((feedback.positive / total) * 100) : 0;
      const negPct = total > 0 ? Math.round((feedback.negative / total) * 100) : 0;

      return (
        <div className="flex items-center justify-center gap-8">
          <div className="text-center">
            <div className="w-20 h-20 rounded-2xl bg-green-50 dark:bg-green-900/20 text-green-500 flex items-center justify-center text-4xl mb-3 mx-auto transition-transform hover:scale-110">
              <ThumbsUpIcon weight="fill" />
            </div>
            <p className="text-4xl font-bold text-gray-800 dark:text-white mb-1">{posPct}%</p>
            <p className="text-sm font-medium text-gray-500">{t('admin.dashboard.positive', 'Positive')}</p>
          </div>
          <div className="h-16 w-px bg-gray-200 dark:bg-gray-700"></div>
          <div className="text-center">
            <div className="w-20 h-20 rounded-2xl bg-red-50 dark:bg-red-900/20 text-red-500 flex items-center justify-center text-4xl mb-3 mx-auto transition-transform hover:scale-110">
              <ThumbsDownIcon weight="fill" />
            </div>
            <p className="text-4xl font-bold text-gray-800 dark:text-white mb-1">{negPct}%</p>
            <p className="text-sm font-medium text-gray-500">{t('admin.dashboard.negative', 'Negative')}</p>
          </div>
        </div>
      );
    })() : null}
  </div>
);

const Dashboard = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [timeRange, setTimeRange] = useState('7days');

  const {
    stats, activity, topics, engagement, feedback, chartData,
    loadingStats, loadingActivity, loadingTopics, loadingEngagement, loadingFeedback, loadingChart,
    error, fetchDashboardData
  } = useDashboard();

  useEffect(() => {
    const controller = new AbortController();
    fetchDashboardData(true, controller.signal, timeRange);

    const intervalId = setInterval(() => {
      fetchDashboardData(false, undefined, timeRange);
    }, 60000);

    return () => {
      controller.abort();
      clearInterval(intervalId);
    };
  }, [fetchDashboardData, timeRange]);

  // Handle range change
  const handleRangeChange = (range) => {
    setTimeRange(range);
  };

  if (error) {
    return <div className="p-10 text-center text-red-500"><WarningIcon size={32} className="mx-auto mb-2" />{t('common.error_loading', 'Failed to load dashboard')}</div>;
  }

  // No fallback data
  const displayChartData = chartData || [];

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in duration-700">
      <WelcomeHeader t={t} user={user} stats={stats} />

      {/* 4 Stat Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title={t('admin.dashboard.total_students', 'Total Students')}
          value={stats?.total_users || 0}
          icon={UsersIcon}
          colorClass="bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400"
          loading={loadingStats}
        />
        <StatCard
          title={t('admin.dashboard.total_queries', 'Total Queries')}
          value={stats?.total_chats || 0}
          icon={ChatIcon}
          colorClass="bg-indigo-50 text-indigo-600 dark:bg-indigo-900/20 dark:text-indigo-400"
          loading={loadingStats}
        />
        <StatCard
          title={t('admin.dashboard.ai_resolved', 'AI Resolved')}
          value={stats?.ai_resolved_percent || '0%'}
          icon={RobotIcon}
          colorClass="bg-emerald-50 text-emerald-600 dark:bg-emerald-900/20 dark:text-emerald-400"
          loading={loadingStats}
        />
        <StatCard
          title={t('admin.dashboard.avg_response', 'Avg Response')}
          value={stats?.avg_response_time || '0s'}
          icon={LightningIcon}
          colorClass="bg-orange-50 text-orange-600 dark:bg-orange-900/20 dark:text-orange-400"
          loading={loadingStats}
        />
      </div>

      {/* Main Grid: Graph + Sidebar widgets */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        {/* Large Chart Container */}
        <div className="lg:col-span-2 space-y-8">
          <div className="bg-white dark:bg-gray-800 rounded-[2rem] border border-gray-100 dark:border-gray-700 p-8 shadow-sm">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">Chatbot Usage Over Time</h3>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-2xl font-black text-gray-900 dark:text-white">{stats?.total_chats || 0}</span>
                  {engagement?.trend !== undefined && engagement?.trend !== null && (
                    <span className={clsx(
                      "text-xs font-bold px-2 py-0.5 rounded-full",
                      engagement.trend >= 0 ? "text-emerald-500 bg-emerald-50" : "text-red-500 bg-red-50"
                    )}>
                      {engagement.trend > 0 ? '+' : ''}{engagement.trend}% this month
                    </span>
                  )}
                </div>
              </div>
              <div className="flex bg-gray-50 dark:bg-gray-900 p-1 rounded-xl">
                <button
                  className={clsx("px-4 py-1.5 text-xs font-bold transition-all", timeRange === '24h' ? "text-primary-600 bg-white dark:bg-gray-800 rounded-lg shadow-sm" : "text-gray-500 hover:text-gray-900")}
                  onClick={() => handleRangeChange('24h')}
                >
                  Daily
                </button>
                <button
                  className={clsx("px-4 py-1.5 text-xs font-bold transition-all", timeRange === '7days' ? "text-primary-600 bg-white dark:bg-gray-800 rounded-lg shadow-sm" : "text-gray-500 hover:text-gray-900")}
                  onClick={() => handleRangeChange('7days')}
                >
                  Weekly
                </button>
                <button
                  className={clsx("px-4 py-1.5 text-xs font-bold transition-all", timeRange === '30days' ? "text-primary-600 bg-white dark:bg-gray-800 rounded-lg shadow-sm" : "text-gray-500 hover:text-gray-900")}
                  onClick={() => handleRangeChange('30days')}
                >
                  Monthly
                </button>
              </div>
            </div>

            {/* Chart Area */}
            <div className="h-[340px] w-full relative">
              <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                <AreaChart
                  data={displayChartData}
                  margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                  style={{ opacity: loadingChart ? 0 : 1, transition: 'opacity 0.3s' }}
                >
                  <defs>
                    <linearGradient id="usageGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                  <XAxis
                    dataKey="period"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#9CA3AF', fontSize: 10, fontWeight: 700 }}
                    dy={10}
                    // For backend dates, we might want to format them
                    tickFormatter={(val) => {
                      if (val.includes('-')) {
                        try {
                          const date = new Date(val);
                          return date.toLocaleDateString(undefined, { weekday: 'short' });
                        } catch (e) { return val; }
                      }
                      return val;
                    }}
                  />
                  <YAxis
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#9CA3AF', fontSize: 10, fontWeight: 700 }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#FFF',
                      borderRadius: '12px',
                      border: 'none',
                      boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
                      padding: '12px'
                    }}
                    itemStyle={{ color: '#3B82F6', fontWeight: 700 }}
                    labelStyle={{ marginBottom: '4px', fontWeight: 700, color: '#111827' }}
                  />
                  <Area
                    type="monotone"
                    dataKey="count"
                    stroke="#3B82F6"
                    strokeWidth={4}
                    fillOpacity={1}
                    fill="url(#usageGradient)"
                    animationDuration={1500}
                  />
                </AreaChart>
              </ResponsiveContainer>

              {loadingChart && (
                <div className="absolute inset-0 flex items-center justify-center bg-white/50 dark:bg-gray-800/10 backdrop-blur-[1px] transition-all rounded-3xl z-10">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
                </div>
              )}
            </div>
          </div>

          {/* Bottom Grid: 3 Sub-cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Topic Distribution */}
            <div className="bg-white dark:bg-gray-800 rounded-3xl border border-gray-100 dark:border-gray-700 p-6 flex flex-col items-center">
              <h4 className="text-sm font-bold text-gray-900 dark:text-white mb-6 w-full text-center">Topic Distribution</h4>
              <div className="relative w-32 h-32 mb-6">
                <svg className="w-full h-full" viewBox="0 0 36 36">
                  <path className="text-gray-100 dark:text-gray-700" strokeDasharray="100, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="4" />
                  <path className="text-blue-500" strokeDasharray={`${topics?.[0]?.percent || 0}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-2xl font-black text-gray-900 dark:text-white">{topics?.[0]?.percent || 0}%</span>
                  <span className="text-[8px] font-bold text-gray-400 uppercase tracking-tighter">{topics?.[0]?.name || ''}</span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 w-full text-[10px] font-medium text-gray-500">
                {topics?.length > 0 ? (
                  topics.slice(0, 4).map((topic, i) => (
                    <div key={i} className="flex items-center gap-1.5 truncate">
                      <div className={clsx(
                        "w-2 h-2 rounded-full",
                        i === 0 ? "bg-blue-500" : i === 1 ? "bg-indigo-400" : i === 2 ? "bg-slate-300" : "bg-slate-200"
                      )}></div>
                      {topic.name} ({topic.percent}%)
                    </div>
                  ))
                ) : (
                  <>
                    <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-blue-500"></div> Math (45%)</div>
                    <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-indigo-400"></div> Science (20%)</div>
                    <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-slate-300"></div> English (15%)</div>
                    <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-slate-200"></div> Other (20%)</div>
                  </>
                )}
              </div>
            </div>

            {/* Usage by Grade */}
            <div className="bg-white dark:bg-gray-800 rounded-3xl border border-gray-100 dark:border-gray-700 p-6 flex flex-col items-center">
              <h4 className="text-sm font-bold text-gray-900 dark:text-white mb-6 w-full text-center">Usage by Grade</h4>
              <div className="w-full h-32 flex items-end justify-between gap-2 px-2">
                {(engagement?.byGrade || [30, 80, 50, 40]).map((h, i) => (
                  <div key={i} className="flex flex-col items-center gap-2 w-full">
                    <div className={clsx("w-full rounded-md transition-all", i === 1 ? "bg-blue-500" : "bg-slate-100 dark:bg-gray-700")} style={{ height: `${h}%` }}></div>
                    <span className="text-[10px] font-bold text-gray-400 uppercase">{9 + i}th</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Activity Heatmap */}
            <div className="bg-white dark:bg-gray-800 rounded-3xl border border-gray-100 dark:border-gray-700 p-6 flex flex-col items-center">
              <h4 className="text-sm font-bold text-gray-900 dark:text-white mb-6 w-full text-center">Activity Heatmap</h4>
              <div className="grid grid-cols-6 grid-rows-4 gap-1 w-full flex-1">
                {(engagement?.heatmap || [...Array(24)].map(() => Math.floor(Math.random() * 6))).map((intensity, i) => {
                  return (
                    <div
                      key={i}
                      className={clsx(
                        "rounded-[2px] w-full h-full min-h-[14px]",
                        intensity === 0 ? "bg-slate-50 dark:bg-gray-900" :
                          intensity === 1 ? "bg-blue-50" :
                            intensity === 2 ? "bg-blue-100" :
                              intensity === 3 ? "bg-blue-300" :
                                intensity === 4 ? "bg-blue-500" :
                                  "bg-blue-700"
                      )}
                    ></div>
                  );
                })}
              </div>
              <div className="flex justify-between w-full mt-4">
                <span className="text-[8px] font-bold text-gray-400 uppercase">8am</span>
                <span className="text-[8px] font-bold text-gray-400 uppercase">12pm</span>
                <span className="text-[8px] font-bold text-gray-400 uppercase">4pm</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Sidebar Widgets */}
        <div className="space-y-6">
          <ActivityFeed t={t} activity={activity} loading={loadingActivity} />

          <div className="bg-blue-50/50 dark:bg-primary-900/10 rounded-[2rem] p-8 border border-blue-100/50 dark:border-primary-800/20 shadow-sm transition-all hover:bg-white dark:hover:bg-gray-800 group">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-blue-500 rounded-xl text-white shadow-md shadow-blue-200 dark:shadow-none">
                <LightningIcon weight="fill" size={20} />
              </div>
              <h3 className="text-lg font-bold text-blue-900 dark:text-blue-100">AI Insights</h3>
            </div>

            <ul className="space-y-4">
              {[
                "High engagement in Math topics today.",
                "15% increase in queries about Science Project."
              ].map((insight, i) => (
                <li key={i} className="flex gap-3 text-sm font-medium text-blue-800/80 dark:text-blue-200/80">
                  <div className="mt-1.5 w-1.5 h-1.5 rounded-full bg-blue-400 flex-shrink-0" />
                  {insight}
                </li>
              ))}
            </ul>

            <button className="mt-8 w-full py-3 rounded-2xl bg-white dark:bg-gray-900 text-blue-600 dark:text-primary-400 font-bold text-xs uppercase tracking-widest shadow-sm hover:shadow-md transition-all group-hover:bg-blue-600 group-hover:text-white transition-all">
              View Full Analysis
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
