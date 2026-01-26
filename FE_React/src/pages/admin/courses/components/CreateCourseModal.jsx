import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Select from 'react-select';
import { kbsService } from '../../../../services/kbsService';
import { toast } from 'react-hot-toast';
import { useTheme } from '../../../../context/ThemeContext'; // Import useTheme

const CreateCourseModal = ({ isOpen, onClose, onCreate, selectedSemester }) => {
  const { t } = useTranslation();
  const { theme } = useTheme(); // Get theme
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [selectedKbs, setSelectedKbs] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [availableKbs, setAvailableKbs] = useState([]);
  const [loadingKbs, setLoadingKbs] = useState(false);

  // Fetch KBs when opened
  useEffect(() => {
    if (isOpen) {
      setCode('');
      setName('');
      setSelectedKbs([]);
      setIsSubmitting(false);

      const fetchKbs = async () => {
        setLoadingKbs(true);
        try {
          const data = await kbsService.getKnowledgeBases();
          setAvailableKbs(Array.isArray(data) ? data : (data?.data || []));
        } catch (error) {
          console.error("Failed to load KBs", error);
          toast.error("Failed to load Knowledge Bases");
        } finally {
          setLoadingKbs(false);
        }
      };

      fetchKbs();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedSemester) return;

    setIsSubmitting(true);
    try {
      await onCreate({
        code,
        name,
        semester_id: selectedSemester.id,
        kb_ids: selectedKbs.map(opt => opt.value)
      });
      onClose();
    } catch (error) {
      console.error(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Convert KBs to options
  const kbOptions = availableKbs.map(kb => ({
    value: kb.id,
    label: kb.name
  }));

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
    multiValue: (provided) => ({
      ...provided,
      backgroundColor: isDark ? '#4b5563' : '#e5e7eb',
    }),
    multiValueLabel: (provided) => ({
      ...provided,
      color: isDark ? '#f3f4f6' : '#111827',
    }),
    multiValueRemove: (provided) => ({
      ...provided,
      color: isDark ? '#9ca3af' : '#6b7280',
      ':hover': {
        backgroundColor: isDark ? '#6b7280' : '#d1d5db',
        color: isDark ? '#f3f4f6' : '#111827',
      },
    }),
    input: (provided) => ({
      ...provided,
      color: isDark ? '#f3f4f6' : '#111827',
    }),
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-md w-full p-6 animate-in fade-in zoom-in duration-200">
        <h3 className="text-lg font-bold mb-4">{t('courses.form.createCourseTitle', 'Create Course')}</h3>
        <p className="text-sm text-gray-500 mb-4">{t('courses.form.semesterLabel')}: <b>{selectedSemester?.name}</b></p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">{t('courses.form.codeLabel')} (e.g., "CS101")</label>
            <input
              type="text" required
              className="w-full rounded-lg border dark:bg-gray-700 dark:border-gray-600 p-2.5"
              value={code} onChange={e => setCode(e.target.value)}
              placeholder={t('courses.form.codePlaceholder')}
              disabled={isSubmitting}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">{t('courses.form.nameLabel')}</label>
            <input
              type="text" required
              className="w-full rounded-lg border dark:bg-gray-700 dark:border-gray-600 p-2.5"
              value={name} onChange={e => setName(e.target.value)}
              placeholder={t('courses.form.namePlaceholder')}
              disabled={isSubmitting}
            />
          </div>

          {/* KB Selection with React Select */}
          <div>
            <label className="block text-sm font-medium mb-2">Knowledge Bases</label>
            <Select
              isMulti
              className="basic-multi-select"
              classNamePrefix="select"
              value={selectedKbs}
              onChange={setSelectedKbs}
              options={kbOptions}
              isLoading={loadingKbs}
              placeholder="Select Knowledge Bases..."
              styles={customStyles}
              isDisabled={isSubmitting}
              noOptionsMessage={() => loadingKbs ? "Loading..." : "No Knowledge Bases found"}
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

export default CreateCourseModal;
