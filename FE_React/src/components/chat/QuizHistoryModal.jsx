import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { quizService } from '../../services/quizService';
import { XIcon, FileTextIcon, CalendarIcon, RobotIcon, SpinnerIcon, ArrowLeftIcon, CheckCircleIcon, XCircleIcon } from '@phosphor-icons/react';
import { format } from 'date-fns';

const QuizHistoryModal = ({ isOpen, onClose }) => {
  const { t } = useTranslation();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedAttempt, setSelectedAttempt] = useState(null);

  useEffect(() => {
    if (isOpen) {
      loadHistory();
      setSelectedAttempt(null);
    }
  }, [isOpen]);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const data = await quizService.getHistory();
      setHistory(data || []);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const renderDetailView = () => {
    if (!selectedAttempt) return null;

    return (
      <div className="flex flex-col h-full">
        <div className="p-4 border-b border-slate-100 dark:border-gray-700 flex justify-between items-center bg-slate-50/50 dark:bg-gray-900/50 rounded-t-2xl">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setSelectedAttempt(null)}
              className="p-2 -ml-2 hover:bg-slate-200 dark:hover:bg-gray-700 rounded-lg transition text-slate-500"
            >
              <ArrowLeftIcon size={20} />
            </button>
            <h2 className="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
              <span className="bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 text-xs px-2 py-1 rounded-md font-medium">
                {selectedAttempt.bots?.name}
              </span>
              <span className="text-sm font-normal text-slate-500">
                {format(new Date(selectedAttempt.created_at), 'MMM d, yyyy HH:mm')}
              </span>
            </h2>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-slate-200 dark:hover:bg-gray-700 rounded-lg transition text-slate-500">
            <XIcon size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 custom-scrollbar space-y-4">
          <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-gray-900/50 rounded-xl mb-4">
            <span className="text-slate-600 dark:text-slate-300 font-medium">Score</span>
            <span className={`text-lg font-bold ${(selectedAttempt.score / selectedAttempt.total_questions) >= 0.7 ? 'text-green-600' : 'text-amber-600'}`}>
              {selectedAttempt.score} / {selectedAttempt.total_questions}
            </span>
          </div>

          {selectedAttempt.quiz_data?.map((q, idx) => {
            const userAnswer = selectedAttempt.user_answers?.[idx];

            // Robust check similar to QuizRenderer
            const checkIsCorrect = (correctAnswer, optionIndex, optionText) => {
              if (!correctAnswer) return false;
              const ans = String(correctAnswer).trim();

              // 1. Exact Text Match
              if (ans === optionText) return true;

              // 2. Letter/Index Match (A, B, C...)
              const letter = String.fromCharCode(65 + Number(optionIndex)); // A, B...
              const upperAns = ans.toUpperCase();

              if (upperAns === letter) return true;
              if (upperAns === `OPTION ${letter}`) return true;
              if (upperAns.startsWith(`${letter})`) || upperAns.startsWith(`${letter}.`)) return true;

              return false;
            };

            return (
              <div key={idx} className="p-4 rounded-xl border border-slate-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                <h3 className="font-medium text-slate-800 dark:text-white mb-3">
                  {idx + 1}. {q.question}
                </h3>

                <div className="space-y-2">
                  {Object.entries(q.options).map(([key, value]) => {
                    const isSelected = userAnswer === value;
                    const isKeyCorrect = checkIsCorrect(q.correct_answer, key, value);

                    let bgClass = "bg-slate-50 dark:bg-gray-900/30 border-transparent";
                    if (isSelected && isKeyCorrect) bgClass = "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800";
                    else if (isSelected && !isKeyCorrect) bgClass = "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800";
                    else if (!isSelected && isKeyCorrect) bgClass = "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 border-dashed";

                    return (
                      <div key={key} className={`p-3 rounded-lg border text-sm flex justify-between items-center ${bgClass}`}>
                        <span className={isSelected || isKeyCorrect ? "font-medium" : ""}>
                          {value}
                        </span>
                        {isSelected && isKeyCorrect && <CheckCircleIcon className="text-green-600" size={18} weight="fill" />}
                        {isSelected && !isKeyCorrect && <XCircleIcon className="text-red-600" size={18} weight="fill" />}
                        {!isSelected && isKeyCorrect && <CheckCircleIcon className="text-green-600 opacity-50" size={18} />}
                      </div>
                    );
                  })}
                </div>

                {q.explanation && (
                  <div className="mt-3 text-xs text-slate-500 dark:text-gray-400 bg-slate-50 dark:bg-gray-900/50 p-3 rounded-lg">
                    <strong>Explanation:</strong> {q.explanation}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm fade-in">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col border border-slate-200 dark:border-gray-700 h-[600px]">
        {selectedAttempt ? (
          renderDetailView()
        ) : (
          <>
            <div className="p-4 border-b border-slate-100 dark:border-gray-700 flex justify-between items-center bg-slate-50/50 dark:bg-gray-900/50 rounded-t-2xl">
              <h2 className="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
                <FileTextIcon className="text-indigo-600 dark:text-indigo-400" />
                {t('quiz.historyTitle', "Quiz History")}
              </h2>
              <button onClick={onClose} className="p-2 hover:bg-slate-200 dark:hover:bg-gray-700 rounded-lg transition text-slate-500">
                <XIcon size={20} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 custom-scrollbar space-y-3">
              {loading ? (
                <div className="flex justify-center py-8">
                  <SpinnerIcon className="animate-spin text-indigo-600" size={32} />
                </div>
              ) : history.length === 0 ? (
                <div className="text-center py-8 text-slate-500 dark:text-slate-400">
                  {t('quiz.noHistory', "No quiz attempts found.")}
                </div>
              ) : (
                history.map((attempt) => (
                  <div
                    key={attempt.id}
                    onClick={() => setSelectedAttempt(attempt)}
                    className="p-4 rounded-xl border border-slate-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:shadow-md hover:border-indigo-300 dark:hover:border-indigo-700 transition cursor-pointer group"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center gap-2">
                        <span className="bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 text-xs px-2 py-1 rounded-md font-medium flex items-center gap-1">
                          <RobotIcon weight="fill" />
                          {attempt.bots?.name || 'Unknown Bot'}
                        </span>
                        <span className="text-xs text-slate-400 flex items-center gap-1">
                          <CalendarIcon />
                          {format(new Date(attempt.created_at), 'MMM d, yyyy HH:mm')}
                        </span>
                      </div>
                      <div className={`px-2 py-1 rounded-lg text-sm font-bold ${(attempt.score / attempt.total_questions) >= 0.7
                        ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                        : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                        }`}>
                        {attempt.score}/{attempt.total_questions}
                      </div>
                    </div>
                    <div className="text-xs text-indigo-600 dark:text-indigo-400 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                      Click to view details
                    </div>
                  </div>
                ))
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default QuizHistoryModal;
