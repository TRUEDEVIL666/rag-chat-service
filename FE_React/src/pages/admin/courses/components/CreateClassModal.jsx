import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Select from 'react-select';
import { useTheme } from '../../../../context/ThemeContext';

const CreateClassModal = ({ isOpen, onClose, onCreate, instructors = [] }) => {
  const { t } = useTranslation();
  const { theme } = useTheme();
  const [section, setSection] = useState('');
  const [selectedInstructor, setSelectedInstructor] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Prepare options for React Select
  const instructorOptions = instructors.map(inst => ({
    value: inst.id,
    label: `${inst.email} (${inst.user_metadata?.full_name || inst.full_name || t('common.no_name', 'No Name')})`
  }));

  // Reset form when opened
  useEffect(() => {
    if (isOpen) {
      setSection('');
      setSelectedInstructor(null);

      // Auto-select first instructor if available and none selected? 
      // Maybe not for select box, better explicit.
      if (instructorOptions.length > 0) {
        setSelectedInstructor(instructorOptions[0]);
      }

      setIsSubmitting(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedInstructor) return;

    setIsSubmitting(true);
    try {
      await onCreate({
        section,
        instructor_id: selectedInstructor.value
      });
      onClose();
    } catch (error) {
      console.error(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Custom styles for React Select to match Tailwind
  const isDark = theme === 'dark';
  const customStyles = {
    control: (provided, state) => ({
      ...provided,
      borderColor: state.isFocused
        ? '#3b82f6'
        : isDark ? '#4b5563' : '#e5e7eb', // gray-600 : gray-200
      borderRadius: '0.5rem',
      padding: '2px',
      boxShadow: state.isFocused ? '0 0 0 1px #3b82f6' : 'none',
      ':hover': {
        borderColor: isDark ? '#6b7280' : '#9ca3af', // gray-500 : gray-400
      },
      backgroundColor: isDark ? '#374151' : 'white', // gray-700
      color: isDark ? '#f3f4f6' : '#111827', // gray-100 : gray-900
    }),
    menu: (provided) => ({
      ...provided,
      zIndex: 9999,
      backgroundColor: isDark ? '#374151' : 'white',
      border: isDark ? '1px solid #4b5563' : '1px solid #e5e7eb',
    }),
    option: (provided, state) => ({
      ...provided,
      backgroundColor: state.isSelected
        ? '#3b82f6'
        : state.isFocused
          ? (isDark ? '#4b5563' : '#e5e7eb') // gray-600 : gray-200
          : 'transparent',
      color: state.isSelected
        ? 'white'
        : isDark ? '#f3f4f6' : '#111827',
      ':active': {
        backgroundColor: state.isSelected ? '#3b82f6' : (isDark ? '#4b5563' : '#e5e7eb'),
      }
    }),
    singleValue: (provided) => ({
      ...provided,
      color: isDark ? '#f3f4f6' : '#111827',
    }),
    input: (provided) => ({
      ...provided,
      color: isDark ? '#f3f4f6' : '#111827',
    }),
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-md w-full p-6 animate-in fade-in zoom-in duration-200">
        <h3 className="text-lg font-bold mb-4">{t('courses.class.create', "Create Class")}</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">{t('courses.class.section', 'Section')} (e.g., "L01")</label>
            <input
              type="text" required
              className="w-full rounded-lg border dark:bg-gray-700 dark:border-gray-600 p-2.5"
              value={section} onChange={e => setSection(e.target.value)}
              placeholder={t('courses.class.section_placeholder', 'e.g. L01')}
              disabled={isSubmitting}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">{t('courses.class.instructor', 'Instructor')}</label>
            <Select
              className="basic-single"
              classNamePrefix="select"
              value={selectedInstructor}
              onChange={setSelectedInstructor}
              options={instructorOptions}
              itemLoading={false}
              placeholder={t('courses.class.select_instructor', 'Select Instructor...')}
              required
              styles={customStyles}
              isDisabled={isSubmitting}
            />
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

export default CreateClassModal;
