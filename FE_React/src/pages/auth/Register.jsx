import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { Spinner } from '@phosphor-icons/react';
import { useTranslation } from 'react-i18next';

import { authService } from '../../services/authService';

const Register = () => {
  const { t } = useTranslation(['auth', 'translation']);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      setError(t('register.passwordMismatch'));
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      await authService.register({
        name,
        email,
        password
      });
      // On success, redirect to login
      alert(t('register.success'));
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.detail || t('register.fail'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden flex flex-col md:flex-row max-w-4xl mx-auto w-full">
      {/* Image Side */}
      <div className="hidden md:block w-1/2 relative bg-gray-900">
        <img
          src="https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?q=80&w=2070&auto=format&fit=crop"
          alt="Office"
          className="absolute inset-0 w-full h-full object-cover opacity-80"
        />
      </div>

      {/* Form Side */}
      <div className="w-full md:w-1/2 p-8 md:p-10 flex flex-col justify-center">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100 mb-2">{t('register.title')}</h1>
          <p className="text-gray-500 dark:text-gray-400">{t('register.subtitle')}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-gray-700 dark:text-gray-300 font-medium mb-1">{t('login.email')}</label>
            <input
              type="email"
              required
              className="input-field"
              placeholder={t('login.emailPlaceholder')}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-gray-700 dark:text-gray-300 font-medium mb-1">Name</label>
            <input
              type="text"
              required
              className="input-field"
              placeholder="Enter your name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-gray-700 dark:text-gray-300 font-medium mb-1">{t('login.password')}</label>
            <input
              type="password"
              required
              className="input-field"
              placeholder={t('login.passwordPlaceholder')}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-gray-700 dark:text-gray-300 font-medium mb-1">{t('register.confirmPassword')}</label>
            <input
              type="password"
              required
              className="input-field"
              placeholder={t('login.passwordPlaceholder')}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </div>

          {error && (
            <div className="text-red-500 text-sm font-medium text-center">{error}</div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary w-full shadow-lg shadow-blue-500/30 mt-2"
          >
            {isLoading ? (
              <>
                <Spinner className="animate-spin" size={20} />
                <span>{t('common.processing')}</span>
              </>
            ) : (
              t('register.submit')
            )}
          </button>
        </form>

        <div className="mt-6 text-center text-gray-600 dark:text-gray-400">
          {t('register.hasAccount')}{' '}
          <Link to="/login" className="text-primary-600 dark:text-primary-400 font-bold hover:underline">
            {t('register.loginNow')}
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Register;
