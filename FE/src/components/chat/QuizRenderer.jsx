import React, { useState, useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  CheckCircleIcon,
  XCircleIcon,
  PlayIcon,
  TableIcon,
  DownloadIcon,
  ArrowLeftIcon
} from '@phosphor-icons/react';

import { quizService } from '../../services/quizService';
import { toast } from 'react-hot-toast';

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Check if an answer is correct using index-based or text-based matching
 * Supports both new format (index 0-3) and legacy format (text)
 */
const isAnswerCorrect = (question, optionIndex) => {
  const { correct_answer, options = [] } = question;

  // New format: index (0-3)
  if (typeof correct_answer === 'number') {
    return correct_answer === optionIndex;
  }

  // Legacy format: text matching
  const optionText = options[optionIndex];
  if (!optionText) return false;

  const answer = (correct_answer || "").trim();
  if (!answer) return false;

  // Exact match
  if (answer === optionText) return true;

  // Letter matching (A, B, C, D)
  const letter = String.fromCharCode(65 + optionIndex);
  const upperAnswer = answer.toUpperCase();

  return upperAnswer === letter ||
    upperAnswer === `OPTION ${letter}` ||
    upperAnswer.startsWith(`${letter})`) ||
    upperAnswer.startsWith(`${letter}.`);
};

/**
 * Calculate quiz score based on user answers
 */
const calculateQuizScore = (quizData, userAnswers) => {
  return quizData.reduce((score, question, index) => {
    const selectedOption = userAnswers[index];
    const selectedIndex = (question.options || []).indexOf(selectedOption);
    return selectedIndex !== -1 && isAnswerCorrect(question, selectedIndex)
      ? score + 1
      : score;
  }, 0);
};

/**
 * Export quiz to CSV format
 */
