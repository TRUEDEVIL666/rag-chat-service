
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CurrencyDollarIcon, ChatCircleTextIcon, UserPlusIcon,
  FileTextIcon, WarningIcon, LightningIcon, PlusIcon,
  UsersIcon, UploadIcon, RobotIcon, TrendUpIcon,
  ThumbsUpIcon, ThumbsDownIcon, HeartbeatIcon, CheckCircleIcon
} from '@phosphor-icons/react';
import { useDashboard } from '../../hooks/useDashboard';
import { useTranslation } from 'react-i18next';
import { ROUTES } from '../../routes';
import Skeleton from '../../components/common/Skeleton';
import { useAuth } from '../../context/AuthContext';
import ReactWordcloud from '../../components/common/WordCloud';

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
  <div className="row-span-2 col-span-1 bg-white dark:bg-gray-800 rounded-3xl border border-gray-100 dark:border-gray-700 p-6 shadow-sm flex flex-col h-[500px] lg:h-auto">
    <div className="flex items-center justify-between mb-6">
      <h3 className="font-bold text-lg text-gray-800 dark:text-gray-100 flex items-center gap-2">
        <LightningIcon className="text-yellow-500" weight="fill" />
        {t('admin.dashboard.live_activity', 'Live Pulse')}
      </h3>
    </div>

    <div className="flex-1 overflow-y-auto custom-scrollbar -mr-2 pr-2 space-y-6">
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
          <div key={item.id} className="relative pl-6 border-l-2 border-gray-100 dark:border-gray-700 last:border-0 pb-2">
            <div className="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-white dark:bg-gray-800 border-2 border-primary-500"></div>
            <div className="mb-1 flex items-center gap-2">
              <span className="text-sm font-bold text-gray-900 dark:text-white">{item.user}</span>
              <span className="text-xs text-gray-500">{item.time}</span>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-300 line-clamp-2" title={item.type === 'query' ? item.message : ''}>
              {item.type === 'query' && (
                <>Asked <span className="text-primary-600 dark:text-primary-400 font-medium">{item.bot}</span>: "{item.message}"</>
              )}
              {item.type === 'enrollment' && (
                <>Joined <span className="text-green-600 dark:text-green-400 font-medium">{item.class}</span></>
              )}
              {item.type === 'upload' && (
                <>Uploaded <span className="text-purple-600 dark:text-purple-400 font-medium">{item.doc}</span> to {item.kb}</>
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

const EngagementWidget = ({ t, engagement, navigate }) => (
  <div className="col-span-1 lg:col-span-2 bg-white dark:bg-gray-800 rounded-3xl border border-gray-100 dark:border-gray-700 p-6 shadow-sm">
    <h3 className="font-bold text-gray-800 dark:text-gray-100 mb-6 flex items-center justify-between">
      <span className="flex items-center gap-2">
        <UsersIcon className="text-indigo-500" weight="fill" />
        {t('admin.dashboard.engagement.title', 'Engagement Pulse')}
      </span>
      <button
        onClick={() => navigate(ROUTES.ADMIN.CLASSES.LIST)}
        className="text-xs text-primary-600 font-bold hover:underline"
      >
        {t('admin.dashboard.view_all_classes', 'VIEW ALL CLASSES')}
      </button>
    </h3>

    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
      <div>
        <h4 className="text-xs font-bold uppercase text-gray-400 mb-3">{t('admin.dashboard.top_active_classes', 'Top Active Classes')}</h4>
        <div className="space-y-3">
          {engagement?.active_classes?.map((c, i) => (
            <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-gray-50 dark:bg-gray-900/50">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 flex items-center justify-center font-bold text-xs">{i + 1}</div>
                <div>
                  <p className="font-bold text-sm text-gray-800 dark:text-gray-200">{c.name}</p>
                  <p className="text-xs text-gray-500">{t('admin.dashboard.students_count', '{{count}} Students', { count: c.students })}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="font-bold text-primary-600">{c.queries}</p>
                <p className="text-[10px] text-gray-400 uppercase">{t('admin.dashboard.queries', 'Queries')}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h4 className="text-xs font-bold uppercase text-red-400 mb-3">{t('admin.dashboard.needs_attention', 'Needs Attention (At Risk)')}</h4>
        <div className="space-y-3">
          {engagement?.at_risk_students?.map((s, i) => (
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
          ))}
        </div>
      </div>
    </div>
  </div>
);

const FeedbackWidget = ({ t, feedback }) => (
  <div className="bg-white dark:bg-gray-800 rounded-3xl border border-gray-100 dark:border-gray-700 p-6 shadow-sm flex flex-col justify-center">
    <h3 className="font-bold text-gray-800 dark:text-gray-100 mb-4 text-center">{t('admin.dashboard.student_feedback', 'Student Feedback')}</h3>
    {feedback && (
      <div className="flex items-center justify-center gap-6">
        <div className="text-center">
          <div className="w-16 h-16 rounded-2xl bg-green-50 dark:bg-green-900/20 text-green-500 flex items-center justify-center text-3xl mb-2 mx-auto">
            <ThumbsUpIcon weight="fill" />
          </div>
          <p className="text-2xl font-bold text-gray-800 dark:text-white">{feedback.positive}%</p>
          <p className="text-xs text-gray-500">{t('admin.dashboard.positive', 'Positive')}</p>
        </div>
        <div className="h-12 w-px bg-gray-200 dark:bg-gray-700"></div>
        <div className="text-center">
          <div className="w-16 h-16 rounded-2xl bg-red-50 dark:bg-red-900/20 text-red-500 flex items-center justify-center text-3xl mb-2 mx-auto">
            <ThumbsDownIcon weight="fill" />
          </div>
          <p className="text-2xl font-bold text-gray-800 dark:text-white">{feedback.negative}%</p>
          <p className="text-xs text-gray-500">{t('admin.dashboard.negative', 'Negative')}</p>
        </div>
      </div>
    )}
  </div>
);

const Dashboard = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user } = useAuth();

  const {
    stats, activity, topics, engagement, feedback,
    loading, error, fetchDashboardData
  } = useDashboard();

  useEffect(() => {
    const controller = new AbortController();
    fetchDashboardData(true, controller.signal); // allow hook to handle signal

    // Auto-refresh every 30 seconds for "Live Pulse" feel
    const intervalId = setInterval(() => {
      // Create new controller for interval? Or reuse?
      // Intervals are tricky with cancellation. Usually we don't cancel interval fetches on unmount via controller,
      // closely, but we do clear interval.
      // For the initial fetch, we want to cancel if we navigate away quickly.
    }, 30000);

    return () => {
      controller.abort();
      clearInterval(intervalId);
    };
  }, [fetchDashboardData]);

  if (error) {
    return <div className="p-10 text-center text-red-500"><WarningIcon size={32} className="mx-auto mb-2" />{t('common.error_loading', 'Failed to load dashboard')}</div>;
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 lg:p-8 bg-gray-50/50 dark:bg-gray-900/50">

      {/* Bento Grid Layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto">

        {/* Row 1: Welcome & Quick Actions */}
        <WelcomeHeader t={t} user={user} stats={stats} />

        <div className="col-span-1 md:col-span-2 grid grid-cols-2 gap-4">
          <QuickActionTile
            title={t('admin.dashboard.new_bot', 'New Bot')}
            icon={RobotIcon}
            color="bg-indigo-500"
            onClick={() => navigate(ROUTES.ADMIN.BOTS.CREATE)}
          />
          <QuickActionTile
            title={t('admin.dashboard.new_class', 'New Class')}
            icon={UsersIcon}
            color="bg-emerald-500"
            onClick={() => navigate(ROUTES.ADMIN.CLASSES.LIST)}
          />
          <QuickActionTile
            title={t('admin.dashboard.upload_doc', 'Upload Doc')}
            icon={UploadIcon}
            color="bg-pink-500"
            onClick={() => navigate(ROUTES.ADMIN.DOCUMENTS.LIST)}
          />
          <QuickActionTile
            title={t('admin.dashboard.add_user', 'Add User')}
            icon={UserPlusIcon}
            color="bg-orange-500"
            onClick={() => navigate(ROUTES.ADMIN.USERS.LIST)}
          />
        </div>

        {/* Row 2: Stats & Feed */}
        <div className="col-span-1 md:col-span-2 lg:col-span-3 grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatCard
            title={t('admin.dashboard.total_users', 'Total Users')}
            value={stats?.total_users || 0}
            icon={UsersIcon}
            colorClass="bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400"
            loading={loading}
          />
          <StatCard
            title={t('admin.dashboard.total_chats', 'Total Chats')}
            value={stats?.total_chats || 0}
            icon={ChatCircleTextIcon}
            colorClass="bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400"
            loading={loading}
          />
          <StatCard
            title={t('admin.dashboard.total_kbs', 'Knowledge Bases')}
            value={stats?.total_kbs || 0}
            icon={FileTextIcon}
            colorClass="bg-yellow-50 text-yellow-600 dark:bg-yellow-900/20 dark:text-yellow-400"
            loading={loading}
          />

          {/* Charts Row inside this column block to stack properly */}
          <div className="col-span-1 md:col-span-3">
            <EngagementWidget t={t} engagement={engagement} navigate={navigate} />
          </div>
          <div className="col-span-1 md:col-span-3 grid grid-cols-1 md:grid-cols-2 gap-6">
            <TrendingWidget t={t} topics={topics} loading={loading} />
            <FeedbackWidget t={t} feedback={feedback} />
          </div>
        </div>

        <div className="row-span-1 col-span-1 md:col-span-1 lg:col-span-1">
          <ActivityFeed t={t} activity={activity} loading={loading} />
        </div>

      </div>
    </div>
  );
};

export default Dashboard;
