import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import ProviderList from './ProviderList';
import ModelList from './ModelList';
import { SquaresFour, Cube } from '@phosphor-icons/react';
import clsx from 'clsx';


const AiProviderModelPage = () => {
  const { t } = useTranslation('ai-models');
  const [activeTab, setActiveTab] = useState('providers');

  const tabs = [
    { id: 'providers', label: t('providers.title'), icon: SquaresFour },
    { id: 'models', label: t('models.title'), icon: Cube },
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white capitalize">
            {t('title')}
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Manage your AI providers and available models.
          </p>
        </div>
      </div>

      <div className="flex space-x-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-xl w-fit">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={clsx(
                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                activeTab === tab.id
                  ? 'bg-white dark:bg-gray-700 text-primary-600 dark:text-primary-400 shadow-sm'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
              )}
            >
              <Icon size={18} weight={activeTab === tab.id ? 'fill' : 'regular'} />
              {tab.label}
            </button>
          );
        })}
      </div>

      <div className="animate-fade-in-up">
        {activeTab === 'providers' ? <ProviderList /> : <ModelList />}
      </div>
    </div>
  );
};

export default AiProviderModelPage;
