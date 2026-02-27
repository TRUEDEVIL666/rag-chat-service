import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-hot-toast';

const CreateSemesterModal = ({ isOpen, onClose, onCreate }) => {
  const { t } = useTranslation();
  const [name, setName] = useState('');
  const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(
    new Date(new Date().setMonth(new Date().getMonth() + 3)).toISOString().split('T')[0]
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await onCreate({ name, start_date: startDate, end_date: endDate });
      setName(''); // Reset form
      onClose();
    } catch (error) {
      console.error(error);
      // Toast is handled by parent or service usually, but good to have fallback
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-md w-full p-6 animate-in fade-in zoom-in duration-200">
        <h3 className="text-lg font-bold mb-4">{t('courses.form.createSemesterTitle', 'Create Semester')}</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">{t('courses.form.semesterNameLabel', 'Semester Name')} (e.g., "Fall 2024")</label>
            <input
              type="text" required
              className="w-full rounded-lg border dark:bg-gray-700 dark:border-gray-600 p-2.5"
              value={name} onChange={e => setName(e.target.value)}
              disabled={isSubmitting}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Start Date</label>
              <input
                type="date"
                className="w-full rounded-lg border dark:bg-gray-700 dark:border-gray-600 p-2.5"
                value={startDate} onChange={e => setStartDate(e.target.value)}
                disabled={isSubmitting}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">End Date</label>
              <input
                type="date"
                className="w-full rounded-lg border dark:bg-gray-700 dark:border-gray-600 p-2.5"
                value={endDate} onChange={e => setEndDate(e.target.value)}
                disabled={isSubmitting}
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-500 hover:bg-gray-100 rounded-lg"
              disabled={isSubmitting}
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? t('common.processing', 'Processing...') : t('common.create')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateSemesterModal;
