import { useEffect, useState } from 'react';
import { Link, useNavigate, useOutletContext } from 'react-router-dom';
import { ROUTES } from '../../../routes';
import { clsx } from 'clsx';
import { RobotIcon, PlusCircleIcon, ChatCircleDotsIcon, PencilSimpleIcon, TrashIcon, SpinnerIcon, WarningIcon, BookBookmarkIcon, MagnifyingGlassIcon } from '@phosphor-icons/react';

import { useTranslation } from 'react-i18next';
import { useBots } from '../../../hooks/useBots';
import { usePageTour } from '../../../hooks/usePageTour';
import TourButton from '../../../components/common/TourButton';



const BotList = () => {
  const { t } = useTranslation();
  const { bots, loading: isLoading, error, fetchBots, deleteBot } = useBots();
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const { setTitle } = useOutletContext() || {};

  useEffect(() => {
    if (setTitle) setTitle(t('admin.bots.title', 'Chatbots'));
  }, [setTitle, t]);


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
    const controller = new AbortController();
    fetchBots({ signal: controller.signal });
    return () => controller.abort();
  }, [fetchBots]);

  const handleDelete = async (id) => {
    if (!window.confirm(t('admin.bots.deleteConfirm'))) return;

    try {
      await deleteBot(id);
    } catch (err) {
      alert(t('common.deleteError'));
      console.error(err);
    }
  };

  // Search Filter Logic
  const filteredBots = bots.filter(bot => {
    if (!searchTerm) return true;
    const lowerTerm = searchTerm.toLowerCase();
    return (
      bot.name?.toLowerCase().includes(lowerTerm) ||
      bot.description?.toLowerCase().includes(lowerTerm) ||
      bot.model?.name?.toLowerCase().includes(lowerTerm) ||
      (bot.config_model?.model && bot.config_model.model.toLowerCase().includes(lowerTerm))
    );
  });

  if (isLoading) return <div className="flex justify-center py-10"><SpinnerIcon size={32} className="animate-spin text-primary-600" /></div>;

  return (
    <div className="flex flex-col h-full p-6 overflow-hidden">
      <div className="flex flex-col h-full bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">

        {/* Combined Header */}
        <div className="h-16 px-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between shrink-0 bg-gray-50/50 dark:bg-gray-900/20">
          <div className="flex items-center gap-3">
            <TourButton startTour={startTour} />
          </div>

          <div className="flex items-center gap-3">
            {/* Search Input */}
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                <MagnifyingGlassIcon size={18} />
              </div>
              <input
                type="text"
                placeholder={t('admin.bots.searchPlaceholder', 'Search bots...')}
                className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-primary-500 focus:border-primary-500 w-64 transition-all"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            <Link id="create-bot-btn" to={ROUTES.ADMIN.BOTS.CREATE} className="btn-primary flex items-center gap-2 px-4 py-2 rounded-lg shadow-sm hover:shadow text-sm font-medium">
              <PlusCircleIcon size={18} weight="bold" /> <span>{t('admin.bots.createNew')}</span>
            </Link>
          </div>
        </div>

        {/* Table Content */}
        <div id="bot-grid" className="flex-1 overflow-auto relative">
          <table className="w-full text-left border-collapse">
            <thead className="bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10 backdrop-blur-sm">
              <tr className="text-xs uppercase text-gray-500 dark:text-gray-400 font-bold tracking-wider">
                <th className="px-6 py-4">{t('admin.bots.table.name')}</th>
                <th className="px-6 py-4">{t('admin.bots.table.model')}</th>
                <th className="px-6 py-4">{t('admin.bots.table.description')}</th>
                <th className="px-6 py-4">{t('admin.bots.table.status')}</th>
                <th className="px-6 py-4 text-center">{t('admin.bots.table.actions')}</th>
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
              ) : filteredBots.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center text-gray-500">
                    {searchTerm ? t('common.noResults', 'No bots found matching your search.') : t('empty')}
                  </td>
                </tr>
              ) : (
                filteredBots.map((bot) => (
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
                          onClick={() => navigate(ROUTES.ADMIN.CHAT.BOT(bot.id) + '?new=true')}
                          disabled={!bot.model_id}
                          className={clsx(
                            "tour-chat-btn transition p-2 rounded-lg",
                            bot.model_id
                              ? "text-gray-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20"
                              : "text-gray-300 cursor-not-allowed opacity-50"
                          )}
                          title={bot.model_id ? t('admin.bots.tooltip.chat') : t('admin.bots.noModel')}
                        >
                          <ChatCircleDotsIcon size={20} weight="regular" />
                        </button>
                        <Link
                          to={bot.id}
                          className="text-gray-400 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition inline-block p-2 rounded-lg"
                          title={t('admin.bots.tooltip.edit')}
                        >
                          <PencilSimpleIcon size={20} />
                        </Link>
                        <button
                          onClick={() => handleDelete(bot.id)}
                          className="text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition p-2 rounded-lg"
                          title={t('admin.bots.tooltip.delete')}
                        >
                          <TrashIcon size={20} />
                        </button>
                        <button
                          onClick={() => navigate(ROUTES.ADMIN.BOTS.KNOWLEDGE(bot.id))}
                          className="text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition p-2 rounded-lg"
                          title={t('admin.bots.tooltip.kb')}
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
