import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { XIcon, SpinnerIcon, FloppyDiskIcon, InfoIcon, PencilSimpleIcon, CaretDownIcon } from '@phosphor-icons/react';
import clsx from 'clsx';
import { useBotOptions } from '../../hooks/useBots';
import { useKnowledgeBases } from '../../hooks/useKnowledgeBases';
import TextField from '../common/TextField/TextField';

const CreateKBModal = ({ isOpen, onClose, onSuccess, initialData = null }) => {
  const { t } = useTranslation();
  const { createKB, updateKB } = useKnowledgeBases();
  const {
    providers,
    models,
    fetchProviders,
    fetchModels
  } = useBotOptions();

  const isEditMode = !!initialData;

  const [formData, setFormData] = useState({
    name: '',
    embedding_provider_id: '',
    embedding_model_id: '',
    search_method: 'hybrid',
    auto_merging: true
  });

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);

  // Effect to initialize Form Data
  useEffect(() => {
    if (isOpen) {
      if (initialData) {
        // Parse retrieval_model
        let search_method = 'semantic';
        let auto_merging = false;

        if (initialData.retrieval_model) {
          try {
            const rm = typeof initialData.retrieval_model === 'string'
              ? JSON.parse(initialData.retrieval_model)
              : initialData.retrieval_model;

            search_method = rm.search_method || 'semantic';
            auto_merging = !!rm.auto_merging;
          } catch (e) {
            console.warn("Failed to parse retrieval_model", e);
          }
        }

        // Edit Mode
        setFormData({
          name: initialData.name || '',
          description: initialData.description || '',
          embedding_provider_id: initialData.embedding_provider_id || '',
          embedding_model_id: initialData.embedding_model_id || '',
          search_method,
          auto_merging
        });
      } else {
        // Create Mode
        setFormData({
          name: '',
          description: '',
          embedding_provider_id: '',
          embedding_model_id: '',
          search_method: 'hybrid',
          auto_merging: true
        });
      }
      setError(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  // Effect to fetch options
  useEffect(() => {
    if (isOpen) {
      fetchProviders();
      if (initialData && initialData.embedding_provider_id) {
        fetchModels(initialData.embedding_provider_id, 'embedding');
      }
    }
  }, [isOpen, fetchProviders, fetchModels, initialData?.embedding_provider_id]);

  const handleProviderChange = (e) => {
    const providerId = e.target.value;
    setFormData(prev => ({ ...prev, embedding_provider_id: providerId, embedding_model_id: '' }));
    fetchModels(providerId, 'embedding');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    const payload = {
      name: formData.name,
      description: formData.description,
      // Construct retrieval_model JSONB
      retrieval_model: {
        search_method: formData.search_method,
        auto_merging: formData.auto_merging
      }
    };

    try {
      if (isEditMode) {
        // Update
        await updateKB(initialData.id, payload);
      } else {
        // Create - Include Embedding Fields
        await createKB({
          ...payload,
          embedding_provider_id: formData.embedding_provider_id,
          embedding_model_id: formData.embedding_model_id,
        });
      }

      onSuccess();
      onClose();
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || `Failed to ${isEditMode ? 'update' : 'create'} knowledge base`);
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden border border-gray-100 dark:border-gray-700 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between bg-gray-50/50 dark:bg-gray-700/50 flex-shrink-0">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            {isEditMode ? <PencilSimpleIcon className="text-primary-600" /> : <FloppyDiskIcon className="text-primary-600" />}
            {isEditMode ? t('list.editKbTitle', 'Edit Knowledge Base') : t('list.createKbTitle', 'Create New Knowledge Base')}
          </h3>
          <button
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg transition-colors"
          >
            <XIcon size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto custom-scrollbar">
          <form onSubmit={handleSubmit} className="p-6 space-y-5">
            {error && (
              <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm flex items-start gap-2 border border-red-100 dark:border-red-800">
                <InfoIcon size={18} className="mt-0.5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <TextField
              label={t('list.kbName', 'KB Name')}
              name="name"
              required
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder={t('list.kbNamePlaceholder', 'Enter knowledge base name...')}
              disabled={submitting}
            />

            <div className="space-y-1">
              <TextField
                label={t('list.kbDescription', 'Description')}
                name="description"
                required
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder={t('list.kbDescriptionPlaceholder', 'Briefly describe this knowledge base...')}
                disabled={submitting}
              />
              <p className="text-xs text-amber-600 dark:text-amber-400">
                {t('list.kbDescriptionWarning', '* The AI agent uses this description to decide whether to search this knowledge base. Please be descriptive and accurate.')}
              </p>
            </div>

            {/* Embedding Config - Moved Up Here */}
            {!isEditMode && (
              <div className="space-y-4 pt-2 border-t border-gray-100 dark:border-gray-700">
                <h4 className="text-sm font-bold text-gray-900 dark:text-white">{t('list.embeddingConfig', 'Embedding Configuration')}</h4>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-bold text-gray-600 dark:text-gray-400 mb-2">
                      {t('admin.bots.form.configuration.provider', 'Provider')} <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <select
                        value={formData.embedding_provider_id}
                        onChange={handleProviderChange}
                        disabled={isEditMode || submitting}
                        className="w-full px-4 py-3 bg-white dark:bg-[#1f2937] border border-gray-300 dark:border-gray-700 rounded-lg outline-none text-gray-700 dark:text-gray-200 appearance-none cursor-pointer focus:ring-2 focus:ring-primary-500/20 shadow-sm disabled:opacity-50"
                      >
                        <option value="" disabled>{t('admin.bots.form.configuration.providerPlaceholder', 'Select provider...')}</option>
                        {providers.map(p => <option key={p.id} value={p.id}>{p.display_name}</option>)}
                      </select>
                      <CaretDownIcon size={16} className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-bold text-gray-600 dark:text-gray-400 mb-2">
                      {t('admin.bots.form.configuration.model', 'AI Model')} <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <select
                        value={formData.embedding_model_id}
                        onChange={(e) => setFormData(prev => ({ ...prev, embedding_model_id: e.target.value }))}
                        disabled={!formData.embedding_provider_id || isEditMode || submitting}
                        className="w-full px-4 py-3 bg-white dark:bg-[#1f2937] border border-gray-300 dark:border-gray-700 rounded-lg outline-none text-gray-700 dark:text-gray-200 appearance-none cursor-pointer focus:ring-2 focus:ring-primary-500/20 shadow-sm disabled:opacity-50"
                      >
                        <option value="" disabled>{t('admin.bots.form.configuration.modelPlaceholder', 'Select model...')}</option>
                        {models.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                      </select>
                      <CaretDownIcon size={16} className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-transparent border border-gray-300 dark:border-[rgba(255,255,255,0.8)] rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 leading-relaxed">
                  {t('list.kbWarning', 'Note: The embedding model cannot be changed once the KB is created, as it determines the vector space of all documents within.')}
                </div>
              </div>
            )}

            {isEditMode && (
              <div className="pt-2 border-t border-gray-100 dark:border-gray-700">
                <p className="p-4 bg-transparent border border-gray-300 dark:border-[rgba(255,255,255,0.8)] rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 leading-relaxed">
                  {t('list.kbEditWarning', 'Note: Embedding Provider and Model cannot be changed once created.')}
                </p>
              </div>
            )}

            {/* Advanced Settings */}
            <div className="pt-2 border-t border-gray-100 dark:border-gray-700">
              <button
                type="button"
                onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
                className="flex items-center gap-3 text-sm font-bold text-gray-700 dark:text-gray-200 hover:text-primary-600 dark:hover:text-white transition-colors w-full p-3.5 rounded-lg bg-gray-50 hover:bg-gray-100 dark:bg-gray-700/50 dark:hover:bg-gray-700"
              >
                <CaretDownIcon size={18} className={clsx("transition-transform duration-200", !showAdvancedSettings && "-rotate-90")} />
                {t('list.advancedSettings', 'Advanced Settings')}
              </button>

              <div className={clsx("overflow-hidden transition-all duration-300 ease-in-out", showAdvancedSettings ? "max-h-[800px] opacity-100 mt-6" : "max-h-0 opacity-0")}>
                <div className="space-y-6">
                  {/* Retrieval Config Section */}
                  <div className="space-y-4">
                    <h4 className="text-base font-bold text-gray-900 dark:text-white">{t('list.retrievalConfig.title', 'Retrieval Configuration')}</h4>

                    <div className="space-y-2">
                      <label className="block text-sm font-bold text-gray-600 dark:text-gray-300">{t('list.retrievalConfig.searchMethod', 'Search Method')}</label>
                      <div className="relative">
                        <select
                          name="search_method"
                          value={formData.search_method}
                          onChange={(e) => setFormData(prev => ({ ...prev, search_method: e.target.value }))}
                          className="w-full px-4 py-3 bg-white dark:bg-[#1f2937] border border-gray-300 dark:border-gray-700 rounded-lg outline-none text-gray-700 dark:text-gray-200 appearance-none cursor-pointer focus:ring-2 focus:ring-primary-500/20 shadow-sm"
                          disabled={submitting}
                        >
                          <option value="semantic">{t('list.retrievalConfig.semantic', 'Semantic (Dense Vector)')}</option>
                          <option value="hybrid">{t('list.retrievalConfig.hybrid', 'Hybrid (Dense + Keyword)')}</option>
                        </select>
                        <CaretDownIcon size={16} className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                      </div>
                    </div>

                    <label className="flex items-start gap-4 p-4 bg-white dark:bg-[#1f2937] border border-gray-300 dark:border-gray-700 rounded-lg cursor-pointer hover:border-gray-400 dark:hover:border-gray-600 transition-colors shadow-sm">
                      <div className="flex items-center h-5 mt-0.5">
                        <input
                          type="checkbox"
                          checked={formData.auto_merging}
                          onChange={(e) => setFormData(prev => ({ ...prev, auto_merging: e.target.checked }))}
                          className="w-4 h-4 text-primary-600 bg-white border-gray-300 rounded focus:ring-primary-500 dark:focus:ring-primary-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-[#1f2937] dark:border-gray-500 cursor-pointer"
                          disabled={submitting}
                        />
                      </div>
                      <div className="flex-1 text-sm">
                        <div className="font-bold text-gray-900 dark:text-gray-200 mb-1">{t('list.retrievalConfig.autoMerging', 'Enable Auto-Merging')}</div>
                        <p className="text-gray-500 dark:text-gray-400 text-xs leading-relaxed">{t('list.retrievalConfig.autoMergingDesc', 'Combine smaller chunks into larger context (Requires Parent-Child indexing)')}</p>
                      </div>
                    </label>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="pt-4 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
              >
                {t('common.cancel')}
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-xl text-sm font-bold shadow-lg shadow-primary-500/20 transition-all flex items-center gap-2 disabled:opacity-70"
              >
                {submitting ? <SpinnerIcon className="animate-spin" size={18} /> : (isEditMode ? <PencilSimpleIcon size={18} weight="bold" /> : <FloppyDiskIcon size={18} weight="bold" />)}
                {isEditMode ? t('common.save', 'Save Changes') : t('common.create', 'Create KB')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CreateKBModal;
