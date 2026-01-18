import React, { useState, useEffect } from 'react';
import CreateKBModal from '../../../components/documents/CreateKBModal';
import PreviewModal from '../../../components/documents/PreviewModal';
import { documentService } from '../../../services/documentService';
import { useTranslation } from 'react-i18next';
import { useNavigate, useLocation } from 'react-router-dom';
import { usePageTour } from '../../../hooks/usePageTour';
import TourButton from '../../../components/common/TourButton';
import {
  FolderIcon,
  FilePdfIcon,
  FileDocIcon,
  FileTextIcon,
  FileIcon,
  MagnifyingGlassIcon,
  UploadSimpleIcon,
  CircleIcon,
  CheckCircleIcon,
  CaretDownIcon,
  SpinnerIcon,
  TrashIcon,
  WarningIcon,
  ArrowCounterClockwiseIcon,
  EyeIcon,
  DownloadSimpleIcon,
  PencilSimpleIcon
} from '@phosphor-icons/react';
import { clsx } from 'clsx';
import { formatDate, getExtension } from '../../../utils/formatters';
import { useDocuments } from '../../../hooks/useDocuments';
import { useKnowledgeBases } from '../../../hooks/useKnowledgeBases';

const DocumentList = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();

  // Hooks
  const {
    documents,
    loading: docsLoading,
    error: docsError,
    fetchDocuments,
    batchDeleteDocuments,
    retryDocument
  } = useDocuments();

  const {
    kbs,

    loading: kbsLoading,
    error: kbsError,
    fetchKBs,
    deleteKB
  } = useKnowledgeBases();

  const error = docsError || kbsError;


  const [items, setItems] = useState([]);
  const [currentPath, setCurrentPath] = useState([]); // Array of {id, name}
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedItems, setSelectedItems] = useState(new Set());
  const [highlightedDocId, setHighlightedDocId] = useState(null);
  const rowRefs = React.useRef({});
  const [sortConfig, setSortConfig] = useState({ key: 'name', direction: 'asc' });
  const [retryingIds, setRetryingIds] = useState(new Set());
  const [isDeleting, setIsDeleting] = useState(false);

  const [isCreateKBModalOpen, setIsCreateKBModalOpen] = useState(false);
  const [kbToEdit, setKbToEdit] = useState(null);

  // Preview State
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [previewFileUrl, setPreviewFileUrl] = useState('');
  const [previewFileName, setPreviewFileName] = useState('');
  const [previewFileAppType, setPreviewFileAppType] = useState('');

  const loading = docsLoading || kbsLoading || isDeleting;

  const tourSteps = [
    { element: '#doc-header', popover: { title: t('tour.docs.title'), description: t('tour.docs.desc') } },
    { element: '#doc-search', popover: { title: t('tour.docs.search'), description: t('tour.docs.searchDesc') } },
    { element: '#upload-btn', popover: { title: t('tour.docs.upload'), description: t('tour.docs.uploadDesc') } },
    { element: '#doc-list', popover: { title: t('tour.docs.list'), description: t('tour.docs.listDesc') } }
  ];

  const { startTour } = usePageTour('doc-list', tourSteps);

  // Load items on path change
  useEffect(() => {
    loadItems();
  }, [currentPath]);

  // Handle Deep Linking from Dashboard

  useEffect(() => {
    if (location.state?.kbId && location.state?.kbName) {
      setCurrentPath([{ id: location.state.kbId, name: location.state.kbName }]);

      if (location.state.docId) {
        setHighlightedDocId(location.state.docId);
        // Clear highlight after 3 seconds
        setTimeout(() => setHighlightedDocId(null), 3000);
      }

      // Clear state ensuring we don't re-trigger on refresh (optional but good practice)
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  // Scroll to highlighted item when items load
  useEffect(() => {
    if (highlightedDocId && rowRefs.current[highlightedDocId]) {
      rowRefs.current[highlightedDocId].scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [items, highlightedDocId]);

  // Sync state when hooks update
  useEffect(() => {
    if (currentPath.length === 0) {
      // Mapping Knowledge Bases
      const mappedKBs = kbs.map(kb => ({
        id: kb.id,
        name: kb.name,
        type: 'folder',
        description: kb.description || '--',
        document_count: kb.document_count || 0,
        embedding_model: kb.embedding_model_name || kb.embedding_model || '--',
        date_added: formatDate(kb.created_at),
        added_by: 'System',
        date_modified: formatDate(kb.updated_at),
        embedding_provider_id: kb.embedding_provider_id,
        embedding_model_id: kb.embedding_model_id,
      }));
      setItems(mappedKBs);
    } else {
      // Mapping Documents
      const mappedDocs = documents.map(doc => ({
        id: doc.id,
        name: doc.name,
        type: getExtension(doc.name) === 'pdf' ? 'pdf' : 'file',
        ext: getExtension(doc.name), // Added ext for getFileIcon
        size: doc.size ? formatBytes(doc.size) : '--',
        chunk_count: doc.chunk_count || 0,
        date_added: formatDate(doc.created_at),
        date_modified: formatDate(doc.updated_at),
        added_by: doc.creator?.name || doc.created_by || 'System', // Use actual creator if available
        status: doc.status || 'unknown', // Use actual status if available
      }));
      setItems(mappedDocs);
    }
  }, [kbs, documents, currentPath]);

  const loadItems = async () => {
    setSearchQuery('');
    setSelectedItems(new Set());

    try {
      if (currentPath.length === 0) {
        await fetchKBs();
      } else {
        const currentFolder = currentPath[currentPath.length - 1];
        await fetchDocuments(currentFolder.id);
      }
    } catch (error) {
      console.error("Load failed:", error);
      setItems([]);
    }
  };

  // Helper helper
  const formatBytes = (bytes, decimals = 2) => {
    if (!+bytes) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
  };

  const handleNavigateUp = (index) => {
    if (index === -1) {
      setCurrentPath([]);
    } else {
      setCurrentPath(currentPath.slice(0, index + 1));
    }
  };

  const handleNavigateTo = (item) => {
    if (item.type === 'folder') {
      setCurrentPath([...currentPath, { id: item.id, name: item.name }]);
    } else {
      console.log("Opening file:", item.name);
      handlePreview(item);
    }
  };

  const toggleSelection = (id) => {
    const newSelected = new Set(selectedItems);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedItems(newSelected);
  };

  const handleDelete = async () => {
    if (selectedItems.size === 0) return;

    if (!window.confirm(t('admin.documents.list.deleteConfirm', { count: selectedItems.size }))) {
      return;
    }

    setIsDeleting(true);

    try {
      // Execute batch deletion
      await batchDeleteDocuments(Array.from(selectedItems));
      await loadItems();
    } catch (error) {
      console.error("Delete failed:", error);
      alert(t('admin.documents.list.deleteError'));
    } finally {
      setIsDeleting(false);
    }
  };

  const filteredItems = React.useMemo(() => {
    let result = [...items];

    // 1. Filter
    if (searchQuery) {
      result = result.filter(item =>
        item.name.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // 2. Filter out trashed/deleted items - Handled by Backend now
    // result = result.filter(item => item.status !== 'deleted');

    // 3. Sort
    if (sortConfig.key) {
      result.sort((a, b) => {
        if (a[sortConfig.key] < b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (a[sortConfig.key] > b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }

    return result;
  }, [items, searchQuery, sortConfig]);

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const SortIcon = ({ columnKey }) => {
    if (sortConfig.key !== columnKey) return <CaretDownIcon size={12} className="opacity-0 group-hover:opacity-50" />;
    return sortConfig.direction === 'asc'
      ? <CaretDownIcon size={12} className="transform rotate-180 text-primary-600" />
      : <CaretDownIcon size={12} className="text-primary-600" />;
  };

  // Helper functions used to be here (formatDate, getExtension, formatSize)
  // Now imported from src/utils/formatters.js

  const getFileIcon = (item) => {
    if (item.type === 'folder') {
      return (
        <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6">
          <path d="M2.5 11.5V6.5C2.5 5.39543 3.39543 4.5 4.5 4.5H9.5L11.5 6.5H19.5C20.6046 6.5 21.5 7.39543 21.5 8.5V11.5" stroke="#F59E0B" fill="#FCD34D" strokeWidth="0" />
          <path d="M2 10.5C2 9.39543 2.89543 8.5 4 8.5H20C21.1046 8.5 22 9.39543 22 10.5V18.5C22 19.6046 21.1046 20.5 20 20.5H4C2.89543 20.5 2 19.6046 2 18.5V10.5Z" fill="#FCD34D" stroke="#D97706" strokeWidth="0.5" />
        </svg>
      );
    }
    switch (item.ext) {
      case 'pdf': return <FilePdfIcon className="text-2xl text-red-500" weight="fill" />;
      case 'docx': return <FileDocIcon className="text-2xl text-primary-600" weight="fill" />;
      case 'txt': return <FileTextIcon className="text-2xl text-gray-500" weight="fill" />;
      default: return <FileIcon className="text-2xl text-gray-400" weight="fill" />;
    }
  };


  const handleRetry = async (docId, e) => {
    e.stopPropagation();
    setRetryingIds(prev => {
      const next = new Set(prev);
      next.add(docId);
      return next;
    });

    try {
      await retryDocument(docId);
      await loadItems();
    } catch (err) {
      console.error("Retry failed", err);
      // alert(t('list.retryError', 'Failed to retry document processing'));
    } finally {
      setRetryingIds(prev => {
        const next = new Set(prev);
        next.delete(docId);
        return next;
      });
    }
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
      // alert(t('admin.documents.list.deleteError'));
    }
  };

  const handlePreview = async (item) => {
    setPreviewFileName(item.name);
    setPreviewFileAppType(item.ext); // Pass extension or mime type if known
    setPreviewFileUrl(''); // Reset URL while loading
    setPreviewModalOpen(true);

    try {
      const url = await documentService.getDocumentDownloadUrl(item.id);
      setPreviewFileUrl(url);
    } catch (error) {
      console.error("Failed to get preview URL:", error);
      // Ideally show error in modal or toast
    }
  };

  const handleDownload = async (item, e) => {
    e.stopPropagation();
    try {
      const url = await documentService.getDocumentDownloadUrl(item.id);
      window.open(url, '_blank');
    } catch (error) {
      console.error("Failed to get download URL:", error);
      alert(t('common.errorOccurred'));
    }
  };


  return (
    <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden relative bg-white dark:bg-gray-900 transition-colors">

      {/* Top Navigation Bar */}
      <header className="px-6 py-2 border-b border-gray-100 dark:border-gray-700 flex flex-col gap-2 bg-white dark:bg-gray-800 transition-colors">
        {/* Breadcrumbs & Search */}
        <div className="flex items-center justify-between h-10">
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleNavigateUp(-1)}
              className="p-1.5 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-primary-600 rounded-md transition"
              title="Back to Root"
            >
              <FolderIcon size={18} weight={currentPath.length === 0 ? "fill" : "regular"} />
            </button>
            <div className="h-4 w-px bg-gray-300 dark:bg-gray-600 mx-1"></div>
            <div className="flex items-center text-sm font-medium text-gray-500 dark:text-gray-400 gap-2">
              <span
                className={clsx(
                  "hover:underline cursor-pointer transition-colors",
                  currentPath.length === 0 ? "font-bold text-gray-800 dark:text-white" : ""
                )}
                onClick={() => handleNavigateUp(-1)}
              >
                {t('admin.documents.list.title')}
              </span>
              {currentPath.map((item, index) => (
                <React.Fragment key={item.id}>
                  <span className="text-gray-300 dark:text-gray-600">/</span>
                  <span
                    className={clsx(
                      "hover:underline cursor-pointer transition-colors",
                      index === currentPath.length - 1 ? "font-bold text-gray-800 dark:text-white" : ""
                    )}
                    onClick={() => handleNavigateUp(index)}
                  >
                    {item.name}
                  </span>
                </React.Fragment>
              ))}
            </div>
          </div>
        </div>
      </header>
      <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-6 flex-shrink-0 z-20">
        <div className="flex items-center gap-3">
          <h1 id="doc-header" className="text-xl font-semibold text-gray-900 dark:text-white">
            {currentPath.length > 0 ? currentPath[currentPath.length - 1].name : t('admin.documents.list.title')}
          </h1>
          <TourButton startTour={startTour} />
        </div>
        <div className="flex items-center gap-3">
          {selectedItems.size > 0 && (
            <button
              onClick={handleDelete} // Changed from handleDeleteSelected to handleDelete based on original code
              className="flex items-center gap-2 px-3 py-1.5 text-red-600 bg-red-50 hover:bg-red-100 rounded-lg text-sm font-medium transition"
            >
              <TrashIcon size={18} />
              <span>{t('common.delete')} ({selectedItems.size})</span>
            </button>
          )}

          <div className="relative">
            <MagnifyingGlassIcon size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              id="doc-search"
              type="text"
              placeholder={t('admin.documents.list.searchPlaceholder')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 pr-4 py-2 bg-gray-100 dark:bg-gray-700 border-none rounded-lg text-sm w-64 focus:ring-2 focus:ring-primary-500 text-gray-900 dark:text-white"
            />
          </div>

          <button
            id="upload-btn"
            onClick={() => {
              if (currentPath.length === 0) {
                setIsCreateKBModalOpen(true);
              } else {
                const currentKbId = currentPath[currentPath.length - 1].id;
                navigate('/admin/documents/upload', { state: { defaultKbId: currentKbId } });
              }
            }}
            className="btn-primary flex items-center gap-2"
          >
            <UploadSimpleIcon size={20} />
            <span className="hidden sm:inline">{t('admin.documents.list.new')}</span>
          </button>
        </div>
      </header>



      {/* Error Display */}
      {

      }

      {/* File List */}
      <div id="doc-list" className="flex-1 overflow-auto">
        <table className="w-full text-left text-sm border-collapse">
          <thead className="sticky top-0 bg-white dark:bg-gray-800 z-10 border-b border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 font-medium cursor-default">
            <tr>
              <th className="pl-4 pr-2 py-3 w-10 text-center"><CircleIcon size={18} className="opacity-0" /></th>
              <th className="px-2 py-3 w-8">{t('admin.documents.list.table.type')}</th>
              <th
                className="px-2 py-3 w-48 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer group"
                onClick={() => handleSort('name')}
              >
                <div className="flex items-center gap-1 select-none">
                  {t('admin.documents.list.table.name')} <SortIcon columnKey="name" />
                </div>
              </th>
              {currentPath.length > 0 && (
                <th
                  className="px-2 py-3 w-24 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer group"
                  onClick={() => handleSort('status')}
                >
                  <div className="flex items-center gap-1 select-none">
                    {t('admin.documents.list.table.status')} <SortIcon columnKey="status" />
                  </div>
                </th>
              )}
              {currentPath.length === 0 && (
                <th
                  className="px-2 py-3 w-64 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer group"
                  onClick={() => handleSort('description')}
                >
                  <div className="flex items-center gap-1 select-none">
                    {t('admin.documents.list.table.description')} <SortIcon columnKey="description" />
                  </div>
                </th>
              )}
              {currentPath.length === 0 && (
                <>
                  <th
                    className="px-2 py-3 w-32 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer group"
                    onClick={() => handleSort('document_count')}
                  >
                    <div className="flex items-center gap-1 select-none">
                      {t('admin.documents.list.table.documentCount')} <SortIcon columnKey="document_count" />
                    </div>
                  </th>
                  <th
                    className="px-2 py-3 w-48 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer group"
                    onClick={() => handleSort('embedding_model')}
                  >
                    <div className="flex items-center gap-1 select-none">
                      {t('admin.documents.list.table.embeddingModel')} <SortIcon columnKey="embedding_model" />
                    </div>
                  </th>
                </>
              )}
              <th
                className="px-2 py-3 w-24 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer group"
                onClick={() => handleSort('date_added')}
              >
                <div className="flex items-center gap-1 select-none">
                  {t('admin.documents.list.table.dateAdded')} <SortIcon columnKey="date_added" />
                </div>
              </th>
              <th
                className="px-2 py-3 w-28 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer group"
                onClick={() => handleSort('date_modified')}
              >
                <div className="flex items-center gap-1 select-none">
                  {t('list.table.dateModified')} <SortIcon columnKey="date_modified" />
                </div>
              </th>
              {currentPath.length > 0 && (
                <th
                  className="px-2 py-3 w-32 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer group"
                  onClick={() => handleSort('added_by')}
                >
                  <div className="flex items-center gap-1 select-none">
                    {t('admin.documents.list.table.addedBy')} <SortIcon columnKey="added_by" />
                  </div>
                </th>
              )}
              <th
                className="px-2 py-3 w-40 text-center">{t('admin.documents.list.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50 dark:divide-gray-800">
            {loading ? (
              <tr>
                <td colSpan="12" className="px-6 py-20 text-center text-gray-500">
                  <div className="flex flex-col items-center justify-center">
                    <SpinnerIcon size={32} className="animate-spin text-primary-600 mb-3" />
                    <span className="text-sm font-medium">{t('common.processing')}</span>
                  </div>
                </td>

              </tr>
            ) : error ? (
              <tr>
                <td colSpan="12" className="px-6 py-20 text-center text-red-500 bg-red-50 dark:bg-red-900/10 rounded-lg">
                  <div className="flex flex-col items-center gap-3">
                    <WarningIcon size={40} weight="duotone" className="text-red-600 dark:text-red-400" />
                    <div className="space-y-1">
                      <p className="font-semibold text-lg text-slate-800 dark:text-slate-200">{t('common.errorOccurred')}</p>
                      <p className="text-sm text-red-600 dark:text-red-400 max-w-md mx-auto">{error?.message || String(error)}</p>
                    </div>
                    <button
                      onClick={loadItems}
                      className="mt-4 px-4 py-2 bg-white dark:bg-gray-800 border border-slate-200 dark:border-gray-700 rounded-lg text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-primary-600 dark:hover:text-primary-400 shadow-sm transition-all"
                    >
                      {t('common.retry', 'Try Again')}
                    </button>
                  </div>
                </td>
              </tr>
            ) : filteredItems.length === 0 ? (
              <tr><td colSpan="7" className="text-center py-10 text-gray-500">{t('admin.documents.list.empty')}</td></tr>
            ) : (
              filteredItems.map(item => (
                <tr
                  key={item.id}
                  ref={el => rowRefs.current[item.id] = el}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleNavigateTo(item);
                  }}
                  className={clsx(
                    "group border-b border-transparent hover:border-gray-100 hover:bg-gray-50 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white transition-all duration-500 cursor-default text-gray-700 dark:text-gray-300",
                    selectedItems.has(item.id) && "bg-blue-50 dark:bg-blue-900/20",
                    highlightedDocId === item.id && "bg-yellow-100 dark:bg-yellow-900/40"
                  )}
                >
                  <td
                    className="pl-4 pr-2 py-2 text-center"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleSelection(item.id);
                    }}
                  >
                    <button className={clsx(
                      "focus:outline-none transition-colors",
                      selectedItems.has(item.id) ? "text-primary-600 dark:text-primary-400" : "text-gray-400 dark:text-gray-500 hover:text-primary-600 dark:hover:text-primary-400"
                    )}>
                      {selectedItems.has(item.id) ? <CheckCircleIcon size={20} weight="fill" /> : <CircleIcon size={20} />}
                    </button>
                  </td>
                  <td className="px-2 py-2">
                    <div className="flex items-center justify-center">
                      {getFileIcon(item)}
                    </div>
                  </td>
                  <td className="px-2 py-2 font-medium text-gray-900 dark:text-gray-200 group-hover:text-primary-700 dark:group-hover:text-primary-400 truncate max-w-[200px]" title={item.name}>
                    {item.name}
                  </td>
                  {currentPath.length === 0 && (
                    <td className="px-2 py-2 text-gray-500 dark:text-gray-400 text-xs sm:text-sm truncate max-w-[350px]" title={item.description}>
                      {item.description}
                    </td>
                  )}

                  {currentPath.length > 0 && (
                    <td className="px-2 py-2 text-gray-500 dark:text-gray-400 text-xs sm:text-sm capitalize">
                      <div className="flex items-center gap-2">
                        <span className={clsx(
                          item.status === 'error' || item.status === 'failed' || item.status === 'Error' ? "text-red-600 dark:text-red-400 font-medium" : ""
                        )}>
                          {item.status}
                        </span>
                        {(item.status === 'error' || item.status === 'failed' || item.status === 'Error') && (
                          <button
                            onClick={(e) => handleRetry(item.id, e)}
                            className="p-1 text-primary-600 hover:bg-primary-50 rounded-full transition-colors disabled:opacity-50"
                            title={t('list.retry', 'Retry processing')}
                            disabled={retryingIds.has(item.id)}
                          >
                            {retryingIds.has(item.id) ? (
                              <SpinnerIcon className="animate-spin" size={16} />
                            ) : (
                              <ArrowCounterClockwiseIcon size={16} />
                            )}
                          </button>
                        )}
                      </div>
                    </td>
                  )}
                  {currentPath.length === 0 && (
                    <>
                      <td className="px-2 py-2 text-gray-500 dark:text-gray-400 text-xs sm:text-sm">
                        {item.document_count}
                      </td>
                      <td className="px-2 py-2 text-gray-500 dark:text-gray-400 text-xs sm:text-sm truncate max-w-[150px]" title={item.embedding_model}>
                        {item.embedding_model}
                      </td>
                    </>
                  )}
                  <td className="px-2 py-2 text-gray-500 dark:text-gray-400 text-xs sm:text-sm whitespace-nowrap">
                    {item.date_added}
                  </td>
                  <td className="px-2 py-2 text-gray-500 dark:text-gray-400 text-xs sm:text-sm whitespace-nowrap">
                    {item.date_modified}
                  </td>
                  {currentPath.length > 0 && (
                    <td className="px-2 py-2 text-gray-500 dark:text-gray-400 text-xs sm:text-sm max-w-[150px] truncate" title={item.added_by}>
                      {item.added_by}
                    </td>
                  )}
                  {currentPath.length > 0 && (
                    <td className="px-2 py-2 text-center">
                      <div className="flex items-center justify-center gap-2">
                        {item.type !== 'folder' && (
                          <>
                            <button
                              onClick={(e) => { e.stopPropagation(); handlePreview(item); }}
                              className="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg transition-colors"
                              title={t('common.preview', 'Preview')}
                            >
                              <EyeIcon size={18} />
                            </button>
                            <button
                              onClick={(e) => handleDownload(item, e)}
                              className="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg transition-colors"
                              title={t('common.download', 'Download')}
                            >
                              <DownloadSimpleIcon size={18} />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                if (window.confirm(t('admin.documents.list.deleteConfirmSingle'))) {
                                  batchDeleteDocuments([item.id]);
                                  loadItems();
                                }
                              }}
                              className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                              title={t('common.delete', 'Delete')}
                            >
                              <TrashIcon size={18} />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  )}
                  {currentPath.length === 0 && (
                    <td className="px-2 py-2 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={(e) => handleEditKB(item, e)}
                          className="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg transition-colors"
                          title={t('common.edit', 'Edit')}
                        >
                          <PencilSimpleIcon size={18} />
                        </button>
                        <button
                          onClick={(e) => handleDeleteKB(item, e)}
                          className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                          title={t('common.delete', 'Delete')}
                        >
                          <TrashIcon size={18} />
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Bottom Buffer */}
        <div className="h-20"></div>
      </div>

      {/* Footer Status Bar */}
      <div className="bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-4 py-1 text-xs text-gray-500 dark:text-gray-400 flex justify-between items-center">
        <span>{t('admin.documents.list.footer.itemsCount', { count: filteredItems.length })}</span>
        <span>{t('admin.documents.list.footer.lastSynced')}: {t('common.justNow')}</span>
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
      <PreviewModal
        isOpen={previewModalOpen}
        onClose={() => setPreviewModalOpen(false)}
        fileUrl={previewFileUrl}
        fileName={previewFileName}
        fileAppType={previewFileAppType}
      />
    </div >

  );
};

export default DocumentList;
