import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  MagnifyingGlassIcon,
  FloppyDiskIcon,
  ArrowLeftIcon,
  SpinnerIcon,
  CheckCircleIcon
} from '@phosphor-icons/react';
import { kbsService } from '../../../services/kbsService';
import { botService } from '../../../services/botService';
import api from '../../../services/api'; // Corrected default import

const BotKBConfigPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const [bot, setBot] = useState(null);
  const [kbs, setKbs] = useState([]);
  const [selectedKbIds, setSelectedKbIds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('updated_at'); // 'name', 'created_at', 'updated_at'
  const [sortOrder, setSortOrder] = useState('desc'); // 'asc', 'desc'

  useEffect(() => {
    let active = true;

    const loadData = async () => {
      setLoading(true);
      try {
        const [botData, kbsData] = await Promise.all([
          botService.getBot(id),
          kbsService.getKnowledgeBases()
        ]);

        if (active) {
          setBot(botData);
          setKbs(kbsData.data || kbsData || []);
          // Initial load of selected IDs
          setSelectedKbIds(botData.kb_ids || []);
        }
      } catch (error) {
        console.error("Failed to load data", error);
        // toast.error(t('common.errorOccurred'));
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    loadData();

    return () => {
      active = false;
    };
  }, [id]);

  const handleToggleKb = (kbId) => {
    setSelectedKbIds(prev => {
      if (prev.includes(kbId)) {
        return prev.filter(id => id !== kbId);
      } else {
        return [...prev, kbId];
      }
    });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await botService.updateBot(id, { kb_ids: selectedKbIds });
      // toast.success(t('common.savedSuccessfully'));
      navigate('/admin/bots');
    } catch (error) {
      console.error("Failed to save", error);
      // toast.error(t('common.errorOccurred'));
    } finally {
      setSaving(false);
    }
  };

  const filteredAndSortedKbs = useMemo(() => {
    let result = [...kbs];

    // Filter
    if (searchQuery) {
      const lowerQuery = searchQuery.toLowerCase();
      result = result.filter(kb =>
        kb.name.toLowerCase().includes(lowerQuery) ||
        (kb.description && kb.description.toLowerCase().includes(lowerQuery)) ||
        (kb.embedding_model && kb.embedding_model.toLowerCase().includes(lowerQuery)) ||
        (kb.embedding_model_provider && kb.embedding_model_provider.toLowerCase().includes(lowerQuery))
      );
    }

    // Sort
    result.sort((a, b) => {
      // Priority: Selected items first
      const isSelectedA = selectedKbIds.includes(a.id);
      const isSelectedB = selectedKbIds.includes(b.id);

      if (isSelectedA && !isSelectedB) return -1;
      if (!isSelectedA && isSelectedB) return 1;

      // Secondary Sort: Based on user selection
      let valA, valB;

      switch (sortBy) {
        case 'name':
          valA = a.name.toLowerCase();
          valB = b.name.toLowerCase();
          break;
        case 'created_at':
          valA = a.created_at;
          valB = b.created_at;
          break;
        case 'updated_at':
        default:
          valA = a.updated_at || a.created_at;
          valB = b.updated_at || b.created_at;
          break;
      }

      if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
      if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return result;
  }, [kbs, searchQuery, sortBy, sortOrder, selectedKbIds]);

  const formatDate = (timestamp) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp * 1000).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <SpinnerIcon className="animate-spin text-primary-600" size={40} />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate('/admin/bots')}
          className="flex items-center gap-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition mb-4"
        >
          <ArrowLeftIcon size={20} />
          <span>{t('common.backToBots', 'Back to Bots')}</span>
        </button>

        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              {t('admin.bots.kbConfig.pageTitle')} <span className="text-primary-600 dark:text-primary-400">{bot?.name}</span>
            </h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1">
              {t('admin.bots.kbConfig.pageSubtitle')}
            </p>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleSave}
              disabled={saving}
              className="btn-primary flex items-center gap-2 px-6 py-2.5 rounded-xl shadow-lg shadow-primary-500/20 disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {saving ? <SpinnerIcon className="animate-spin" /> : <FloppyDiskIcon size={20} weight="bold" />}
              {t('common.saveChanges', 'Save Changes')}
            </button>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 mb-6 flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-96">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            placeholder={t('admin.bots.kbConfig.searchPlaceholder')}
            className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition-all outline-none"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
          <span className="text-sm text-gray-500 whitespace-nowrap">{t('common.sortBy', 'Sort by:')}</span>
          <select
            className="px-3 py-2 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg text-sm outline-none cursor-pointer hover:border-gray-300 dark:hover:border-gray-500 transition-colors"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="name">{t('admin.bots.kbConfig.sortName')}</option>
            <option value="created_at">{t('admin.bots.table.dateCreated')}</option>
            <option value="updated_at">{t('admin.bots.table.lastUpdated')}</option>
          </select>
          <button
            className="p-2 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
            onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
            title={sortOrder === 'asc' ? "Ascending" : "Descending"}
          >
            <span className="text-xs font-bold">{sortOrder === 'asc' ? 'ASC' : 'DESC'}</span>
          </button>
        </div>
      </div>

      {/* Grid */}
      {filteredAndSortedKbs.length === 0 ? (
        <div className="text-center py-20 bg-white dark:bg-gray-800 rounded-2xl border border-dashed border-gray-300 dark:border-gray-700">
          <p className="text-gray-500 dark:text-gray-400 text-lg">
            {searchQuery ? t('admin.bots.kbConfig.noSearchResults') : t('admin.bots.kbConfig.noKbsAvailable')}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredAndSortedKbs.map(kb => {
            const isSelected = selectedKbIds.includes(kb.id);
            return (
              <div
                key={kb.id}
                onClick={() => handleToggleKb(kb.id)}
                className={`
                  group relative flex flex-col h-full p-6 rounded-2xl border-2 transition-all duration-200 cursor-pointer overflow-hidden
                  ${isSelected
                    ? 'border-primary-500 bg-primary-50/50 dark:bg-primary-900/10 shadow-lg shadow-primary-500/10'
                    : 'border-transparent bg-white dark:bg-gray-800 hover:border-gray-200 dark:hover:border-gray-700 shadow-sm hover:shadow-md'
                  }
                `}
              >
                {/* Selection Indicator */}
                <div className={`
                  absolute top-4 right-4 transition-all duration-200
                  ${isSelected ? 'opacity-100 scale-100' : 'opacity-0 scale-75 group-hover:opacity-100'}
                `}>
                  {isSelected
                    ? <CheckCircleIcon size={28} weight="fill" className="text-primary-600" />
                    : <div className="w-6 h-6 rounded-full border-2 border-gray-300 dark:border-gray-600" />
                  }
                </div>

                {/* Content */}
                <div className="flex-1 pr-8">
                  <h3 className={`font-bold text-lg mb-2 line-clamp-1 ${isSelected ? 'text-primary-900 dark:text-primary-100' : 'text-gray-900 dark:text-gray-100'}`}>
                    {kb.name}
                  </h3>

                  {/* Provider / Model Badge */}
                  <div className="mb-4">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300 border border-gray-200 dark:border-gray-600 max-w-full truncate">
                      {kb.embedding_model_provider || 'Unknown'} / {kb.embedding_model || 'Unknown'}
                    </span>
                  </div>

                  <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-3 mb-4 min-h-[3rem]">
                    {kb.description || t('common.na')}
                  </p>
                </div>

                {/* Footer Data */}
                <div className="pt-4 border-t border-gray-100 dark:border-gray-700/50 flex items-center justify-between text-xs text-gray-400 dark:text-gray-500 font-mono">
                  <span>
                    {sortBy === 'created_at' ? t('common.created') : t('common.updated')}
                  </span>
                  <span>
                    {formatDate(sortBy === 'created_at' ? kb.created_at : (kb.updated_at || kb.created_at))}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default BotKBConfigPage;
