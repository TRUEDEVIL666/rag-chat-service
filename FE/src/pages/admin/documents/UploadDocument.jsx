import { clsx } from 'clsx';
import {
  ArrowLeftIcon,
  CaretDownIcon,
  CheckCircleIcon,
  CloudArrowUpIcon,
  CodeBlockIcon,
  FileDashedIcon,
  FileTextIcon,
  FolderOpenIcon,
  GearIcon,
  InfoIcon,
  PaperPlaneTiltIcon,
  SpinnerIcon,
  TrashIcon,
} from '@phosphor-icons/react';
import { getDefaultParams } from '../../../utils/chunking';
import { formatBytes } from '../../../utils/formatters';
import { useDocuments } from '../../../hooks/useDocuments';
import { useKnowledgeBases } from '../../../hooks/useKnowledgeBases';
import { useLocation, useNavigate } from 'react-router-dom';
import { usePageTour } from '../../../hooks/usePageTour';
import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { ROUTES } from '../../../routes';
import TourButton from '../../../components/common/TourButton';

const UploadDocument = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { uploadDocuments } = useDocuments();
  const [isUploading, setIsUploading] = useState(false);
  const { kbs, loading: kbsLoading, error: kbsError, fetchKBs } = useKnowledgeBases();
  const { startTour } = usePageTour();

  const [selectedKb, setSelectedKb] = useState('default');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [enableExtraction, setEnableExtraction] = useState(true);
  const [chunkingMethod, setChunkingMethod] = useState('recursive');
  const [isDragging, setIsDragging] = useState(false);

  const [chunkSize, setChunkSize] = useState('');
  const [chunkOverlap, setChunkOverlap] = useState('');
  const [separator, setSeparator] = useState('');
  const [windowSize, setWindowSize] = useState('');
  const [thresholdPercentage, setThresholdPercentage] = useState('');
  const [bufferSize, setBufferSize] = useState('');
  const [chunkSizes, setChunkSizes] = useState('');
  const [msg, setMsg] = useState({ text: '', type: '' });
  const fileInputRef = useRef(null);

  const tourSteps = [
    { element: '#upload-header', popover: { title: t('tour.upload.title'), description: t('tour.upload.desc') } },
    { element: '#kb-select', popover: { title: t('tour.upload.kb'), description: t('tour.upload.kbDesc') } },
    { element: '#chunk-settings', popover: { title: t('tour.upload.chunk'), description: t('tour.upload.chunkDesc') } },
    { element: '#drop-zone', popover: { title: t('tour.upload.drop'), description: t('tour.upload.dropDesc') } },
    { element: '#start-upload-btn-top', popover: { title: t('tour.upload.start'), description: t('tour.upload.startDesc') } }
  ];

  useEffect(() => {
    fetchKBs();
  }, [fetchKBs]);

  useEffect(() => {
    // Set defaults when method changes
    const defaults = getDefaultParams(chunkingMethod);
    setChunkSize(defaults.chunkSize?.toString() ?? '');
    setChunkOverlap(defaults.chunkOverlap?.toString() ?? '');
    setSeparator(defaults.separator ?? '');
    setWindowSize(defaults.windowSize?.toString() ?? '');
    setThresholdPercentage(defaults.thresholdPercentage?.toString() ?? '');
    setBufferSize(defaults.bufferSize?.toString() ?? '');
    setChunkSizes(defaults.chunkSizes?.join(',') ?? '');
  }, [chunkingMethod]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const urlKbId = params.get('kbId');
    const stateKbId = location.state?.defaultKbId;

    if (urlKbId) {
      setSelectedKb(urlKbId);
    } else if (stateKbId) {
      setSelectedKb(stateKbId);
    } else if (kbs.length > 0 && selectedKb === 'default') {
      setSelectedKb(kbs[0].id);
    }
  }, [location, kbs, selectedKb]);

  const renderChunkingParams = () => {
    const inputClasses = "w-full px-4 py-2 mt-1.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all text-gray-800 dark:text-gray-200 text-sm";
    const labelClasses = "block text-xs font-semibold text-gray-500 dark:text-gray-400";

    switch (chunkingMethod) {
      case 'sentence':
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-5">
            <div>
              <label className={labelClasses}>{t('admin.documents.upload.chunking.params.chunkSize')}</label>
              <input type="number" value={chunkSize} onChange={e => setChunkSize(e.target.value)} placeholder="Default" className={inputClasses} />
            </div>
            <div>
              <label className={labelClasses}>{t('admin.documents.upload.chunking.params.chunkOverlap')}</label>
              <input type="number" value={chunkOverlap} onChange={e => setChunkOverlap(e.target.value)} placeholder="Default" className={inputClasses} />
            </div>
          </div>
        );
      case 'token':
      case 'word':
      case 'recursive':
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-5">
            <div>
              <label className={labelClasses}>{t('admin.documents.upload.chunking.params.chunkSize')}</label>
              <input type="number" value={chunkSize} onChange={e => setChunkSize(e.target.value)} className={inputClasses} />
            </div>
            <div>
              <label className={labelClasses}>{t('admin.documents.upload.chunking.params.chunkOverlap')}</label>
              <input type="number" value={chunkOverlap} onChange={e => setChunkOverlap(e.target.value)} className={inputClasses} />
            </div>
          </div>
        );
      case 'character':
        return (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-5">
            <div>
              <label className={labelClasses}>{t('admin.documents.upload.chunking.params.chunkSize')}</label>
              <input type="number" value={chunkSize} onChange={e => setChunkSize(e.target.value)} className={inputClasses} />
            </div>
            <div>
              <label className={labelClasses}>{t('admin.documents.upload.chunking.params.chunkOverlap')}</label>
              <input type="number" value={chunkOverlap} onChange={e => setChunkOverlap(e.target.value)} className={inputClasses} />
            </div>
            <div>
              <label className={labelClasses}>{t('admin.documents.upload.chunking.params.separator')}</label>
              <input type="text" value={separator} onChange={e => setSeparator(e.target.value)} className={inputClasses} />
            </div>
          </div>
        );
      case 'sliding':
        return (
          <div className="mt-5">
            <label className={labelClasses}>{t('admin.documents.upload.chunking.params.windowSize')}</label>
            <input type="number" value={windowSize} onChange={e => setWindowSize(e.target.value)} className={inputClasses} />
          </div>
        );
      case 'semantic':
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-5">
            <div>
              <label className={labelClasses}>{t('admin.documents.upload.chunking.params.bufferSize')}</label>
              <input type="number" value={bufferSize} onChange={e => setBufferSize(e.target.value)} className={inputClasses} />
            </div>
            <div>
              <label className={labelClasses}>{t('admin.documents.upload.chunking.params.thresholdPercentage')}</label>
              <input type="number" step="0.01" value={thresholdPercentage} onChange={e => setThresholdPercentage(e.target.value)} className={inputClasses} />
            </div>
          </div>
        );
      case 'hierarchical':
        return (
          <div className="mt-5">
            <label className={labelClasses}>{t('admin.documents.upload.chunking.params.chunkSizes')}</label>
            <input type="text" value={chunkSizes} onChange={e => setChunkSizes(e.target.value)} className={inputClasses} placeholder="e.g. 2000,500,100" />
            <p className="text-[11px] text-gray-500 mt-1.5 ml-1">Comma separated descending integers.</p>
          </div>
        );
      default:
        return null;
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files);
      setSelectedFiles(prev => {
        const existingNames = new Set(prev.map(f => f.name));
        const uniqueNewFiles = newFiles.filter(f => !existingNames.has(f.name));
        return [...prev, ...uniqueNewFiles];
      });
    }
  };

  const handleRemoveFile = (fileName) => {
    setSelectedFiles(prev => prev.filter(f => f.name !== fileName));
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files);
      setSelectedFiles(prev => {
        const existingNames = new Set(prev.map(f => f.name));
        const uniqueNewFiles = newFiles.filter(f => !existingNames.has(f.name));
        return [...prev, ...uniqueNewFiles];
      });
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (isUploading) return;

    if (selectedFiles.length === 0) {
      setMsg({ text: t('admin.documents.upload.alert.selectAtLeastOne'), type: "error" });
      return;
    }
    if (!selectedKb || selectedKb === 'default') {
      setMsg({ text: t('admin.documents.upload.alert.selectKb'), type: "error" });
      return;
    }

    const chunkingSettings = {
      method: chunkingMethod,
    };

    if (chunkSize) chunkingSettings.chunkSize = Number(chunkSize);
    if (chunkOverlap) chunkingSettings.chunkOverlap = Number(chunkOverlap);
    if (separator) chunkingSettings.separator = separator;
    if (windowSize) chunkingSettings.windowSize = Number(windowSize);
    if (thresholdPercentage) chunkingSettings.thresholdPercentage = Number(thresholdPercentage);
    if (bufferSize) chunkingSettings.bufferSize = Number(bufferSize);

    if (chunkingMethod === 'hierarchical' && chunkSizes) {
      try {
        const parsed = chunkSizes.split(',').map(s => Number(s.trim()));
        if (parsed.some(isNaN)) throw new Error('Invalid format');
        chunkingSettings.chunkSizes = parsed;

        let isValidOrder = true;
        for (let i = 0; i < parsed.length - 1; i++) {
          if (parsed[i] <= parsed[i + 1]) isValidOrder = false;
        }
        if (!isValidOrder) {
          setMsg({ text: t('admin.documents.upload.validation.hierarchicalOrder'), type: "error" });
          return;
        }
      } catch {
        setMsg({ text: t('admin.documents.upload.validation.invalidHierarchical'), type: "error" });
        return;
      }
    }

    setMsg({ text: '', type: '' });
    setIsUploading(true);
    try {
      // The hook expects (kbId, formData, onProgress)
      // We must construct the FormData as required by the backend
      const formData = new FormData();
      formData.append('kb_id', selectedKb);
      selectedFiles.forEach(file => formData.append('files', file));
      formData.append('enable_extraction', enableExtraction);
      formData.append('chunking_method', chunkingMethod);
      formData.append('chunking_settings', JSON.stringify(chunkingSettings));

      await uploadDocuments(selectedKb, formData);

      setMsg({ text: t('admin.documents.upload.alert.uploadSuccess', 'Upload successful! Redirecting...'), type: "success" });
      setSelectedFiles([]);
      if (fileInputRef.current) fileInputRef.current.value = "";

      // Redirect to the KB Document List after a brief delay so the user sees the success message
      setTimeout(() => {
        navigate(ROUTES.ADMIN.DOCUMENTS.DETAIL(selectedKb));
      }, 1500);
    } catch (err) {
      setMsg({ text: err.response?.data?.detail || err.message || t('admin.documents.upload.alert.uploadFailed'), type: "error" });
      setIsUploading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-slate-50 dark:bg-gray-900 font-sans text-gray-900 dark:text-gray-100">

      {/* HEADER: Clean & Integrated */}
      <header className="px-6 py-4 lg:px-10 lg:py-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shrink-0 transition-all">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(ROUTES.ADMIN.DOCUMENTS.LIST)}
            className="flex items-center justify-center w-10 h-10 rounded-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-500 hover:text-primary-600 dark:hover:text-primary-400 hover:border-primary-200 dark:hover:border-primary-900/50 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-all shadow-sm"
            title="Return to Hub"
          >
            <ArrowLeftIcon size={18} weight="bold" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 id="upload-header" className="text-xl md:text-2xl font-bold tracking-tight text-gray-900 dark:text-white">
                {t('admin.documents.upload.title', 'Upload Document')}
              </h1>
              <TourButton startTour={startTour} tourSteps={tourSteps} />
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 hidden sm:block">Upload and parse new knowledge distinctively.</p>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          {msg.text && (
            <span className={clsx("text-sm font-medium px-4 py-2 rounded-xl border flex items-center gap-2 shadow-sm",
              msg.type === 'error' ? 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800/50' :
                msg.type === 'success' ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-400 dark:border-emerald-800/50' :
                  'bg-white text-gray-700 border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700'
            )}>
              {msg.type === 'error' ? <InfoIcon weight="fill" /> : <CheckCircleIcon weight="fill" />}
              {msg.text}
            </span>
          )}

          <button
            id="start-upload-btn-top"
            onClick={handleSubmit}
            disabled={isUploading}
            className="px-6 py-2.5 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 disabled:dark:bg-gray-800 disabled:text-gray-500 text-white text-sm font-bold rounded-xl transition-all shadow-md hover:shadow-lg disabled:shadow-none flex items-center justify-center gap-2"
          >
            {isUploading ? (
              <SpinnerIcon size={18} className="animate-spin" />
            ) : (
              <PaperPlaneTiltIcon size={18} weight="bold" />
            )}
            {t('admin.documents.upload.startProcess', 'Upload & Process')}
          </button>
        </div>
      </header>

      {/* MAIN CONTENT: Balanced 7/5 Grid */}
      <div className="flex-1 px-6 pb-8 lg:px-10 max-w-[1600px] mx-auto w-full">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8 min-h-max">

          {/* LEFT COLUMN (7/12): Upload Dropzone Hero */}
          <div className="lg:col-span-7 flex flex-col min-h-[400px]">
            <div
              id="drop-zone"
              onDragEnter={handleDragEnter}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={clsx(
                "flex-1 bg-white dark:bg-gray-800 rounded-3xl shadow-sm border transition-all flex flex-col overflow-hidden relative group/dropzone",
                isDragging
                  ? "border-primary-500 ring-4 ring-primary-500/20 dark:ring-primary-500/10 scale-[1.01]"
                  : "border-gray-200 dark:border-gray-700 hover:border-primary-400 dark:hover:border-primary-500/50 hover:shadow-md"
              )}
            >
              <input
                type="file"
                ref={fileInputRef}
                multiple
                className="hidden"
                accept=".pdf,.docx,.pptx,.txt,.md,.html,.xlsx,.jpg,.jpeg,.png,.bmp,.tiff"
                onChange={handleFileChange}
              />

              {/* Decorative Background Blob */}
              <div className="absolute top-0 right-0 -mt-20 -mr-20 w-64 h-64 bg-primary-100 dark:bg-primary-900/20 rounded-full blur-3xl opacity-50 dark:opacity-40 transition-opacity group-hover/dropzone:opacity-100 pointer-events-none"></div>

              {selectedFiles.length === 0 ? (
                <div
                  className="flex-1 flex flex-col items-center justify-center text-center p-12 cursor-pointer z-10"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <div className={clsx("w-20 h-20 rounded-2xl flex items-center justify-center mb-6 transition-all duration-300",
                    isDragging ? "bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 scale-110" : "bg-gray-50 dark:bg-gray-900 text-gray-400 dark:text-gray-500 group-hover/dropzone:bg-primary-50 dark:group-hover/dropzone:bg-primary-900/20 group-hover/dropzone:text-primary-500"
                  )}>
                    <CloudArrowUpIcon size={40} weight={isDragging ? "fill" : "light"} />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                    {t('admin.documents.upload.dragDrop', 'Drag and drop files to attach')}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400 max-w-sm mb-8">
                    {t('admin.documents.upload.supportedFormats', 'Text, Word, PDF, Excel, and Images are supported.')}
                  </p>
                  <button
                    type="button"
                    className="px-6 py-2.5 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-xl font-semibold text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 transition shadow-sm"
                  >
                    {t('admin.documents.upload.selectFromComputer', 'Browse Files')}
                  </button>
                </div>
              ) : (
                <div className="flex flex-col h-full w-full z-10 p-6 md:p-8">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                      <FileDashedIcon size={24} className="text-primary-500" weight="duotone" />
                      Selected Documents
                    </h3>
                    <span className="bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400 text-xs font-bold px-3 py-1 rounded-full">
                      {selectedFiles.length} file{selectedFiles.length !== 1 && 's'}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 gap-3 auto-rows-max overflow-y-auto pr-2 custom-scrollbar flex-1 mb-6">
                    {selectedFiles.map((file, idx) => (
                      <div key={`${file.name}-${idx}`} className="flex items-center p-3 sm:p-4 bg-gray-50 dark:bg-gray-900/50 border border-gray-100 dark:border-gray-800 rounded-2xl group hover:border-gray-300 dark:hover:border-gray-700 transition-all">
                        <div className="w-10 h-10 rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 flex items-center justify-center shrink-0 mr-4">
                          <FileTextIcon size={20} className="text-gray-500 dark:text-gray-400" weight="fill" />
                        </div>
                        <div className="flex-1 min-w-0 pr-4">
                          <p className="text-sm font-semibold text-gray-900 dark:text-white truncate" title={file.name}>{file.name}</p>
                          <p className="text-[11px] font-medium text-gray-500 uppercase tracking-wider mt-0.5">{formatBytes(file.size)}</p>
                        </div>
                        <button
                          type="button"
                          onClick={(e) => { e.stopPropagation(); handleRemoveFile(file.name); }}
                          className="w-8 h-8 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center justify-center shrink-0 opacity-100 sm:opacity-0 group-hover:opacity-100 transition-all"
                          title="Remove file"
                        >
                          <TrashIcon size={16} weight="bold" />
                        </button>
                      </div>
                    ))}
                  </div>

                  <div className="mt-auto">
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="w-full py-4 border-2 border-dashed border-gray-200 dark:border-gray-700 rounded-2xl text-sm font-bold text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 hover:border-primary-400 dark:hover:border-primary-500 hover:bg-primary-50/50 dark:hover:bg-primary-900/10 transition-all"
                    >
                      + {t('admin.documents.upload.addMore', 'Attach More Files')}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* RIGHT COLUMN (5/12): Structured Configuration Stack */}
          <div className="lg:col-span-5 flex flex-col gap-6">

            {/* Target KB Card */}
            <div id="kb-select" className="bg-white dark:bg-gray-800 rounded-3xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 md:p-8 relative overflow-hidden">
              <div className="flex items-start gap-4 mb-5 relative z-10">
                <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center shrink-0 border border-blue-100 dark:border-blue-800/50">
                  <FolderOpenIcon size={20} className="text-blue-600 dark:text-blue-400" weight="duotone" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-gray-900 dark:text-white">{t('admin.documents.upload.storage.title', 'Storage Destination')}</h2>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 leading-relaxed">{t('admin.documents.upload.storage.desc', 'Select the Knowledge Base to index these documents within.')}</p>
                </div>
              </div>

              <div className="relative z-10">
                <select
                  value={selectedKb}
                  onChange={(e) => setSelectedKb(e.target.value)}
                  className="w-full pl-4 pr-10 py-3 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 appearance-none font-semibold text-gray-800 dark:text-gray-200 cursor-pointer transition-colors shadow-sm text-sm"
                >
                  {kbs.length === 0 ? (
                    <option value="default" disabled>{kbsLoading ? t('admin.documents.upload.storage.loading', 'Loading databases...') : t('admin.documents.upload.storage.empty', 'No Knowledge Bases Found')}</option>
                  ) : (
                    kbs.map(kb => (
                      <option key={kb.id} value={kb.id}>{kb.name}</option>
                    ))
                  )}
                </select>
                <CaretDownIcon size={16} weight="bold" className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
              </div>

              {selectedKb && selectedKb !== 'default' && kbs.find(kb => kb.id === selectedKb)?.embedding_model && (
                <div className="mt-3 flex items-center gap-1.5 px-3 py-2 bg-gray-50/50 dark:bg-gray-900/40 rounded-lg border border-gray-100 dark:border-gray-700/50 relative z-10 w-fit">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0"></span>
                  <p className="text-[11px] font-medium text-gray-600 dark:text-gray-400">
                    {t('admin.documents.upload.usingModel', { model: kbs.find(kb => kb.id === selectedKb).embedding_model })}
                  </p>
                </div>
              )}
              {kbsError && (
                <div className="mt-3 p-3 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-xs font-semibold rounded-lg flex items-start gap-2 border border-red-100 dark:border-red-800/50 z-10 relative">
                  <InfoIcon size={16} className="shrink-0 mt-0.5" />
                  <span>{kbsError.message || String(kbsError)}</span>
                </div>
              )}
            </div>

            {/* Ingestion Settings Card */}
            <div id="chunk-settings" className="flex-1 bg-white dark:bg-gray-800 rounded-3xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 md:p-8 flex flex-col">
              <div className="flex items-start gap-4 mb-6">
                <div className="w-10 h-10 rounded-xl bg-purple-50 dark:bg-purple-900/20 flex items-center justify-center shrink-0 border border-purple-100 dark:border-purple-800/50">
                  <GearIcon size={20} className="text-purple-600 dark:text-purple-400" weight="duotone" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-gray-900 dark:text-white">{t('admin.documents.upload.settings.title', 'Ingestion Settings')}</h2>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 leading-relaxed">{t('admin.documents.upload.settings.desc', 'Configure how data is parsed and segmented.')}</p>
                </div>
              </div>

              {/* Extraction Toggle */}
              <label className="flex items-center justify-between p-4 mb-6 bg-gray-50 dark:bg-gray-900/50 border border-gray-100 dark:border-gray-700/50 rounded-2xl cursor-pointer group hover:border-primary-200 dark:hover:border-primary-800 transition-colors">
                <div className="pr-4">
                  <span className="block text-sm font-bold text-gray-900 dark:text-white mb-0.5">{t('admin.documents.upload.extraction.title', 'Entity Extraction')}</span>
                  <span className="block text-xs text-gray-500 dark:text-gray-400">{t('admin.documents.upload.extraction.desc', 'Isolate Key Persons, Locations, and Organizations via NLP.')}</span>
                </div>
                <div className={clsx("w-12 h-6 rounded-full shrink-0 relative transition-colors border", enableExtraction ? "bg-primary-500 border-primary-600" : "bg-gray-200 dark:bg-gray-700 border-gray-300 dark:border-gray-600")}>
                  <div className={clsx("absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform", enableExtraction ? "translate-x-6" : "translate-x-0")}></div>
                </div>
                <input
                  type="checkbox"
                  className="hidden"
                  checked={enableExtraction}
                  onChange={(e) => setEnableExtraction(e.target.checked)}
                />
              </label>

              {/* Chunking UI */}
              <div className="flex-1 flex flex-col">
                <label className="block text-sm font-bold text-gray-900 dark:text-white mb-3">{t('admin.documents.upload.algorithm.title', 'Parsing Algorithm')}</label>
                <div className="relative mb-5">
                  <select
                    value={chunkingMethod}
                    onChange={(e) => setChunkingMethod(e.target.value)}
                    className="w-full pl-4 pr-10 py-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 appearance-none font-semibold text-gray-800 dark:text-gray-200 cursor-pointer shadow-sm text-sm"
                  >
                    <option value="sentence">{t('admin.documents.upload.chunking.sentence')}</option>
                    <option value="semantic">{t('admin.documents.upload.chunking.semantic')}</option>
                    <option value="token">{t('admin.documents.upload.chunking.token')}</option>
                    <option value="character">{t('admin.documents.upload.chunking.character')}</option>
                    <option value="word">{t('admin.documents.upload.chunking.word')}</option>
                    <option value="recursive">{t('admin.documents.upload.chunking.recursive')}</option>
                    <option value="hierarchical">{t('admin.documents.upload.chunking.hierarchical')}</option>
                    <option value="sliding">{t('admin.documents.upload.chunking.sliding')}</option>
                  </select>
                  <CaretDownIcon size={16} weight="bold" className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                </div>

                <div className="bg-gray-50/50 dark:bg-gray-900/30 border border-gray-100 dark:border-gray-700/50 rounded-2xl p-4 mb-4">
                  <h4 className="text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                    {t(`admin.documents.upload.chunking.info.${chunkingMethod}.title`)}
                  </h4>
                  <p className="text-[11px] text-gray-500 dark:text-gray-400 leading-relaxed mb-3">
                    {t(`admin.documents.upload.chunking.info.${chunkingMethod}.desc`)}
                  </p>
                  <div className="inline-flex m-0 text-[10px] font-bold uppercase tracking-wider text-primary-600 bg-primary-50 dark:text-primary-400 dark:bg-primary-900/30 px-2.5 py-1 rounded-lg">
                    Best for: {t(`admin.documents.upload.chunking.info.${chunkingMethod}.usage`)}
                  </div>
                </div>

                <div className="border-t border-gray-100 dark:border-gray-700/50 pt-2 flex-1">
                  {renderChunkingParams()}
                </div>
              </div>
            </div>

          </div>
        </div>

      </div>
    </div>
  );
};

export default UploadDocument;
