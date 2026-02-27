import React from 'react';
import { Question } from '@phosphor-icons/react';
import Button from '../Button'; // Assuming generic button is in sibling folder or adjust import
import { useTranslation } from 'react-i18next';

const TourButton = ({ startTour }) => {
  const { t } = useTranslation();

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={startTour}
      title={t('common.startTour', 'Start Tour')}
      className="!p-2 text-gray-500 hover:text-primary-600 dark:text-gray-400 dark:hover:text-primary-400"
    >
      <Question size={24} weight="duotone" />
    </Button>
  );
};

export default TourButton;
