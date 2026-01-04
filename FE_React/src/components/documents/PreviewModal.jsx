import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import DocViewer, { DocViewerRenderers } from '@cyntler/react-doc-viewer';
import { XIcon, DownloadSimpleIcon } from '@phosphor-icons/react';
import { useTranslation } from 'react-i18next';
import { renderAsync } from 'docx-preview';
import * as XLSX from 'xlsx';
import axios from 'axios';

const DocxViewer = ({ fileUrl }) => {
  const containerRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadDocx = async () => {
      try {
        setLoading(true);
        const response = await axios.get(fileUrl, { responseType: 'blob' });
        if (containerRef.current) {
          await renderAsync(response.data, containerRef.current, containerRef.current, {
            className: 'docx-viewer',
            inWrapper: true,
            ignoreWidth: false, // Keep false to respect page layout, modal width increase should handle it
            ignoreHeight: false,
            ignoreFonts: false,
            breakPages: true,
            ignoreLastRenderedPageBreak: true,
            experimental: false,
            trimXmlDeclaration: true,
            useBase64URL: false,
            useMathJax: false,
            renderChanges: false,
            debug: false,
          });
        }
        setLoading(false);
      } catch (err) {
        console.error("Error rendering DOCX:", err);
        setError("Failed to load DOCX preview.");
        setLoading(false);
      }
    };

    if (fileUrl) {
      loadDocx();
    }
  }, [fileUrl]);

  if (error) return <div className="flex items-center justify-center h-full text-red-500">{error}</div>;

  return (
    <div className="h-full w-full overflow-auto bg-gray-100 p-4 relative">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/50 z-10">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      )}
      <div ref={containerRef} className="bg-white shadow-sm min-h-full" />
    </div>
  );
};

const ExcelViewer = ({ fileUrl }) => {
  const [html, setHtml] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadExcel = async () => {
      try {
        setLoading(true);
        const response = await axios.get(fileUrl, { responseType: 'arraybuffer' });
        const workbook = XLSX.read(response.data, { type: 'array' });
        const firstSheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[firstSheetName];
        // Generate HTML table
        const htmlString = XLSX.utils.sheet_to_html(worksheet, { id: 'excel-table', editable: false });
        setHtml(htmlString);
        setLoading(false);
      } catch (err) {
        console.error("Error rendering Excel:", err);
        setError("Failed to load Excel preview.");
        setLoading(false);
      }
    };

    if (fileUrl) {
      loadExcel();
    }
  }, [fileUrl]);

  if (error) return <div className="flex items-center justify-center h-full text-red-500">{error}</div>;

  return (
    <div className="h-full w-full overflow-auto bg-white p-4 relative excel-preview-container">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/50 z-10">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      )}
      {/* Sanitize if dealing with untrusted content, but here we assume internal docs */}
      <div dangerouslySetInnerHTML={{ __html: html }} className="prose max-w-none" />
      <style>{`
        .excel-preview-container table { border-collapse: collapse; width: 100%; font-size: 14px; }
        .excel-preview-container th, .excel-preview-container td { border: 1px solid #e5e7eb; padding: 4px 8px; text-align: left; }
        .excel-preview-container th { bg-color: #f9fafb; font-weight: 600; }
      `}</style>
    </div>
  );
};

const PreviewModal = ({ isOpen, onClose, fileUrl, fileName, fileAppType }) => {
  const { t } = useTranslation();

  if (!isOpen) return null;

  // Determine file type more robustly
  const getFileType = () => {
    if (fileAppType) return fileAppType;
    if (fileName) {
      const lowerName = fileName.toLowerCase();
      if (lowerName.endsWith('.pdf')) return 'pdf';
      if (lowerName.endsWith('.docx')) return 'docx';
      if (lowerName.endsWith('.xlsx') || lowerName.endsWith('.xls') || lowerName.endsWith('.csv')) return 'spreadsheets';
    }
    return '';
  };

  const currentFileType = getFileType();

  const renderContent = () => {
    if (!fileUrl) {
      return (
        <div className="flex items-center justify-center h-full text-gray-500">
          {t('preview.loading', 'Loading preview...')}
        </div>
      );
    }

    if (currentFileType === 'docx') {
      return <DocxViewer fileUrl={fileUrl} />;
    }

    if (currentFileType === 'spreadsheets' || fileName?.endsWith('.xlsx') || fileName?.endsWith('.xls')) {
      return <ExcelViewer fileUrl={fileUrl} />;
    }

    if (currentFileType === 'pdf') {
      return (
        <iframe
          src={fileUrl}
          className="w-full h-full border-none"
          title={fileName}
        />
      );
    }

    const docs = [{ uri: fileUrl, fileType: currentFileType, fileName: fileName }];

    return (
      <DocViewer
        documents={docs}
        pluginRenderers={DocViewerRenderers}
        style={{ height: '100%', width: '100%' }}
        config={{
          header: {
            disableHeader: true,
            disableFileName: true,
            retainURLParams: false
          },
        }}
        theme={{
          primary: "#5296d8",
          secondary: "#f3f4f6",
          tertiary: "#5296d899",
          text_primary: "#000000",
          text_secondary: "#5296d8",
          text_tertiary: "#00000099",
          disableThemeScrollbar: false,
        }}
      />
    );
  };

  return createPortal(
    <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          aria-hidden="true"
          onClick={onClose}
        ></div>

        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

        <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-6xl sm:w-full">
          <div className="flex justify-between items-center px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
            <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white truncate max-w-[70%]" id="modal-title">
              {fileName}
            </h3>
            <div className="flex items-center gap-2">
              {fileUrl && (
                <a
                  href={fileUrl}
                  download
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-1 bg-white dark:bg-gray-800 rounded-md text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
                  title={t('common.download')}
                >
                  <DownloadSimpleIcon className="h-6 w-6" />
                </a>
              )}
              <button
                onClick={onClose}
                className="bg-white dark:bg-gray-800 rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <span className="sr-only">{t('common.close')}</span>
                <XIcon className="h-6 w-6" aria-hidden="true" />
              </button>
            </div>
          </div>

          <div className="bg-gray-100 dark:bg-gray-900 h-[70vh] w-full flex flex-col">
            {renderContent()}
          </div>
        </div>
      </div>
    </div>
    , document.body);
};

export default PreviewModal;
