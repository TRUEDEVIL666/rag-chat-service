import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { XIcon, SpinnerIcon, FloppyDiskIcon, InfoIcon } from '@phosphor-icons/react';
import { useBotOptions } from '../../hooks/useBots';
import { useKnowledgeBases } from '../../hooks/useKnowledgeBases';
import TextField from '../common/TextField/TextField';
import Select from '../common/Select/Select';

const CreateKBModal = ({ isOpen, onClose, onSuccess }) => {
  const { t } = useTranslation(['admin/documents', 'admin/bots', 'translation']);
  const { createKB } = useKnowledgeBases();
  const {
    providers,
    models,
    fetchProviders,
    fetchModels,
    loading: optionsLoading
  } = useBotOptions();

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    embedding_provider_id: '',
    embedding_model_id: '',
  });

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      fetchProviders();
      // Reset form
      setFormData({
        name: '',
        description: '',
        embedding_provider_id: '',
        embedding_model_id: '',
      });
      setError(null);
    }
  }, [isOpen, fetchProviders]);

  const handleProviderChange = (e) => {
    const providerId = e.target.value;
    setFormData(prev => ({ ...prev, embedding_provider_id: providerId, embedding_model_id: '' }));
    fetchModels(providerId, 'embedding');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await createKB(formData);
      onSuccess();
      onClose();
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Failed to create knowledge base');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden border border-gray-100 dark:border-gray-700">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between bg-gray-50/50 dark:bg-gray-700/50">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">
            {t('list.createKbTitle', 'Create New Knowledge Base')}
          </h3>
          <button
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg transition-colors"
          >
            <XIcon size={20} />
          </button>
        </div>

        {/* Body */}
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
          />

          <TextField
            label={t('list.kbDescription', 'Description')}
            name="description"
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            placeholder={t('list.kbDescriptionPlaceholder', 'Briefly describe this knowledge base...')}
          />

          <div className="grid grid-cols-2 gap-4">
            <Select
              label={t('admin/bots:form.configuration.provider')}
              name="embedding_provider_id"
              required
              value={formData.embedding_provider_id}
              onChange={handleProviderChange}
              options={providers.map(p => ({ value: p.id, label: p.display_name }))}
              placeholder={t('admin/bots:form.configuration.providerPlaceholder')}
              loading={optionsLoading}
            />

            <Select
              label={t('admin/bots:form.configuration.model')}
              name="embedding_model_id"
              required
              value={formData.embedding_model_id}
              onChange={(e) => setFormData(prev => ({ ...prev, embedding_model_id: e.target.value }))}
              options={models.map(m => ({ value: m.id, label: m.name }))}
              placeholder={t('admin/bots:form.configuration.modelPlaceholder')}
              disabled={!formData.embedding_provider_id}
              loading={optionsLoading}
            />
          </div>

          <p className="text-xs text-secondary-500 bg-secondary-50 dark:bg-secondary-900/20 p-3 rounded-lg border border-secondary-100 dark:border-secondary-800 leading-relaxed">
            {t('list.kbWarning', 'Note: The embedding model cannot be changed once the KB is created, as it determines the vector space of all documents within.')}
          </p>

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
              {submitting ? <SpinnerIcon className="animate-spin" size={18} /> : <FloppyDiskIcon size={18} weight="bold" />}
              {t('common.create', 'Create KB')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateKBModal;
