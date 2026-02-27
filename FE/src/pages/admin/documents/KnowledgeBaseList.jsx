import React, { useState, useEffect } from 'react';
import CreateKBModal from '../../../components/documents/CreateKBModal';
import { useTranslation } from 'react-i18next';
import { useNavigate, useOutletContext } from 'react-router-dom';
import { ROUTES } from '../../../routes';
import { usePageTour } from '../../../hooks/usePageTour';
import TourButton from '../../../components/common/TourButton';
import {
  FolderIcon,
  FileIcon,
  MagnifyingGlassIcon,
  UploadSimpleIcon,
  PencilSimpleIcon,
  TrashIcon,
  WarningIcon,
  SpinnerIcon,
  FileDocIcon,
  FileTextIcon
} from '@phosphor-icons/react';
import { useDocuments } from '../../../hooks/useDocuments';
import { formatDate } from '../../../utils/formatters';
import { useKnowledgeBases } from '../../../hooks/useKnowledgeBases';

const KnowledgeBaseList = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  // Hooks
  const {
    kbs,
    loading: kbsLoading,
    error: kbsError,
    fetchKBs,
    deleteKB
  } = useKnowledgeBases();

  const { documents } = useDocuments();


  const { setTitle } = useOutletContext() || {};

  useEffect(() => {
    if (setTitle) {
      setTitle(t('admin.documents.list.kbSection', 'Knowledge Bases'));
    }
  }, [setTitle, t]);

  const [searchQuery, setSearchQuery] = useState('');

  const [isCreateKBModalOpen, setIsCreateKBModalOpen] = useState(false);
  const [kbToEdit, setKbToEdit] = useState(null);

  const loading = kbsLoading;
  const error = kbsError;

  const tourSteps = [
    { element: '#doc-header', popover: { title: t('tour.docs.title'), description: t('tour.docs.desc') } },
    { element: '#doc-search', popover: { title: t('tour.docs.search'), description: t('tour.docs.searchDesc') } },
    { element: '#upload-btn', popover: { title: t('tour.docs.upload'), description: t('tour.docs.uploadDesc') } },
    { element: '#doc-list', popover: { title: t('tour.docs.list'), description: t('tour.docs.listDesc') } }
  ];

  const { startTour } = usePageTour('doc-list', tourSteps);

  const loadItems = React.useCallback(async (signal) => {
    setSearchQuery('');
    try {
      const options = { signal };
      await fetchKBs(options);
    } catch (error) {
      if (signal?.aborted) return;
      console.error("Load failed:", error);
    }
  }, [fetchKBs]);

  // Load items on mount
  useEffect(() => {
    const controller = new AbortController();
    loadItems(controller.signal);
    return () => controller.abort();
  }, [loadItems]);

  const items = React.useMemo(() => kbs.map(kb => ({
    id: kb.id,
    name: kb.name,
    type: 'folder',
    description: kb.description || '--',
    document_count: kb.document_count || 0,
    embedding_model: kb.embedding_model_name || kb.embedding_model || '--',
    date_added: formatDate(kb.created_at),
    date_modified: formatDate(kb.updated_at),
  })), [kbs]);

  const handleNavigateTo = (item) => {
    navigate(ROUTES.ADMIN.DOCUMENTS.DETAIL(item.id), { state: { kbId: item.id, kbName: item.name } });
  };

  const handleEditKB = (kb, e) => {
    e.stopPropagation();
    setKbToEdit(kb);
    setIsCreateKBModalOpen(true);
  };

  const handleDeleteKB = async (kb, e) => {
    e.stopPropagation();
    if (!window.confirm(t('admin.documents.list.deleteConfirmKB', `Are you sure you want to delete knowledge base "${kb.name}"? This will delete all documents inside it.`))) {
      return;
    }

    try {
      await deleteKB(kb.id);
      await loadItems();
    } catch (err) {
      console.error("Failed to delete KB", err);
    }
  };

  const filteredItems = React.useMemo(() => {
    let result = [...items];
    if (searchQuery) {
      result = result.filter(item =>
        item.name.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    return result;
  }, [items, searchQuery]);

  return (
    <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden relative bg-gray-50 dark:bg-gray-900 transition-colors">

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-6">
        <div className="stats-card bg-white rounded-xl shadow-sm p-5 border border-gray-100 dark:bg-gray-800 dark:border-gray-700">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
              <FolderIcon size={24} />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500 dark:text-gray-400">{t('admin.documents.list.stats.kb', 'Total Knowledge Bases')}</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{kbs.length}</p>
            </div>
          </div>
        </div>

        <div className="stats-card bg-white rounded-xl shadow-sm p-5 border border-gray-100 dark:bg-gray-800 dark:border-gray-700/50 transition-all hover:shadow-md hover:ring-1 hover:ring-primary-500/30">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400">
              <FileIcon size={24} />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500 dark:text-gray-400">{t('admin.documents.list.stats.documents', 'Total Documents')}</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {kbs.reduce((acc, kb) => acc + (kb.document_count || 0), 0)}
              </p>
            </div>
          </div>
        </div>

        <div className="stats-card bg-white rounded-xl shadow-sm p-5 border border-gray-100 dark:bg-gray-800 dark:border-gray-700/50 transition-all hover:shadow-md hover:ring-1 hover:ring-primary-500/30">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400">
              <FileDocIcon size={24} />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500 dark:text-gray-400">{t('admin.documents.list.stats.pdfs', 'Total PDFs')}</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {documents.filter(doc => doc.name.toLowerCase().endsWith('.pdf')).length}
              </p>
            </div>
          </div>
        </div>

        <div className="stats-card bg-white rounded-xl shadow-sm p-5 border border-gray-100 dark:bg-gray-800 dark:border-gray-700/50 transition-all hover:shadow-md hover:ring-1 hover:ring-primary-500/30">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400">
              <FileTextIcon size={24} />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500 dark:text-gray-400">{t('admin.documents.list.stats.text', 'Text Files')}</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {documents.filter(doc => doc.name.toLowerCase().endsWith('.txt')).length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* File List */}
      <div id="doc-list" className="flex-1 flex flex-col min-h-0">
        <div className="flex flex-col min-h-0 h-full">
          <div className="px-6 pt-2 pb-4 shrink-0 flex items-center justify-between">
            <h2 id="doc-header" className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-3">
              {t('admin.documents.list.kbSection', 'Knowledge Bases')}
              <TourButton startTour={startTour} />
            </h2>
            <div className="flex items-center gap-3">
              <div className="relative">
                <MagnifyingGlassIcon size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  id="doc-search"
                  type="text"
                  placeholder={t('admin.documents.list.searchPlaceholder')}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 pr-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm w-64 focus:ring-2 focus:ring-primary-500 text-gray-900 dark:text-white shadow-sm"
                />
              </div>
              <button
                id="upload-btn"
                onClick={() => setIsCreateKBModalOpen(true)}
                className="btn-primary flex items-center gap-2"
              >
                <UploadSimpleIcon size={20} />
                <span className="hidden sm:inline">{t('admin.documents.list.new')}</span>
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-auto px-6 pb-6 pt-2">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-20">
                <SpinnerIcon size={32} className="animate-spin text-primary-600 mb-3" />
                <span className="text-sm font-medium text-gray-600 dark:text-gray-300">{t('common.processing')}</span>
              </div>
            ) : error ? (
              <div className="flex flex-col items-center gap-3 py-12 bg-red-50 dark:bg-red-900/10 rounded-lg mx-6">
                <WarningIcon size={40} className="text-red-600 dark:text-red-400" />
                <div className="space-y-1">
                  <p className="font-semibold text-gray-800 dark:text-slate-200">{t('common.errorOccurred')}</p>
                  <p className="text-sm text-red-600 dark:text-red-400 max-w-md mx-auto">{error?.message || String(error)}</p>
                </div>
                <button
                  onClick={loadItems}
                  className="mt-4 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-all"
                >
                  {t('common.retry', 'Try Again')}
                </button>
              </div>
            ) : filteredItems.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-700 mb-4">
                  <FolderIcon size={32} className="text-gray-400" />
                </div>
                <p className="text-gray-500 dark:text-gray-400">{t('admin.documents.list.empty')}</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {filteredItems.map((kb) => (
                  <div key={kb.id} onClick={() => handleNavigateTo(kb)} className="card-hover bg-white dark:bg-gray-800 rounded-xl shadow-sm p-5 border border-gray-100 dark:border-gray-700/50 overflow-hidden transition-all duration-200 cursor-pointer hover:shadow-md hover:-translate-y-1 hover:bg-gray-50 dark:hover:bg-gray-700/50 hover:border-primary-500/50">
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex items-center">
                        <div className="folder-icon bg-gradient-to-br from-amber-400 to-amber-500 p-3 rounded-lg shadow-sm">
                          <FolderIcon size={24} className="text-white" />
                        </div>
                        <div className="ml-4">
                          <h3 className="font-bold text-gray-900 dark:text-white">{kb.name}</h3>
                          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 line-clamp-1" title={kb.description}>
                            {kb.description}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                      <div className="flex items-center text-gray-500 dark:text-gray-400">
                        <FileIcon size={16} className="mr-2 text-gray-400" />
                        <span>{kb.document_count} {t('admin.documents.list.documents')}</span>
                      </div>
                      <div className="flex items-center text-gray-500 dark:text-gray-400">
                        <FolderIcon size={16} className="mr-2 text-gray-400" />
                        <span className="truncate" title={kb.embedding_model}>{kb.embedding_model}</span>
                      </div>
                    </div>

                    <div className="mt-4 flex justify-between items-center">
                      <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                        <span className="text-xs">{t('admin.documents.list.updated')}: {kb.date_modified}</span>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={(e) => handleEditKB(kb, e)}
                          className="p-2 text-gray-500 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg transition-colors"
                          title={t('common.edit')}
                        >
                          <PencilSimpleIcon size={16} />
                        </button>
                        <button
                          onClick={(e) => handleDeleteKB(kb, e)}
                          className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                          title={t('common.delete')}
                        >
                          <TrashIcon size={16} />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      <CreateKBModal
        isOpen={isCreateKBModalOpen}
        onClose={() => {
          setIsCreateKBModalOpen(false);
          setKbToEdit(null);
        }}
        onSuccess={() => {
          loadItems(); // Refresh the list
        }}
        initialData={kbToEdit}
      />
    </div >
  );
};

export default KnowledgeBaseList;
