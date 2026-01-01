import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { clsx } from 'clsx';
import { RobotIcon, PlusCircleIcon, ChatCircleDotsIcon, PencilSimpleIcon, TrashIcon, SpinnerIcon, WarningIcon, BookBookmarkIcon } from '@phosphor-icons/react';
import { useAuth } from '../../../context/AuthContext';
import { useTranslation } from 'react-i18next';
import { useBots } from '../../../hooks/useBots';
import { usePageTour } from '../../../hooks/usePageTour';
import TourButton from '../../../components/common/TourButton';



const BotList = () => {
  const { t } = useTranslation(['bots', 'translation']);
  const { bots, loading: isLoading, error, fetchBots, deleteBot } = useBots();
  const { user } = useAuth();
  const navigate = useNavigate();


  const tourSteps = [
    {
      element: '#bot-list-header',
      popover: { title: t('tour.bots.title', 'Chatbots'), description: t('tour.bots.desc', 'Manage your AI chatbots here.') }
    },
    {
      element: '#create-bot-btn',
      popover: { title: t('tour.bots.create', 'Create Bot'), description: t('tour.bots.createDesc', 'Click here to create a new chatbot.') }
    },
    {
      element: '#bot-grid',
      popover: { title: t('tour.bots.list', 'Bot List'), description: t('tour.bots.listDesc', 'Your active bots appear here.') }
    },
    {
      element: '.tour-chat-btn',
      popover: { title: t('tour.bots.chat', 'Test Chat'), description: t('tour.bots.chatDesc', 'Click here to chat with your bot.') }
    }
  ];

  const { startTour } = usePageTour('bot-list', tourSteps);

  useEffect(() => {
    fetchBots();
  }, [fetchBots]);

  const handleDelete = async (id) => {
    if (!window.confirm(t('deleteConfirm'))) return;

    try {
      await deleteBot(id);
    } catch (err) {
      alert(t('common.deleteError'));
      console.error(err);
    }
  };

  if (isLoading) return <div className="flex justify-center py-10"><SpinnerIcon size={32} className="animate-spin text-primary-600" /></div>;

  return (
    <div className="flex flex-col h-full p-6 overflow-hidden">
      <div className="flex flex-col h-full bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">

        {/* Combined Header */}
        <div className="h-16 px-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between shrink-0 bg-gray-50/50 dark:bg-gray-900/20">
          <div className="flex items-center gap-3">
            <h1 id="bot-list-header" className="text-lg font-bold text-gray-900 dark:text-gray-100 uppercase tracking-wide">{t('title')}</h1>
            <TourButton startTour={startTour} />
          </div>
          <Link id="create-bot-btn" to="create" className="btn-primary flex items-center gap-2 px-4 py-2 rounded-lg shadow-sm hover:shadow text-sm font-medium">
            <PlusCircleIcon size={18} weight="bold" /> <span>{t('createNew')}</span>
          </Link>
        </div>

        {/* Table Content */}
        <div id="bot-grid" className="flex-1 overflow-auto relative">
          <table className="w-full text-left border-collapse">
            <thead className="bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10 backdrop-blur-sm">
              <tr className="text-xs uppercase text-gray-500 dark:text-gray-400 font-bold tracking-wider">
                <th className="px-6 py-4">{t('table.name')}</th>
                <th className="px-6 py-4">{t('table.model')}</th>
                <th className="px-6 py-4">{t('table.description')}</th>
                <th className="px-6 py-4">{t('table.status')}</th>
                <th className="px-6 py-4 text-center">{t('table.actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700 text-sm dark:text-gray-300">
              {error ? (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center text-red-500 bg-red-50 dark:bg-red-900/10">
                    <div className="flex flex-col items-center gap-2">
                      <WarningIcon size={32} />
                      <p className="font-medium">{t('common.errorOccurred')}</p>
                      <p className="text-sm text-red-600 dark:text-red-400">{error?.message || String(error)}</p>
                    </div>
                  </td>
                </tr>
              ) : bots.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center text-gray-500">{t('empty')}</td>
                </tr>
              ) : (
                bots.map((bot) => (
                  <tr key={bot.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition duration-150 group">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-100 to-primary-200 dark:from-primary-900/40 dark:to-primary-800/20 flex items-center justify-center text-primary-600 dark:text-primary-400 shadow-sm group-hover:scale-105 transition-transform">
                          <RobotIcon size={24} weight="duotone" />
                        </div>
                        <div>
                          <p className="font-bold text-gray-900 dark:text-gray-100">{bot.name}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-2.5 py-1 rounded-md text-[11px] font-bold border border-gray-200 dark:border-gray-600 shadow-sm">
                        {bot.model?.name || t('common.na')}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-500 dark:text-gray-400 max-w-xs truncate" title={bot.description}>
                      {bot.description || t('common.na')}
                    </td>
                    <td className="px-6 py-4">
                      <span className="flex items-center gap-2 text-green-600 dark:text-green-400 font-bold bg-green-50 dark:bg-green-900/20 px-3 py-1 rounded-full w-fit text-[11px] border border-green-100 dark:border-green-900/30">
                        <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span> {t('common.status.active')}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-center gap-1 opacity-100 lg:opacity-60 lg:group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => navigate(`/admin/chat/${bot.id}`)}
                          disabled={!bot.model_id}
                          className={clsx(
                            "tour-chat-btn transition p-2 rounded-lg",
                            bot.model_id
                              ? "text-gray-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20"
                              : "text-gray-300 cursor-not-allowed opacity-50"
                          )}
                          title={bot.model_id ? t('tooltip.chat') : t('noModel', 'No model configured')}
                        >
                          <ChatCircleDotsIcon size={20} weight="regular" />
                        </button>
                        <Link
                          to={`edit/${bot.id}`}
                          className="text-gray-400 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition inline-block p-2 rounded-lg"
                          title={t('tooltip.edit')}
                        >
                          <PencilSimpleIcon size={20} />
                        </Link>
                        <button
                          onClick={() => handleDelete(bot.id)}
                          className="text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition p-2 rounded-lg"
                          title={t('tooltip.delete')}
                        >
                          <TrashIcon size={20} />
                        </button>
                        <button
                          onClick={() => navigate(`/admin/bots/${bot.id}/kbs`)}
                          className="text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition p-2 rounded-lg"
                          title={t('tooltip.kb')}
                        >
                          <BookBookmarkIcon size={20} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>


    </div>
  );
};

export default BotList;
