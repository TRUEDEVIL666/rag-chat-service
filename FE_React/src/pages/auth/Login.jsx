import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';

import { Eye, EyeSlash, Spinner } from '@phosphor-icons/react';
import { useAuth } from '../../context/AuthContext';


const Login = () => {
  const { t } = useTranslation(['auth', 'translation']);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const success = await login(email, password);
      if (success) {
        navigate('/admin/dashboard');
      } else {
        setError(t('login.fail'));
      }
    } catch (err) {
      setError(err.response?.data?.detail || t('login.fail'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden flex flex-col md:flex-row max-w-4xl mx-auto w-full min-h-[600px]">
      {/* Image Side */}
      <div className="hidden md:block w-1/2 relative bg-gray-900">
        <img
          src="https://images.unsplash.com/photo-1497215728101-856f4ea42174?q=80&w=2070&auto=format&fit=crop"
          alt="Office"
          className="absolute inset-0 w-full h-full object-cover opacity-80"
        />
      </div>

      {/* Form Side */}
      <div className="w-full md:w-1/2 p-8 md:p-12 flex flex-col justify-center">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100 mb-2">{t('login.title')}</h1>
          <p className="text-gray-500 dark:text-gray-400">{t('login.subtitle')}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-gray-700 dark:text-gray-300 font-medium mb-2">{t('login.email')}</label>
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
            <label className="block text-gray-700 dark:text-gray-300 font-medium mb-2">{t('login.password')}</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                required
                className="input-field pr-10"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                {showPassword ? <Eye size={20} /> : <EyeSlash size={20} />}
              </button>
            </div>
          </div>

          <div className="min-h-[24px] flex items-center justify-center mt-4">
            {error && (
              <div className="text-red-500 text-sm font-medium text-center">{error}</div>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary w-full shadow-lg shadow-blue-500/30"
          >
            {isLoading ? (
              <>
                <Spinner className="animate-spin" size={20} />
                <span>{t('common.processing')}</span>
              </>
            ) : (
              t('login.submit')
            )}
          </button>
        </form>

        <div className="mt-8 text-center text-gray-600 dark:text-gray-400">
          {t('login.noAccount')}{' '}
          <Link to="/register" className="text-primary-600 dark:text-primary-400 font-bold hover:underline">
            {t('login.registerNow')}
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Login;
