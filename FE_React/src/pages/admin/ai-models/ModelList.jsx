import { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { aiModelService } from '../../../services/aiModelService';
import { PencilSimple, Trash, Plus, Spinner, X, MagnifyingGlassIcon, CaretDownIcon } from '@phosphor-icons/react';
import clsx from 'clsx';
import { toast } from 'react-hot-toast';

const PROVIDER_CAPABILITIES = {
  openai: ['chat', 'embedding'],
  google: ['chat', 'embedding'],
  ollama: ['chat', 'embedding'],
  huggingface: ['chat', 'embedding', 'reranker']
};

const ModelList = () => {
  const { t } = useTranslation('ai-models');
  const [models, setModels] = useState([]);
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingModel, setEditingModel] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: 'name', direction: 'asc' });

  const [formData, setFormData] = useState({
    provider_id: '',
    model_id: '',
    name: '',
    model_type: 'chat',
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
    } else {
      setEditingModel(null);
      setFormData({
        provider_id: '',
        model_id: '',
        name: '',
        model_type: 'chat',
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
    if (!window.confirm(t('models.confirmDelete'))) return;
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

  if (loading) return <div className="p-8 flex justify-center"><Spinner className="animate-spin" size={32} /></div>;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex flex-col sm:flex-row justify-between items-center bg-gray-50/50 dark:bg-gray-900/20 gap-4">
        <h3 className="font-bold text-gray-700 dark:text-gray-200">{t('models.title')}</h3>
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <MagnifyingGlassIcon size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder={t('searchPlaceholder', 'Search...')}
              className="w-full pl-10 pr-4 py-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition shadow-sm"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <button
            onClick={() => handleOpenModal()}
            className="btn-primary flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap"
          >
            <Plus size={16} weight="bold" /> {t('models.create')}
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
                  {t('models.name')} <SortIcon columnKey="name" />
                </div>
              </th>
              <th className="px-6 py-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition group" onClick={() => handleSort('model_id')}>
                <div className="flex items-center gap-1">
                  {t('models.modelId')} <SortIcon columnKey="model_id" />
                </div>
              </th>
              <th className="px-6 py-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition group" onClick={() => handleSort('provider_name')}>
                <div className="flex items-center gap-1">
                  {t('models.provider')} <SortIcon columnKey="provider_name" />
                </div>
              </th>
              <th className="px-6 py-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition group" onClick={() => handleSort('model_type')}>
                <div className="flex items-center gap-1">
                  {t('models.type')} <SortIcon columnKey="model_type" />
                </div>
              </th>
              <th className="px-6 py-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition group" onClick={() => handleSort('is_active')}>
                <div className="flex items-center gap-1">
                  {t('models.status')} <SortIcon columnKey="is_active" />
                </div>
              </th>
              <th className="px-6 py-3 text-right">{t('models.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
            {filteredAndSortedModels.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                  {searchQuery ? t('common.noResults', 'No matching results') : t('models.empty')}
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
                    <span className={clsx(
                      "px-2 py-0.5 rounded text-[10px] font-bold uppercase",
                      m.is_active ? "bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400" : "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400"
                    )}>
                      {m.is_active ? t('common.active') : t('common.inactive')}
                    </span>
                  </td>
                  <td className="px-6 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button onClick={() => handleOpenModal(m)} className="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/10 rounded-lg transition">
                        <PencilSimple size={18} />
                      </button>
                      <button onClick={() => handleDelete(m.id)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/10 rounded-lg transition">
                        <Trash size={18} />
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
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md overflow-hidden animate-fade-in-up">
            <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-gray-900/50">
              <h3 className="font-bold text-lg text-gray-800 dark:text-white">
                {editingModel ? t('models.edit') : t('models.create')}
              </h3>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">{t('models.provider')}</label>
                <select
                  className="input-field"
                  required
                  value={formData.provider_id}
                  onChange={(e) => {
                    const providerId = e.target.value;
                    const selectedProvider = providers.find(p => p.id === providerId);
                    const providerName = selectedProvider?.name?.toLowerCase();
                    const allowedTypes = PROVIDER_CAPABILITIES[providerName] || ['chat', 'embedding', 'reranker'];

                    const newFormData = { ...formData, provider_id: providerId };
                    if (!allowedTypes.includes(formData.model_type)) {
                      newFormData.model_type = allowedTypes[0];
                    }
                    setFormData(newFormData);
                  }}
                >
                  <option value="">Select a provider</option>
                  {providers.map(p => (
                    <option key={p.id} value={p.id}>{p.display_name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">{t('models.name')}</label>
                <input
                  type="text"
                  required
                  className="input-field"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. GPT-4 Turbo"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">{t('models.modelId')}</label>
                  <input
                    type="text"
                    required
                    className="input-field font-mono text-sm"
                    value={formData.model_id}
                    onChange={(e) => setFormData({ ...formData, model_id: e.target.value })}
                    placeholder="e.g. gpt-4-turbo-preview"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">{t('models.type')}</label>
                  <select
                    className="input-field"
                    value={formData.model_type}
                    onChange={(e) => setFormData({ ...formData, model_type: e.target.value })}
                  >
                    {(() => {
                      const selectedProvider = providers.find(p => p.id === formData.provider_id);
                      const providerName = selectedProvider?.name?.toLowerCase();
                      const allowedTypes = PROVIDER_CAPABILITIES[providerName] || ['chat', 'embedding', 'reranker'];

                      return (
                        <>
                          {allowedTypes.includes('chat') && <option value="chat">{t('models.types.chat')}</option>}
                          {allowedTypes.includes('embedding') && <option value="embedding">{t('models.types.embedding')}</option>}
                          {allowedTypes.includes('reranker') && <option value="reranker">{t('models.types.reranker')}</option>}
                        </>
                      );
                    })()}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">{t('models.status')}</label>
                <select
                  className="input-field"
                  value={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.value === 'true' })}
                >
                  <option value="true">{t('common.active')}</option>
                  <option value="false">{t('common.inactive')}</option>
                </select>
              </div>

              <div className="pt-4 flex justify-end gap-2">
                <button type="button" onClick={() => setIsModalOpen(false)} className="btn-secondary text-sm">
                  {t('common.cancel')}
                </button>
                <button type="submit" className="btn-primary text-sm px-4">
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
