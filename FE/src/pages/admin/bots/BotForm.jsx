import {
  ArrowLeftIcon,
  ArrowRightIcon,
  CpuIcon,
  FloppyDiskIcon,
  LightningIcon,
  MagicWandIcon,
  NotebookIcon,
  RobotIcon
} from '@phosphor-icons/react';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import Button from '../../../components/common/Button';
import Select from '../../../components/common/Select';
import TextField from '../../../components/common/TextField';
import TourButton from '../../../components/common/TourButton';
import { useBotOptions, useBots } from '../../../hooks/useBots';
import { usePageTour } from '../../../hooks/usePageTour';
import { ROUTES } from '../../../routes';

const BotForm = ({ initialData, isEdit = false }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { createBot, updateBot, loading: processing } = useBots();
  const { providers, models, rerankers, loading: loadingOptions, fetchProviders, fetchModels, fetchRerankers } = useBotOptions();

  const tourSteps = [
    { element: '#bot-name-input', popover: { title: t('tour.bots.form.name'), description: t('tour.bots.form.nameDesc') } },
    { element: '#provider-select', popover: { title: t('tour.bots.form.provider'), description: t('tour.bots.form.providerDesc') } },
    { element: '#model-select', popover: { title: t('tour.bots.form.model'), description: t('tour.bots.form.modelDesc') } },
    { element: '#system-prompt-input', popover: { title: t('tour.bots.form.prompt'), description: t('tour.bots.form.promptDesc') } },
    { element: '#save-bot-btn', popover: { title: t('tour.bots.form.save'), description: t('tour.bots.form.saveDesc') } }
  ];

  const { startTour } = usePageTour('bot-form', tourSteps);

  /* State */
  const [formData, setFormData] = useState({
    bot_name: '',
    description: '',
    provider_id: '',
    model_id: '',
    system_prompt: '',
    config_model: {
      temperature: 0.7,
      top_k: 10,
      score_threshold: 0.4,
      score_threshold_enabled: false,
      reranking_enable: false,
      reranking_model: 'cross-encoder/ms-marco-MiniLM-L-6-v2'
    }
  });

  // Fetch providers and rerankers on mount
  useEffect(() => {
    fetchProviders();
    fetchRerankers();
  }, [fetchProviders, fetchRerankers]);

  // Handle initial data
  useEffect(() => {
    if (initialData) {
      setFormData({
        bot_name: initialData.bot_name || '',
        description: initialData.description || '',
        provider_id: initialData.provider_id || '',
        model_id: initialData.model_id || '',
        system_prompt: initialData.config_prompt || initialData.system_prompt || '', // Handle legacy/renamed field
        config_model: {
          temperature: initialData.config_model?.temperature ?? 0.7,
          top_k: initialData.config_model?.top_k ?? 10,
          score_threshold: initialData.config_model?.score_threshold ?? 0.4,
          score_threshold_enabled: initialData.config_model?.score_threshold_enabled ?? false,
          reranking_enable: initialData.config_model?.reranking_enable ?? (!!initialData.config_model?.reranking_mode) ?? false,
          reranking_model: initialData.config_model?.reranking_model ||
            initialData.config_model?.reranking_mode?.model_name ||
            initialData.config_model?.reranking_mode?.reranking_model ||
            'cross-encoder/ms-marco-MiniLM-L-6-v2'
        }
      });
      // Fetch models for the existing provider
      if (initialData.provider_id) {
        fetchModels(initialData.provider_id, 'chat');
      }
    }
  }, [initialData, fetchModels]);

  const handleProviderChange = (newProviderId) => {
    fetchModels(newProviderId, 'chat');
    setFormData(prev => ({ ...prev, provider_id: newProviderId, model_id: '' }));
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    if (name === 'provider_id') {
      handleProviderChange(value);
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        name: formData.bot_name,
        description: formData.description,
        provider_id: formData.provider_id,
        model_id: formData.model_id,
        config_prompt: formData.system_prompt,
        config_model: formData.config_model
      };

      if (isEdit) {
        await updateBot(initialData.id, payload);
        alert(t('admin.bots.form.updateSuccess'));
        navigate('/admin/bots');
      } else {
        const newBot = await createBot(payload);
        alert(t('admin.bots.form.createSuccess'));
        // Redirect to configurable KB page for the new bot
        navigate(`/admin/bots/${newBot.id}/kbs`);
      }
    } catch (error) {
      alert(t('common.errorOccurred') + ': ' + (error.response?.data?.detail || t('common.actionFailed')));
      console.error(error);
    }
  };

  // Auto-select first model if list loaded and no model selected (optional, existing logic did this)
  useEffect(() => {
    if (models.length > 0 && !formData.model_id && !isEdit) {
      setFormData(prev => ({ ...prev, model_id: models[0].id }));
    }
  }, [models, formData.model_id, isEdit]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-auto p-6 flex justify-center">
        <div className="w-full max-w-6xl">
          <form onSubmit={handleSubmit}>
            {/* Header Section */}
            <div className="mb-4">
              <div className="flex items-center gap-4">
                <button
                  type="button"
                  onClick={() => navigate(ROUTES.ADMIN.BOTS.LIST)}
                  className="flex items-center gap-2 text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-4 py-2 rounded-xl shadow-sm transition-colors w-fit"
                  title={t('common.back')}
                >
                  <ArrowLeftIcon size={16} />
                  {t('common.back', 'Back')}
                </button>
                <div className="flex items-center gap-3">
                  <TourButton startTour={startTour} />
                </div>
              </div>
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
              {/* LEFT COLUMN */}
              <div className="lg:col-span-7">
                <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 space-y-6 shadow-sm border border-gray-100 dark:border-gray-700">

                  <div>
                    <TextField
                      id="bot-name-input"
                      label={t('admin.bots.form.nameLabel')}
                      name="bot_name"
                      value={formData.bot_name}
                      onChange={handleChange}
                      placeholder={t('admin.bots.form.namePlaceholder')}
                      required
                      icon={RobotIcon}
                    />
                  </div>

                  <div>
                    <TextField
                      label={t('admin.bots.form.descLabel')}
                      name="description"
                      value={formData.description}
                      onChange={handleChange}
                      placeholder={t('admin.bots.form.descPlaceholder')}
                      icon={NotebookIcon}
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Select
                        id="provider-select"
                        label={t('admin.bots.form.providerLabel')}
                        name="provider_id"
                        value={formData.provider_id}
                        onChange={handleChange}
                        options={providers.map(p => ({ value: p.id, label: p.display_name }))}
                        placeholder={t('admin.bots.form.selectProvider')}
                        icon={CpuIcon}
                        required
                      />
                    </div>

                    <div>
                      <Select
                        id="model-select"
                        label={t('admin.bots.form.modelLabel')}
                        name="model_id"
                        value={formData.model_id}
                        onChange={handleChange}
                        required
                        disabled={!formData.provider_id || loadingOptions}
                        options={models.map(m => ({ value: m.id, label: m.name }))}
                        placeholder={t('admin.bots.form.selectModel')}
                        icon={CpuIcon}
                        loading={loadingOptions}
                      />
                    </div>
                  </div>

                  <div id="system-prompt-input" className="relative group space-y-3">
                    <label className="block text-sm font-bold text-primary-600 uppercase tracking-widest flex items-center gap-2">
                      <MagicWandIcon size={18} className="text-primary-500" />
                      {t('admin.bots.form.promptLabel')}
                    </label>

                    <div className="bg-primary-50/50 dark:bg-gray-800/50 rounded-xl p-4 border border-primary-100/50 dark:border-gray-700 flex gap-3">
                      <LightningIcon className="text-primary-500 shrink-0" size={20} />
                      <div>
                        <h5 className="font-bold text-primary-900 dark:text-primary-400 text-xs mb-0.5">{t('admin.bots.form.preview.tipTitle')}</h5>
                        <p className="text-xs text-primary-700 dark:text-gray-400 leading-relaxed">{t('admin.bots.form.preview.tipText')}</p>
                      </div>
                    </div>
                    <textarea
                      name="system_prompt"
                      value={formData.system_prompt}
                      onChange={handleChange}
                      rows="8"
                      required
                      placeholder={t('admin.bots.form.promptPlaceholder')}
                      className="input-field p-4"
                    ></textarea>
                  </div>

                  <div className="pt-4 flex justify-end gap-4 border-t border-gray-100 dark:border-gray-700">
                    <Button variant="secondary" onClick={() => navigate('/admin/bots')}>
                      {t('common.cancel')}
                    </Button>
                    <Button
                      id="save-bot-btn"
                      type="submit"
                      loading={processing}
                      icon={isEdit ? FloppyDiskIcon : ArrowRightIcon}
                      className="shadow-lg"
                    >
                      {isEdit ? t('common.saveChanges') : t('admin.bots.form.createContinue')}
                    </Button>
                  </div>
                </div>
              </div>

              {/* RIGHT COLUMN: CONFIGURATION */}
              <div className="lg:col-span-5">
                <div className="sticky top-6 space-y-6">

                  <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 shadow-sm border border-gray-100 dark:border-gray-700 space-y-6">
                    <div className="flex items-center gap-3 border-b border-gray-100 dark:border-gray-700 pb-4">
                      <div className="p-2 bg-primary-100 dark:bg-primary-900/30 rounded-xl">
                        <CpuIcon size={24} className="text-primary-600 dark:text-primary-400" />
                      </div>
                      <div>
                        <h3 className="font-bold text-gray-800 dark:text-white">{t('admin.bots.form.configuration.title')}</h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400">{t('admin.bots.form.configuration.subtitle')}</p>
                      </div>
                    </div>

                    {/* Temperature */}
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <label className="text-sm font-bold text-gray-700 dark:text-gray-300">{t('admin.bots.form.configuration.temperature')}</label>
                        <span className="text-xs font-mono bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded text-gray-600 dark:text-gray-300">{formData.config_model.temperature}</span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        name="temperature"
                        value={formData.config_model.temperature}
                        onChange={(e) => setFormData(prev => ({
                          ...prev,
                          config_model: { ...prev.config_model, temperature: parseFloat(e.target.value) }
                        }))}
                        className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary-600"
                      />
                      <p className="text-xs text-gray-500 dark:text-gray-400">{t('admin.bots.form.configuration.temperatureDesc')}</p>
                    </div>

                    {/* Top K */}
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <label className="text-sm font-bold text-gray-700 dark:text-gray-300">{t('admin.bots.form.configuration.topK')}</label>
                        <span className="text-xs font-mono bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded text-gray-600 dark:text-gray-300">{formData.config_model.top_k}</span>
                      </div>
                      <input
                        type="range"
                        min="1"
                        max="20"
                        step="1"
                        name="top_k"
                        value={formData.config_model.top_k}
                        onChange={(e) => setFormData(prev => ({
                          ...prev,
                          config_model: { ...prev.config_model, top_k: parseInt(e.target.value) }
                        }))}
                        className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary-600"
                      />
                      <p className="text-xs text-gray-500 dark:text-gray-400">{t('admin.bots.form.configuration.topKDesc')}</p>
                    </div>

                    {/* Reranking Toggle */}
                    <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-xl">
                      <div>
                        <label className="text-sm font-bold text-gray-800 dark:text-gray-200 block">{t('admin.bots.form.configuration.reranking')}</label>
                        <p className="text-xs text-gray-500 dark:text-gray-400">{t('admin.bots.form.configuration.rerankingDesc')}</p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.config_model.reranking_enable}
                          onChange={(e) => setFormData(prev => ({
                            ...prev,
                            config_model: { ...prev.config_model, reranking_enable: e.target.checked }
                          }))}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary-600"></div>
                      </label>
                    </div>

                    {/* Reranking Settings (Conditional) */}
                    {formData.config_model.reranking_enable && (
                      <div className="space-y-4 pt-2 animate-fadeIn">
                        <div>
                          <Select
                            label={t('admin.bots.form.configuration.rerankingModel')}
                            name="reranking_model"
                            value={formData.config_model.reranking_model || ''}
                            onChange={(e) => setFormData(prev => ({
                              ...prev,
                              config_model: { ...prev.config_model, reranking_model: e.target.value }
                            }))}
                            options={rerankers.map(m => ({ value: m.model_id, label: m.name }))}
                            placeholder={t('admin.bots.form.configuration.rerankingPlaceholder')}
                          />
                        </div>

                        <div className="space-y-3">
                          <div className="flex justify-between items-center">
                            <div className="flex items-center gap-2">
                              <input
                                type="checkbox"
                                checked={formData.config_model.score_threshold_enabled}
                                onChange={(e) => setFormData(prev => ({
                                  ...prev,
                                  config_model: { ...prev.config_model, score_threshold_enabled: e.target.checked }
                                }))}
                                className="rounded text-primary-600 focus:ring-primary-500"
                              />
                              <label className="text-sm font-bold text-gray-700 dark:text-gray-300">{t('admin.bots.form.configuration.scoreThreshold')}</label>

                            </div>
                            <span className="text-xs font-mono bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded text-gray-600 dark:text-gray-300">{formData.config_model.score_threshold}</span>
                          </div>

                          {formData.config_model.score_threshold_enabled && (
                            <input
                              type="range"
                              min="0"
                              max="1"
                              step="0.05"
                              value={formData.config_model.score_threshold}
                              onChange={(e) => setFormData(prev => ({
                                ...prev,
                                config_model: { ...prev.config_model, score_threshold: parseFloat(e.target.value) }
                              }))}
                              className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary-600"
                            />
                          )}
                        </div>
                      </div>
                    )}

                  </div>
                </div>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default BotForm;
