import { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { aiModelService } from '../../../services/aiModelService';
import { PencilSimpleIcon, TrashIcon, PlusIcon, SpinnerIcon, XIcon, MagnifyingGlassIcon, CaretDownIcon } from '@phosphor-icons/react';
import { toast } from 'react-hot-toast';
import SearchableSelect from '../../../components/common/SearchableSelect';

const PROVIDER_CAPABILITIES = {
  openai: ['chat', 'embedding'],
  google: ['chat', 'embedding'],
  ollama: ['chat', 'embedding'],
  huggingface: ['chat', 'embedding', 'reranker']
};

const ModelList = () => {
  const { t } = useTranslation();
  const [models, setModels] = useState([]);
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingModel, setEditingModel] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: 'name', direction: 'asc' });

  // New state for dynamic fetching
  const [externalModels, setExternalModels] = useState([]);
  const [isFetchingModels, setIsFetchingModels] = useState(false);

  const [formData, setFormData] = useState({
    provider_id: '',
    model_id: '',
    name: '',
    model_type: '',
    is_active: true,
    config: {}
  });

  const fetchData = async () => {
    try {
      setLoading(true);
      const [modelsData, providersData] = await Promise.all([
        aiModelService.getAllModels(),
        aiModelService.getProviders()
      ]);
      setModels(modelsData);
      setProviders(providersData);
    } catch (error) {
      console.error(error);
      toast.error(t('common.errorFetch'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Effect to fetch external models when provider or type changes
  useEffect(() => {
    const fetchExternalModels = async () => {
      if (formData.provider_id && formData.model_type) {
        // Ensure the provider is one that supports fetching (optional check, or just try)
        // We'll just try for all, backend will handle or return empty
        setIsFetchingModels(true);
        setExternalModels([]);
        try {
          const models = await aiModelService.getProviderExternalModels(formData.provider_id, formData.model_type);
          setExternalModels(models);
        } catch (error) {
          console.error("Failed to fetch external models", error);
          // Don't toast error here to avoid spamming if provider doesn't support it, 
          // unless it's a connection error which backend 400s.
          // But for UX, maybe just silent fail or show empty list if not supported.
          // If it's a real error (network), backend sends 400/500.
        } finally {
          setIsFetchingModels(false);
        }
      } else {
        setExternalModels([]);
      }
    };

    // Only fetch if modal is open and we are NOT editing an existing model (or maybe we should? 
    // If editing, we might want to change model ID, but usually not. 
    // Let's allow it for flexibility).
    if (isModalOpen) {
      fetchExternalModels();
    }
  }, [formData.provider_id, formData.model_type, isModalOpen]);


  const handleOpenModal = (model = null) => {
    if (model) {
      setEditingModel(model);
      setFormData({
        provider_id: model.provider_id,
        model_id: model.model_id,
        name: model.name,
        model_type: model.model_type,
        is_active: model.is_active,
        config: model.config || {}
      });
      // When editing, we might want to load the external models list too in case they want to change it
      // But we don't strictly need to trigger it here since the useEffect will catch the state change.
    } else {
      setEditingModel(null);
      setFormData({
        provider_id: '',
        model_id: '',
        name: '',
        model_type: '',
        is_active: true,
        config: {}
      });
    }
    setIsModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingModel) {
        await aiModelService.updateModel(editingModel.id, formData);
        toast.success(t('common.successUpdate'));
      } else {
        await aiModelService.createModel(formData);
        toast.success(t('common.successCreate'));
      }
      setIsModalOpen(false);
      fetchData();
    } catch (error) {
      console.error(error);
      toast.error(error.message || 'Error saving model');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm(t('admin.aiModels.models.confirmDelete'))) return;
    try {
      await aiModelService.deleteModel(id);
      toast.success('Deleted successfully');
      fetchData();
    } catch (error) {
      console.error(error);
      toast.error('Error deleting model');
    }
  };

  const getProviderName = (providerId) => {
    const provider = providers.find(p => p.id === providerId);
    return provider ? provider.display_name : 'Unknown';
  };

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const SortIcon = ({ columnKey }) => {
    if (sortConfig.key !== columnKey) return <CaretDownIcon size={12} className="opacity-0 group-hover:opacity-50" />;
    return sortConfig.direction === 'asc'
      ? <CaretDownIcon size={12} className="transform rotate-180 text-primary-600" />
      : <CaretDownIcon size={12} className="text-primary-600" />;
  };

  const filteredAndSortedModels = useMemo(() => {
    let result = models.map(m => ({
      ...m,
      provider_name: getProviderName(m.provider_id)
    }));

    // Filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(m =>
        m.name.toLowerCase().includes(query) ||
        m.model_id.toLowerCase().includes(query) ||
        m.model_type.toLowerCase().includes(query) ||
        m.provider_name.toLowerCase().includes(query)
      );
    }

    // Sort
    if (sortConfig.key) {
      result.sort((a, b) => {
        const aValue = a[sortConfig.key];
        const bValue = b[sortConfig.key];

        if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return result;
  }, [models, providers, searchQuery, sortConfig]);

  if (loading) return <div className="p-8 flex justify-center"><SpinnerIcon className="animate-spin" size={32} /></div>;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex flex-col sm:flex-row justify-between items-center bg-gray-50/50 dark:bg-gray-900/20 gap-4">
        <h3 className="font-bold text-gray-700 dark:text-gray-200">{t('admin.aiModels.models.title')}</h3>
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <MagnifyingGlassIcon size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder={t('admin.aiModels.searchPlaceholder')}
              className="w-full pl-10 pr-4 py-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition shadow-sm"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <button
            onClick={() => handleOpenModal()}
            className="btn-primary flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap"
          >
            <PlusIcon size={16} weight="bold" /> {t('admin.aiModels.models.create')}
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 dark:bg-gray-700/50 border-b border-gray-100 dark:border-gray-700 text-xs uppercase text-gray-500 dark:text-gray-400">
            <tr>
              <th className="px-6 py-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition group" onClick={() => handleSort('name')}>
                <div className="flex items-center gap-1">
                  {t('admin.aiModels.models.name')} <SortIcon columnKey="name" />
                </div>
              </th>
              <th className="px-6 py-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition group" onClick={() => handleSort('model_id')}>
                <div className="flex items-center gap-1">
                  {t('admin.aiModels.models.modelId')} <SortIcon columnKey="model_id" />
                </div>
              </th>
              <th className="px-6 py-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition group" onClick={() => handleSort('provider_name')}>
                <div className="flex items-center gap-1">
                  {t('admin.aiModels.models.provider')} <SortIcon columnKey="provider_name" />
                </div>
              </th>
              <th className="px-6 py-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition group" onClick={() => handleSort('model_type')}>
                <div className="flex items-center gap-1">
                  {t('admin.aiModels.models.type')} <SortIcon columnKey="model_type" />
                </div>
              </th>
              <th className="px-6 py-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition group" onClick={() => handleSort('is_active')}>
                <div className="flex items-center gap-1">
                  {t('admin.aiModels.models.status')} <SortIcon columnKey="is_active" />
                </div>
              </th>
              <th className="px-6 py-3 text-right">{t('admin.aiModels.models.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
            {filteredAndSortedModels.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                  {searchQuery ? t('common.noResults') : t('admin.aiModels.models.empty')}
                </td>
              </tr>
            ) : (
              filteredAndSortedModels.map((m) => (
                <tr key={m.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition">
                  <td className="px-6 py-3 font-medium text-gray-900 dark:text-gray-100">{m.name}</td>
                  <td className="px-6 py-3 font-mono text-xs text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/10 px-2 py-0.5 rounded w-fit">{m.model_id}</td>
                  <td className="px-6 py-3 text-gray-500 dark:text-gray-400">{m.provider_name}</td>
                  <td className="px-6 py-3 text-gray-500 dark:text-gray-400 capitalize whitespace-nowrap">{m.model_type}</td>
                  <td className="px-6 py-3">
                    {m.is_active ? (
                      <span className="flex items-center gap-2 text-green-600 dark:text-green-400 font-bold bg-green-50 dark:bg-green-900/20 px-3 py-1 rounded-full w-fit text-[11px] border border-green-100 dark:border-green-900/30">
                        <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span> {t('common.status.active')}
                      </span>
                    ) : (
                      <span className="flex items-center gap-2 text-gray-500 dark:text-gray-400 font-bold bg-gray-100 dark:bg-gray-700 px-3 py-1 rounded-full w-fit text-[11px] border border-gray-200 dark:border-gray-600">
                        <span className="w-1.5 h-1.5 rounded-full bg-gray-400"></span> {t('common.status.inactive')}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button onClick={() => handleOpenModal(m)} className="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/10 rounded-lg transition">
                        <PencilSimpleIcon size={18} />
                      </button>
                      <button onClick={() => handleDelete(m.id)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/10 rounded-lg transition">
                        <TrashIcon size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-2xl border border-gray-100 dark:border-gray-700 animate-fade-in-up">
            <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-gray-900/50">
              <h3 className="font-bold text-lg text-gray-800 dark:text-white">
                {editingModel ? t('admin.aiModels.models.edit') : t('admin.aiModels.models.create')}
              </h3>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                <XIcon size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {/* Row 1: Provider */}
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">{t('admin.aiModels.models.provider')}</label>
                <select
                  className="input-field"
                  required
                  value={formData.provider_id}
                  onChange={(e) => {
                    const providerId = e.target.value;
                    setFormData(prev => ({
                      ...prev,
                      provider_id: providerId,
                      model_type: '', // Reset type on provider change
                      model_id: '',   // Reset model ID
                      name: ''        // Reset name
                    }));
                  }}
                >
                  <option value="">{t('common.select')} {t('admin.aiModels.models.provider')}</option>
                  {providers.map(p => (
                    <option key={p.id} value={p.id}>{p.display_name}</option>
                  ))}
                </select>
              </div>

              {/* Row 2: Type and Model ID */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">{t('admin.aiModels.models.type')}</label>
                  <select
                    className={`input-field ${!formData.provider_id ? 'opacity-50 cursor-not-allowed' : ''}`}
                    value={formData.model_type}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      model_type: e.target.value,
                      model_id: '', // Reset model on type change
                      name: ''      // Reset name
                    }))}
                    disabled={!formData.provider_id}
                    required
                  >
                    <option value="">{t('common.select')} {t('admin.aiModels.models.type')}</option>
                    {formData.provider_id && (() => {
                      const selectedProvider = providers.find(p => p.id === formData.provider_id);
                      const providerName = selectedProvider?.name?.toLowerCase();
                      const allowedTypes = PROVIDER_CAPABILITIES[providerName] || ['chat', 'embedding', 'reranker'];
                      return (
                        <>
                          {allowedTypes.includes('chat') && <option value="chat">{t('admin.aiModels.models.types.chat')}</option>}
                          {allowedTypes.includes('embedding') && <option value="embedding">{t('admin.aiModels.models.types.embedding')}</option>}
                          {allowedTypes.includes('reranker') && <option value="reranker">{t('admin.aiModels.models.types.reranker')}</option>}
                        </>
                      );
                    })()}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">{t('admin.aiModels.models.modelId')}</label>
                  <SearchableSelect
                    options={externalModels}
                    value={formData.model_id}
                    onChange={(val) => {
                      setFormData(prev => ({
                        ...prev,
                        model_id: val,
                        // Auto-fill name if empty or if it was just the ID
                        name: (!prev.name || prev.name === prev.model_id) ? val : prev.name
                      }));
                    }}
                    disabled={!formData.model_type || !formData.provider_id}
                    loading={isFetchingModels}
                    placeholder={!formData.model_type ? "Select type first..." : (isFetchingModels ? "Fetching models..." : "Select or type model ID")}
                    allowCustom={true}
                  />
                  {/* Helper hidden input for standard form validation if needed, or we rely on SearchableSelect's state */}
                  <input
                    type="hidden"
                    name="model_id"
                    value={formData.model_id}
                    required
                  />
                </div>
              </div>

              {/* Row 3: Name and Status */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">{t('admin.aiModels.models.name')}</label>
                  <input
                    type="text"
                    required
                    className={`input-field ${!formData.model_id ? 'opacity-50 cursor-not-allowed' : ''}`}
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g. GPT-4 Turbo"
                    disabled={!formData.model_id}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">{t('admin.aiModels.models.status')}</label>
                  <select
                    className={`input-field ${!formData.model_id ? 'opacity-50 cursor-not-allowed' : ''}`}
                    value={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.value === 'true' })}
                    disabled={!formData.model_id}
                  >
                    <option value="true">{t('common.status.active')}</option>
                    <option value="false">{t('common.status.inactive')}</option>
                  </select>
                </div>
              </div>

              <div className="pt-4 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setIsModalOpen(false);
                    setEditingModel(null);
                    setExternalModels([]);
                  }}
                  className="btn-secondary text-sm"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  className={`btn-primary text-sm px-4 ${!formData.model_id ? 'opacity-50 cursor-not-allowed' : ''}`}
                  disabled={!formData.model_id}
                >
                  {t('common.save')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelList;
