import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { XIcon, SpinnerIcon, FloppyDiskIcon, InfoIcon, PencilSimpleIcon } from '@phosphor-icons/react';
import { useBotOptions } from '../../hooks/useBots';
import { useKnowledgeBases } from '../../hooks/useKnowledgeBases';
import TextField from '../common/TextField/TextField';
import Select from '../common/Select/Select';

const CreateKBModal = ({ isOpen, onClose, onSuccess, initialData = null }) => {
  const { t } = useTranslation();
  const { createKB, updateKB } = useKnowledgeBases();
  const {
    providers,
    models,
    fetchProviders,
    fetchModels,
    loading: optionsLoading
  } = useBotOptions();

  const isEditMode = !!initialData;

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    embedding_provider_id: '',
    embedding_model_id: '',
    search_method: 'semantic',
    auto_merging: false
  });

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

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
          search_method: 'semantic',
          auto_merging: false
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

            <TextField
              label={t('list.kbDescription', 'Description')}
              name="description"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder={t('list.kbDescriptionPlaceholder', 'Briefly describe this knowledge base...')}
              disabled={submitting}
            />

            {/* Retrieval Config Section */}
            <div className="space-y-3 pt-2 border-t border-gray-100 dark:border-gray-700">
              <h4 className="text-sm font-semibold text-gray-900 dark:text-white">Retrieval Configuration</h4>

              <Select
                label="Search Method"
                name="search_method"
                value={formData.search_method}
                onChange={(e) => setFormData(prev => ({ ...prev, search_method: e.target.value }))}
                options={[
                  { value: 'semantic', label: 'Semantic (Dense Vector)' },
                  { value: 'hybrid', label: 'Hybrid (Dense + Keyword)' }
                ]}
                disabled={submitting}
              />

              <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700/30 rounded-lg border border-gray-100 dark:border-gray-700">
                <div className="flex items-center h-5">
                  <input
                    id="auto_merging"
                    name="auto_merging"
                    type="checkbox"
                    checked={formData.auto_merging}
                    onChange={(e) => setFormData(prev => ({ ...prev, auto_merging: e.target.checked }))}
                    className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500 dark:bg-gray-700 dark:border-gray-600"
                    disabled={submitting}
                  />
                </div>
                <div className="ml-2 text-sm">
                  <label htmlFor="auto_merging" className="font-medium text-gray-700 dark:text-gray-300">Enable Auto-Merging</label>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Combine smaller chunks into larger context (Requires Parent-Child indexing)</p>
                </div>
              </div>
            </div>

            {!isEditMode && (
              <div className="space-y-4 pt-2 border-t border-gray-100 dark:border-gray-700">
                <h4 className="text-sm font-semibold text-gray-900 dark:text-white">Embedding Configuration</h4>
                <div className="grid grid-cols-2 gap-4">
                  <Select
                    label={t('admin.bots.form.configuration.provider')}
                    name="embedding_provider_id"
                    required
                    value={formData.embedding_provider_id}
                    onChange={handleProviderChange}
                    options={providers.map(p => ({ value: p.id, label: p.display_name }))}
                    placeholder={t('admin.bots.form.configuration.providerPlaceholder')}
                    loading={optionsLoading}
                    disabled={isEditMode || submitting}
                  />

                  <Select
                    label={t('admin.bots.form.configuration.model')}
                    name="embedding_model_id"
                    required
                    value={formData.embedding_model_id}
                    onChange={(e) => setFormData(prev => ({ ...prev, embedding_model_id: e.target.value }))}
                    options={models.map(m => ({ value: m.id, label: m.name }))}
                    placeholder={t('admin.bots.form.configuration.modelPlaceholder')}
                    disabled={!formData.embedding_provider_id || isEditMode || submitting}
                    loading={optionsLoading}
                  />
                </div>
                <p className="text-xs text-secondary-500 bg-secondary-50 dark:bg-secondary-900/20 p-3 rounded-lg border border-secondary-100 dark:border-secondary-800 leading-relaxed">
                  {t('list.kbWarning', 'Note: The embedding model cannot be changed once the KB is created, as it determines the vector space of all documents within.')}
                </p>
              </div>
            )}

            {isEditMode && (
              <p className="text-xs text-gray-500 bg-gray-50 dark:bg-gray-700/50 p-3 rounded-lg border border-gray-100 dark:border-gray-700 leading-relaxed">
                {t('list.kbEditWarning', 'Note: Embedding Provider and Model cannot be changed.')}
              </p>
            )}

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
