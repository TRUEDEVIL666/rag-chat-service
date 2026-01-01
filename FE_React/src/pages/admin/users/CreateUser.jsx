import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  User,
  Camera,
  ShieldCheck,
  Key,
  Envelope,
  Lock,
  CheckSquare,
  IdentificationBadge,
  CaretDown,
  HashStraight,
  ArrowRight,
  Spinner,
} from '@phosphor-icons/react';
import { useTranslation } from 'react-i18next';
import { clsx } from 'clsx';
import { useUsers } from '../../../hooks/useUsers';

const CreateUser = () => {
  const { t } = useTranslation(['users', 'translation']);
  const navigate = useNavigate();
  const { createUser, loading } = useUsers();
  const [msg, setMsg] = useState({ text: '', type: '' });

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    role: 'user',
    tenant_id: ''
  });



  const handleChange = (e) => {
    const { id, value } = e.target;
    // Map id to state key manually or standardize ids
    let key = id;
    if (id === 'userEmail') key = 'email';
    if (id === 'userPassword') key = 'password';
    if (id === 'confirmPassword') key = 'confirmPassword';
    if (id === 'userRole') key = 'role';
    if (id === 'tenantId') key = 'tenant_id';

    setFormData(prev => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (formData.password !== formData.confirmPassword) {
      setMsg({ text: t('create.alert.passwordMismatch'), type: "error" });
      return;
    }

    setMsg({ text: "", type: "" });

    const payload = {
      email: formData.email,
      password: formData.password,
      role: formData.role,
      tenant_id: formData.tenant_id || null
    };

    try {
      await createUser(payload);

      setMsg({ text: t('create.alert.createSuccess'), type: "success" });
      setTimeout(() => {
        navigate('/admin/users');
      }, 1500);

    } catch (error) {
      console.error("Create user failed", error);
      const errorMsg = error.response?.data?.detail || t('common.errorOccurred');
      setMsg({ text: errorMsg, type: "error" });
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-gray-50 dark:bg-gray-900 transition-colors">
      {/* Header */}
      <header className="h-20 bg-white/80 dark:bg-gray-800/80 backdrop-blur-md border-b border-gray-100 dark:border-gray-700 flex items-center justify-between px-10 sticky top-0 z-40 transition-colors">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/admin/users')}
            className="p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-full transition text-gray-400 hover:text-primary-600"
          >
            <ArrowLeft size={24} />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-800 dark:text-white tracking-tight">{t('create.title')}</h1>
            <p className="text-sm text-gray-400 font-medium">{t('create.subtitle')}</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <span className="text-xs font-bold text-gray-300 uppercase tracking-widest">{t('create.stepInfo')}</span>
        </div>
      </header>

      {/* Form Scroll Area */}
      <div className="flex-1 overflow-auto p-10 flex justify-center">
        <div className="w-full max-w-4xl animate-slide-up">
          <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-12 gap-10">
            {/* LEFT COLUMN: Profile Visual */}
            <div className="lg:col-span-4 flex flex-col items-center">
              <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl border border-white/20 shadow-xl w-full rounded-3xl p-8 flex flex-col items-center text-center transition-colors">
                <div className="relative group cursor-pointer">
                  <div className="w-32 h-32 rounded-3xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-gray-400 text-5xl mb-6 shadow-inner transition group-hover:scale-105">
                    <User size={48} />
                  </div>
                  <div className="absolute -bottom-1 -right-1 w-10 h-10 bg-white dark:bg-gray-600 rounded-2xl shadow-lg border border-gray-50 dark:border-gray-500 flex items-center justify-center text-primary-600 dark:text-primary-400">
                    <Camera size={20} weight="fill" />
                  </div>
                </div>
                <h3 className="font-bold text-gray-800 dark:text-white text-lg break-all">
                  {formData.email || t('create.newAccount')}
                </h3>
                <p className="text-xs text-gray-400 mt-1 uppercase tracking-tighter font-bold">
                  {formData.role === 'admin' ? t('role.admin') : t('role.user')}
                </p>

                <div className="mt-8 pt-8 border-t border-gray-50 dark:border-gray-700 w-full text-left space-y-4">
                  <div className="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
                    <ShieldCheck size={20} className="text-green-500" />
                    <span>{t('create.features.security')}</span>
                  </div>
                  <div className="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
                    <Key size={20} className="text-primary-500" />
                    <span>{t('create.features.access')}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* RIGHT COLUMN: Form Fields */}
            <div className="lg:col-span-8 flex flex-col gap-6">
              <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl border border-white/20 shadow-xl rounded-3xl p-10 space-y-8 transition-colors">

                {/* Section: Identity */}
                <div>
                  <h4 className="text-sm font-bold text-primary-600 uppercase tracking-widest mb-6">{t('create.sections.identity')}</h4>
                  <div className="grid grid-cols-1 gap-6">
                    <div>
                      <label className="block text-sm font-semibold text-gray-600 dark:text-gray-300 mb-2">{t('create.emailLabel')}</label>
                      <div className="relative">
                        <Envelope size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                        <input
                          type="email"
                          id="userEmail"
                          value={formData.email}
                          onChange={handleChange}
                          required
                          placeholder="example@domain.com"
                          className="w-full pl-12 pr-4 py-3.5 bg-gray-50/50 dark:bg-gray-700/50 border-none rounded-2xl outline-none text-gray-700 dark:text-gray-200 focus:ring-2 focus:ring-primary-500/20 transition-all"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Section: Credentials */}
                <div>
                  <h4 className="text-sm font-bold text-primary-600 uppercase tracking-widest mb-6">{t('create.sections.security')}</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-semibold text-gray-600 dark:text-gray-300 mb-2">{t('create.passwordLabel')}</label>
                      <div className="relative">
                        <Lock size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                        <input
                          type="password"
                          id="userPassword"
                          value={formData.password}
                          onChange={handleChange}
                          required
                          placeholder="••••••••"
                          className="w-full pl-12 pr-4 py-3.5 bg-gray-50/50 dark:bg-gray-700/50 border-none rounded-2xl outline-none text-gray-700 dark:text-gray-200 focus:ring-2 focus:ring-primary-500/20 transition-all"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-600 dark:text-gray-300 mb-2">{t('create.confirmPasswordLabel')}</label>
                      <div className="relative">
                        <CheckSquare size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                        <input
                          type="password"
                          id="confirmPassword"
                          value={formData.confirmPassword}
                          onChange={handleChange}
                          required
                          placeholder="••••••••"
                          className="w-full pl-12 pr-4 py-3.5 bg-gray-50/50 dark:bg-gray-700/50 border-none rounded-2xl outline-none text-gray-700 dark:text-gray-200 focus:ring-2 focus:ring-primary-500/20 transition-all"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Section: Role & Tenant */}
                <div>
                  <h4 className="text-sm font-bold text-primary-600 uppercase tracking-widest mb-6">{t('create.sections.permissions')}</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-semibold text-gray-600 dark:text-gray-300 mb-2">{t('create.roleLabel')}</label>
                      <div className="relative">
                        <IdentificationBadge size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                        <select
                          id="userRole"
                          value={formData.role}
                          onChange={handleChange}
                          className="w-full pl-12 pr-10 py-3.5 bg-gray-50/50 dark:bg-gray-700/50 border-none rounded-2xl outline-none text-gray-700 dark:text-gray-200 appearance-none cursor-pointer focus:ring-2 focus:ring-primary-500/20 transition-all"
                        >
                          <option value="user">{t('role.user')}</option>
                          <option value="admin">{t('role.admin')}</option>
                        </select>
                        <CaretDown size={16} className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-600 dark:text-gray-300 mb-2">{t('create.tenantLabel')}</label>
                      <div className="relative">
                        <HashStraight size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                        <input
                          type="text"
                          id="tenantId"
                          value={formData.tenant_id}
                          onChange={handleChange}
                          placeholder={t('create.tenantPlaceholder')}
                          className="w-full pl-12 pr-4 py-3.5 bg-gray-50/50 dark:bg-gray-700/50 border-none rounded-2xl outline-none text-gray-700 dark:text-gray-200 focus:ring-2 focus:ring-primary-500/20 transition-all"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="pt-6 flex items-center justify-between border-t border-gray-50 dark:border-gray-700/50">
                  <p className={clsx("text-sm font-medium", msg.type === 'error' ? 'text-red-500' : 'text-green-500')}>
                    {msg.text}
                  </p>
                  <div className="flex gap-4">
                    <button
                      type="button"
                      onClick={() => navigate('/admin/users')}
                      className="px-8 py-3.5 text-gray-500 dark:text-gray-400 font-bold hover:bg-gray-50 dark:hover:bg-gray-700 rounded-2xl transition"
                    >
                      {t('common.cancel')}
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="bg-gradient-to-r from-primary-600 to-indigo-600 hover:from-primary-700 hover:to-indigo-700 px-10 py-3.5 text-white font-bold rounded-2xl shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300 flex items-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
                    >
                      {loading ? (
                        <>
                          <Spinner size={20} className="animate-spin" />
                          <span>{t('common.processing')}</span>
                        </>
                      ) : (
                        <>
                          <span>{t('create.submit')}</span>
                          <ArrowRight size={20} weight="bold" />
                        </>
                      )}
                    </button>
                  </div>
                </div>

              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CreateUser;
