import { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { aiModelService } from '../../../services/aiModelService';
import { PencilSimple, Trash, Plus, Spinner, X, MagnifyingGlassIcon, CaretDownIcon } from '@phosphor-icons/react';
import clsx from 'clsx';
import { toast } from 'react-hot-toast';

const ProviderList = () => {
  const { t } = useTranslation();
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProvider, setEditingProvider] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: 'display_name', direction: 'asc' });

  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    base_url: '',
    api_key: '',
    is_active: true
  });

  const fetchProviders = async () => {
    try {
      setLoading(true);
      const data = await aiModelService.getProviders();
      setProviders(data);
    } catch (error) {
      console.error(error);
      toast.error(t('common.errorFetch'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProviders();
  }, []);

  const handleOpenModal = (provider = null) => {
    if (provider) {
      setEditingProvider(provider);
      setFormData({
        name: provider.name,
        display_name: provider.display_name,
        base_url: provider.base_url || '',
        api_key: '', // Don't show existing key
        is_active: provider.is_active
      });
    } else {
      setEditingProvider(null);
      setFormData({
        name: '',
        display_name: '',
        base_url: '',
        api_key: '',
        is_active: true
      });
    }
    setIsModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingProvider) {
        await aiModelService.updateProvider(editingProvider.id, formData);
        toast.success(t('common.successUpdate'));
      } else {
        await aiModelService.createProvider(formData);
        toast.success(t('common.successCreate'));
      }
      setIsModalOpen(false);
      fetchProviders();
    } catch (error) {
      console.error(error);
      toast.error(error.message || 'Error saving provider');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm(t('admin.aiModels.providers.confirmDelete'))) return;
    try {
      await aiModelService.deleteProvider(id);
      toast.success('Deleted successfully');
      fetchProviders();
    } catch (error) {
      console.error(error);
      toast.error('Error deleting provider');
    }
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

  const filteredAndSortedProviders = useMemo(() => {
    let result = [...providers];

    // Filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(p =>
        p.display_name.toLowerCase().includes(query) ||
        p.name.toLowerCase().includes(query)
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
  }, [providers, searchQuery, sortConfig]);

  if (loading) return <div className="p-8 flex justify-center"><Spinner className="animate-spin" size={32} /></div>;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex flex-col sm:flex-row justify-between items-center bg-gray-50/50 dark:bg-gray-900/20 gap-4">
        <h3 className="font-bold text-gray-700 dark:text-gray-200">{t('admin.aiModels.providers.title')}</h3>
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
            <Plus size={16} weight="bold" /> {t('admin.aiModels.providers.create')}
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 dark:bg-gray-700/50 border-b border-gray-100 dark:border-gray-700 text-xs uppercase text-gray-500 dark:text-gray-400">
            <tr>
              <th className="px-6 py-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition group" onClick={() => handleSort('display_name')}>
                <div className="flex items-center gap-1">
                  {t('admin.aiModels.providers.displayName')} <SortIcon columnKey="display_name" />
                </div>
              </th>
              <th className="px-6 py-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition group" onClick={() => handleSort('name')}>
                <div className="flex items-center gap-1">
                  {t('admin.aiModels.providers.name')} <SortIcon columnKey="name" />
                </div>
              </th>
              <th className="px-6 py-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition group" onClick={() => handleSort('base_url')}>
                <div className="flex items-center gap-1">
                  {t('admin.aiModels.providers.baseUrl')} <SortIcon columnKey="base_url" />
                </div>
              </th>
              <th className="px-6 py-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition group" onClick={() => handleSort('is_active')}>
                <div className="flex items-center gap-1">
                  {t('admin.aiModels.providers.status')} <SortIcon columnKey="is_active" />
                </div>
              </th>
              <th className="px-6 py-3 text-right">{t('admin.aiModels.providers.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
            {filteredAndSortedProviders.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                  {searchQuery ? t('common.noResults') : t('admin.aiModels.providers.empty')}
                </td>
              </tr>
            ) : (
              filteredAndSortedProviders.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition">
                  <td className="px-6 py-3 font-medium text-gray-900 dark:text-gray-100">{p.display_name}</td>
                  <td className="px-6 py-3 font-mono text-xs text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/10 px-2 py-0.5 rounded w-fit">{p.name}</td>
                  <td className="px-6 py-3 text-gray-500 dark:text-gray-400 truncate max-w-[200px]" title={p.base_url}>{p.base_url || '-'}</td>
                  <td className="px-6 py-3">
                    <span className={clsx(
                      "px-2 py-0.5 rounded text-[10px] font-bold uppercase",
                      p.is_active ? "bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400" : "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400"
                    )}>
                      {p.is_active ? t('common.status.active') : t('common.status.inactive')}
                    </span>
                  </td>
                  <td className="px-6 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button onClick={() => handleOpenModal(p)} className="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/10 rounded-lg transition">
                        <PencilSimple size={18} />
                      </button>
                      <button onClick={() => handleDelete(p.id)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/10 rounded-lg transition">
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
                {editingProvider ? t('admin.aiModels.providers.edit') : t('admin.aiModels.providers.create')}
              </h3>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">{t('admin.aiModels.providers.displayName')}</label>
                <input
                  type="text"
                  required
                  className="input-field"
                  value={formData.display_name}
                  onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                  placeholder="e.g. OpenAI"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">{t('admin.aiModels.providers.name')}</label>
                  <select
                    required
                    className="input-field"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  >
                    <option value="" disabled>Select provider</option>
                    {['openai', 'google', 'huggingface', 'ollama'].map((p) => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">{t('admin.aiModels.providers.status')}</label>
                  <select
                    className="input-field"
                    value={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.value === 'true' })}
                  >
                    <option value="true">{t('common.status.active')}</option>
                    <option value="false">{t('common.status.inactive')}</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">{t('admin.aiModels.providers.baseUrl')}</label>
                <input
                  type="text"
                  className="input-field font-mono text-sm"
                  value={formData.base_url}
                  onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
                  placeholder="https://api.openai.com/v1"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">{t('admin.aiModels.providers.apiKey')}</label>
                <input
                  type="password"
                  className="input-field font-mono text-sm"
                  value={formData.api_key}
                  onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                  placeholder={editingProvider?.secret_id ? "•••••••• (Stored)" : "Enter API Key"}
                />
                <p className="text-[10px] text-gray-400 mt-1">{t('admin.aiModels.providers.apiKeyDesc')}</p>
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

export default ProviderList;
