import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { RobotIcon, MagnifyingGlassIcon, X } from '@phosphor-icons/react';
import { toast } from 'react-hot-toast';
import { botService } from '../../../../services/botService';
import courseService from '../../../../services/courseService';
import Skeleton from '../../../../components/common/Skeleton';
import clsx from 'clsx';

const AddBotsModal = ({ isOpen, onClose, onSuccess, classId, assignedBots = [] }) => {
  const { t } = useTranslation();
  const [availableBots, setAvailableBots] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedBotIds, setSelectedBotIds] = useState([]);
  const [previewBot, setPreviewBot] = useState(null);

  useEffect(() => {
    if (isOpen) {
      loadAvailableBots();
      setSearch('');
      setSelectedBotIds([]);
      setPreviewBot(null);
    }
  }, [isOpen]);

  const loadAvailableBots = async () => {
    setLoading(true);
    try {
      const allBots = await botService.getBots();
      const assignedIds = assignedBots.map(b => b.id);
      const available = (allBots || []).filter(b => !assignedIds.includes(b.id));
      setAvailableBots(available);
    } catch (error) {
      console.error("Error loading bots", error);
      toast.error(t('courses.class.load_bots_error', 'Failed to load bots'));
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    try {
      await courseService.addBotsToClass(classId, selectedBotIds);
      toast.success(t('courses.class.bots_added', 'Bots added successfully'));
      onSuccess();
      onClose();
    } catch (error) {
      console.error(error);
      toast.error(t('courses.class.add_bots_error', 'Failed to add bots'));
    }
  };

  const toggleSelection = (botId) => {
    setSelectedBotIds(prev =>
      prev.includes(botId)
        ? prev.filter(id => id !== botId)
        : [...prev, botId]
    );
  };

  const filteredBots = availableBots.filter(bot =>
    bot.name?.toLowerCase().includes(search.toLowerCase()) ||
    bot.description?.toLowerCase().includes(search.toLowerCase())
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4 backdrop-blur-sm md:pl-64">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-5xl w-full max-h-[85vh] flex flex-col overflow-hidden border border-gray-200 dark:border-gray-700">
        {/* Modal Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50">
          <div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <RobotIcon className="text-primary-500" size={24} weight="fill" />
              {t('courses.class.add_bots', 'Add Bots to Class')}
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {t('courses.class.add_bots_desc', 'Select bots to assign to this class for student interaction.')}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-all"
          >
            <X size={20} weight="bold" />
          </button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Left Column: List */}
          <div className="w-1/2 border-r border-gray-100 dark:border-gray-700 flex flex-col bg-white dark:bg-gray-800">
            {/* Search Bar */}
            <div className="p-4 border-b border-gray-50 dark:border-gray-700/50">
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="text"
                  placeholder={t('courses.class.search_bots', 'Search by name or description...')}
                  className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-all text-sm"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
              {loading ? (
                <div className="space-y-3">
                  {[...Array(5)].map((_, i) => (
                    <Skeleton key={i} className="h-20 w-full rounded-xl" />
                  ))}
                </div>
              ) : filteredBots.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-gray-500 h-full">
                  <RobotIcon size={48} className="opacity-20 mb-3" />
                  <p>{t('courses.class.no_bots_found', 'No bots matches your search')}</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredBots.map((bot) => (
                    <div
                      key={bot.id}
                      className={clsx(
                        "group flex items-center gap-4 p-4 rounded-xl border transition-all cursor-pointer",
                        previewBot?.id === bot.id
                          ? "bg-primary-50/50 dark:bg-primary-900/10 border-primary-200 dark:border-primary-800"
                          : "bg-white dark:bg-gray-800 border-gray-100 dark:border-gray-700 hover:border-primary-200 dark:hover:border-primary-800 hover:bg-gray-50 dark:hover:bg-gray-800/50"
                      )}
                      onMouseEnter={() => setPreviewBot(bot)}
                      onClick={() => setPreviewBot(bot)}
                    >
                      <div className="relative flex items-center justify-center">
                        <input
                          type="checkbox"
                          checked={selectedBotIds.includes(bot.id)}
                          onChange={() => toggleSelection(bot.id)}
                          className="w-5 h-5 text-primary-600 border-gray-300 rounded-md focus:ring-primary-500 cursor-pointer"
                          onClick={(e) => e.stopPropagation()}
                        />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-gray-900 dark:text-white truncate">{bot.name}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-1">{bot.description || t('courses.class.no_desc', 'No description provided')}</p>
                      </div>
                      <div className="text-xs font-medium text-gray-400 dark:text-gray-500 whitespace-nowrap">
                        {bot.model?.name || bot.model_name || 'GPT-4o'}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Preview */}
          <div className="w-1/2 flex flex-col bg-gray-50/30 dark:bg-gray-900/10">
            <div className="p-6 h-full overflow-y-auto">
              {previewBot ? (
                <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-16 h-16 rounded-2xl bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-primary-600">
                        <RobotIcon size={32} weight="duotone" />
                      </div>
                      <div className="flex-1">
                        <h4 className="text-xl font-bold text-gray-900 dark:text-white">{previewBot.name}</h4>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800 dark:bg-primary-900/40 dark:text-primary-300">
                          {previewBot.provider?.name || 'OpenAI'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-1">
                    <p className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500">{t('courses.class.description', 'Description')}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed italic">
                      "{previewBot.description || t('courses.class.no_desc', 'No description')}"
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 rounded-xl bg-white dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700">
                      <p className="text-xs font-medium text-gray-400 dark:text-gray-500 mb-1">{t('courses.class.model', 'AI Model')}</p>
                      <p className="text-sm font-semibold text-gray-900 dark:text-white truncate"> {previewBot.model?.name || previewBot.model_name || 'GPT-4o'}</p>
                    </div>
                    <div className="p-3 rounded-xl bg-white dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700">
                      <p className="text-xs font-medium text-gray-400 dark:text-gray-500 mb-1">{t('courses.class.temp', 'Temperature')}</p>
                      <p className="text-sm font-semibold text-gray-900 dark:text-white truncate"> {previewBot.config_model?.temperature ?? 0.7}</p>
                    </div>
                    <div className="p-3 rounded-xl bg-white dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700">
                      <p className="text-xs font-medium text-gray-400 dark:text-gray-500 mb-1">{t('courses.class.top_k', 'Top K')}</p>
                      <p className="text-sm font-semibold text-gray-900 dark:text-white truncate"> {previewBot.config_model?.top_k ?? 10}</p>
                    </div>
                    <div className="p-3 rounded-xl bg-white dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700">
                      <p className="text-xs font-medium text-gray-400 dark:text-gray-500 mb-1">{t('courses.class.score', 'Score Threshold')}</p>
                      <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                        {previewBot.config_model?.score_threshold_enabled ? (previewBot.config_model?.score_threshold ?? 0.4) : 'Disabled'}
                      </p>
                    </div>
                    <div className="col-span-2 p-3 rounded-xl bg-white dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700">
                      <p className="text-xs font-medium text-gray-400 dark:text-gray-500 mb-1">{t('courses.class.rerank', 'Reranking')}</p>
                      <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                        {previewBot.config_model?.reranking_enable ? (previewBot.config_model?.reranking_model || 'Enabled') : 'Disabled'}
                      </p>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <p className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500">{t('courses.class.kb', 'Knowledge Bases')}</p>
                    <div className="flex flex-wrap gap-2">
                      {previewBot.knowledge_bases?.length > 0 ? (
                        previewBot.knowledge_bases.map((kb) => (
                          <span key={kb.id} className="px-3 py-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-300 text-xs font-medium border border-indigo-100 dark:border-indigo-800" title={kb.id}>
                            {kb.name}
                          </span>
                        ))
                      ) : previewBot.kb_ids?.length > 0 ? (
                        previewBot.kb_ids.map((id, idx) => (
                          <span key={idx} className="px-3 py-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-300 text-xs font-medium border border-indigo-100 dark:border-indigo-800">
                            KB-{id.substring(0, 8)}
                          </span>
                        ))
                      ) : (
                        <p className="text-sm text-gray-400 dark:text-gray-600">{t('courses.class.no_kb', 'No knowledge base linked.')}</p>
                      )}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <p className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500">{t('courses.class.instructions', 'Instructions')}</p>
                    <div className="p-4 rounded-xl bg-gray-900 dark:bg-black/40 text-gray-300 text-xs font-mono leading-relaxed max-h-48 overflow-y-auto custom-scrollbar">
                      {previewBot.config_prompt || t('courses.class.no_prompt', 'Default behavior set.')}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center p-10 space-y-4">
                  <div className="w-20 h-20 rounded-3xl bg-gray-50 dark:bg-gray-800/50 flex items-center justify-center text-gray-200 dark:text-gray-700">
                    <RobotIcon size={48} weight="duotone" />
                  </div>
                  <div>
                    <p className="text-gray-900 dark:text-white font-semibold">{t('courses.class.select_to_preview', 'Select a bot to preview')}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{t('courses.class.select_to_preview_desc', 'Hover over a bot in the list to see its full configuration and settings.')}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="flex justify-between items-center p-6 border-t border-gray-100 dark:border-gray-700 bg-gray-50/30 dark:bg-gray-800/50">
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {selectedBotIds.length} {t('courses.class.bots_selected', 'bots selected')}
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-5 py-2.5 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-xl font-semibold transition-all"
            >
              {t('common.cancel', 'Cancel')}
            </button>
            <button
              onClick={handleAdd}
              disabled={selectedBotIds.length === 0}
              className="px-6 py-2.5 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-200 dark:disabled:bg-gray-700/50 disabled:text-gray-400 disabled:cursor-not-allowed text-white rounded-xl font-bold transition-all shadow-lg shadow-primary-500/20 active:scale-[0.98]"
            >
              {t('common.add', 'Add Selections')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AddBotsModal;