const exportQuizToCSV = (quizData, t) => {
  const headers = [
    t('quiz.headers.question'),
    t('quiz.headers.optionA'),
    t('quiz.headers.optionB'),
    t('quiz.headers.optionC'),
    t('quiz.headers.optionD'),
    t('quiz.headers.correctAnswer')
  ];

  const rows = quizData.map(q => {
    const options = q.options || [];
    const correctAnswerText = typeof q.correct_answer === 'number'
      ? options[q.correct_answer] || `Index ${q.correct_answer}`
      : q.correct_answer;

    return [
      q.question,
      ...options.slice(0, 4).map(opt => opt || ""),
      correctAnswerText
    ].map(text => `"${text.replace(/"/g, '""')}"`).join(",");
  });

  const csvContent = [headers.join(","), ...rows].join("\n");
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", "quiz_export.csv");
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

// ============================================================================
// SUB-COMPONENTS
// ============================================================================

const StartScreen = ({ questionCount, onPlay, onViewTable, t }) => (
  <div className="w-full max-w-md bg-white dark:bg-gray-800 rounded-xl p-6 border border-slate-200 dark:border-gray-700 shadow-sm flex flex-col gap-4">
    <h3 className="text-lg font-bold text-slate-800 dark:text-white text-center">
      {t('quiz.generated')}
    </h3>
    <p className="text-slate-500 dark:text-slate-400 text-center text-sm">
      {t('quiz.readyMessage', { count: questionCount })}
    </p>
    <div className="flex gap-3 mt-2">
      <button
        onClick={onPlay}
        className="flex-1 flex flex-col items-center justify-center gap-2 p-4 rounded-xl bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800 hover:bg-indigo-100 dark:hover:bg-indigo-900/40 transition group"
      >
        <PlayIcon size={32} className="text-indigo-600 dark:text-indigo-400 group-hover:scale-110 transition-transform" weight="duotone" />
        <span className="font-semibold text-indigo-700 dark:text-indigo-300">{t('quiz.play')}</span>
      </button>
      <button
        onClick={onViewTable}
        className="flex-1 flex flex-col items-center justify-center gap-2 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-gray-700 hover:bg-slate-100 dark:hover:bg-slate-700 transition group"
      >
        <TableIcon size={32} className="text-slate-600 dark:text-slate-400 group-hover:scale-110 transition-transform" weight="duotone" />
        <span className="font-semibold text-slate-700 dark:text-slate-300">{t('quiz.viewTable')}</span>
      </button>
    </div>
  </div>
);

const TableMode = ({ quizData, onBack, onExport, t }) => (
  <div className="w-full max-w-5xl bg-white dark:bg-gray-800 rounded-xl border border-slate-200 dark:border-gray-700 shadow-sm overflow-hidden flex flex-col">
    <div className="p-4 border-b border-slate-200 dark:border-gray-700 flex items-center justify-between bg-slate-50 dark:bg-gray-900/50">
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition"
      >
        <ArrowLeftIcon /> {t('quiz.back')}
      </button>
      <button
        onClick={onExport}
        className="flex items-center gap-2 px-3 py-1.5 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition shadow-sm"
      >
        <DownloadIcon weight="bold" /> {t('quiz.exportCsv')}
      </button>
    </div>
    <div className="overflow-x-auto">
      <table className="w-full text-sm text-left border-collapse">
        <thead className="bg-slate-100 dark:bg-gray-900 text-slate-700 dark:text-slate-300 font-semibold border-b border-slate-200 dark:border-gray-700 whitespace-nowrap">
          <tr>
            <th className="px-4 py-3 w-12 text-center">#</th>
            <th className="px-4 py-3 min-w-[200px]">{t('quiz.headers.question')}</th>
            <th className="px-4 py-3 min-w-[150px]">{t('quiz.headers.optionA')}</th>
            <th className="px-4 py-3 min-w-[150px]">{t('quiz.headers.optionB')}</th>
            <th className="px-4 py-3 min-w-[150px]">{t('quiz.headers.optionC')}</th>
            <th className="px-4 py-3 min-w-[150px]">{t('quiz.headers.optionD')}</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-gray-700">
          {quizData.map((q, idx) => {
            const options = q.options || [];
            return (
              <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-gray-800/50">
                <td className="px-4 py-3 text-slate-500 text-center">{idx + 1}</td>
                <td className="px-4 py-3 text-slate-900 dark:text-slate-100 font-medium">{q.question}</td>
                {[0, 1, 2, 3].map(i => {
                  const isCorrect = isAnswerCorrect(q, i);
                  return (
                    <td
                      key={i}
                      className={`px-4 py-3 border-l border-slate-100 dark:border-gray-700 ${isCorrect
                          ? "text-green-600 dark:text-green-400 font-bold"
                          : "text-slate-600 dark:text-slate-400"
                        }`}
                    >
                      {options[i] || "-"}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  </div>
);

// ============================================================================
// MAIN COMPONENT
// ============================================================================

const QuizRenderer = ({ data, botId, sessionId }) => {
  const { t } = useTranslation();
  const [mode, setMode] = useState('start');
  const [answers, setAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Validation
  if (!Array.isArray(data) || data.length === 0) {
    return <div className="text-red-500 text-sm">{t('quiz.invalidData')}</div>;
  }

  // Memoized score calculation
  const score = useMemo(
    () => showResults ? calculateQuizScore(data, answers) : 0,
    [data, answers, showResults]
  );

  // Event handlers
  const resetQuiz = useCallback(() => {
    setMode('start');
    setAnswers({});
    setShowResults(false);
    setIsSubmitting(false);
  }, []);

  const handleExportCSV = useCallback(() => {
    exportQuizToCSV(data, t);
  }, [data, t]);

  const handleCheckAnswers = useCallback(async () => {
    if (showResults) return;

    setShowResults(true);

    if (botId && sessionId) {
      setIsSubmitting(true);
      try {
        const finalScore = calculateQuizScore(data, answers);
        await quizService.submitAttempt({
          bot_id: botId,
          session_id: sessionId,
          score: finalScore,
          total_questions: data.length,
          quiz_data: data,
          user_answers: answers
        });
        toast.success(t('quiz.saved', "Quiz result saved!"));
      } catch (error) {
        console.error(error);
        toast.error(t('quiz.saveFailed', "Failed to save result"));
      } finally {
        setIsSubmitting(false);
      }
    }
  }, [showResults, botId, sessionId, data, answers, t]);

  const handleOptionSelect = useCallback((qIndex, option) => {
    if (showResults) return;
    setAnswers(prev => ({ ...prev, [qIndex]: option }));
  }, [showResults]);

  // Render modes
  if (mode === 'start') {
    return (
      <StartScreen
        questionCount={data.length}
        onPlay={() => setMode('play')}
        onViewTable={() => setMode('table')}
        t={t}
      />
    );
  }

  if (mode === 'table') {
    return (
      <TableMode
        quizData={data}
        onBack={resetQuiz}
        onExport={handleExportCSV}
        t={t}
      />
    );
  }

  // Play Mode
  return (
    <div className="space-y-6 w-full max-w-2xl bg-white dark:bg-gray-800 rounded-xl p-6 border border-slate-200 dark:border-gray-700 shadow-sm relative">
      <button
        onClick={resetQuiz}
        className="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-full hover:bg-slate-100 dark:hover:bg-gray-700 transition"
      >
        <ArrowLeftIcon size={20} />
      </button>

      <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-4">
        {t('quiz.title')}
      </h3>

      {data.map((q, qIndex) => (
        <div key={qIndex} className="space-y-3 pb-4 border-b border-slate-100 dark:border-gray-700 last:border-0">
          <p className="font-medium text-slate-700 dark:text-slate-200">
            {qIndex + 1}. {q.question}
          </p>

          <div className="space-y-2 pl-2">
            {Array.isArray(q.options) && q.options.map((option, oIndex) => {
              const selected = answers[qIndex] === option;
              const isCorrect = isAnswerCorrect(q, oIndex);

              let btnClass = "w-full text-left px-4 py-2 rounded-lg border text-sm transition-all ";

              if (showResults) {
                if (isCorrect) {
                  btnClass += "bg-green-50 border-green-200 text-green-700 dark:bg-green-900/30 dark:border-green-800 dark:text-green-300";
                } else if (selected) {
                  btnClass += "bg-red-50 border-red-200 text-red-700 dark:bg-red-900/30 dark:border-red-800 dark:text-red-300";
                } else {
                  btnClass += "bg-slate-50 border-slate-200 text-slate-400 opacity-60 dark:bg-gray-800/50 dark:border-gray-700";
                }
              } else {
                btnClass += selected
                  ? "bg-indigo-50 border-indigo-200 text-indigo-700 dark:bg-indigo-900/30 dark:border-indigo-800 dark:text-indigo-300"
                  : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50 dark:bg-gray-800 dark:border-gray-700 dark:text-slate-300 dark:hover:bg-gray-700";
              }

              return (
                <button
                  key={oIndex}
                  onClick={() => handleOptionSelect(qIndex, option)}
                  className={btnClass}
                  disabled={showResults}
                >
                  <div className="flex items-center justify-between">
                    <span>{option}</span>
                    {showResults && isCorrect && <CheckCircleIcon className="text-green-600 text-lg" weight="fill" />}
                    {showResults && selected && !isCorrect && <XCircleIcon className="text-red-600 text-lg" weight="fill" />}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      ))}

      <div className="pt-2 flex items-center justify-between">
        {!showResults ? (
          <button
            onClick={handleCheckAnswers}
            disabled={Object.keys(answers).length !== data.length || isSubmitting}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition font-medium text-sm shadow-sm"
          >
            {isSubmitting ? t('common.saving', "Saving...") : t('quiz.checkAnswers')}
          </button>
        ) : (
          <div className="flex items-center gap-2 bg-slate-100 dark:bg-gray-700 px-4 py-2 rounded-lg">
            <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">
              {t('quiz.score', { score, total: data.length })}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default QuizRenderer;
