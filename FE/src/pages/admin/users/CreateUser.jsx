
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ROUTES } from '../../../routes';
import {
  ArrowLeft,
  User,
  CameraIcon,
  ShieldCheckIcon,
  KeyIcon,
  Envelope,
  LockIcon,
  CheckSquareIcon,
  IdentificationBadgeIcon,
  CaretDownIcon,
  ArrowRightIcon,
  SpinnerIcon,
} from '@phosphor-icons/react';
import { useTranslation } from 'react-i18next';
import { clsx } from 'clsx';
import { useUsers } from '../../../hooks/useUsers';
import { getAllTenants } from '../../../services/tenantService';
import { XIcon, BuildingsIcon } from '@phosphor-icons/react';

const CreateUser = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { createUser, loading } = useUsers();
  const [msg, setMsg] = useState({ text: '', type: '' });

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'user',
    tenant_id: '',
    tenant_name: ''
  });




  const [isTenantModalOpen, setIsTenantModalOpen] = useState(false);
  const [tenants, setTenants] = useState([]);
  const [loadingTenants, setLoadingTenants] = useState(false);

  const fetchTenants = async () => {
    setLoadingTenants(true);
    try {
      const data = await getAllTenants();
      setTenants(data);
    } catch (error) {
      console.error("Failed to fetch tenants", error);
      setMsg({ text: t('admin.users.create.alert.fetchTenantsFailed') || "Failed to fetch tenants", type: "error" });
    } finally {
      setLoadingTenants(false);
    }
  };

  const handleOpenTenantModal = () => {
    setIsTenantModalOpen(true);
    fetchTenants();
  };

  const handleSelectTenant = (tenant) => {
    setFormData(prev => ({ ...prev, tenant_id: tenant.id, tenant_name: tenant.name }));
    setIsTenantModalOpen(false);
  };

  const handleChange = (e) => {
    const { id, value } = e.target;
    // Map id to state key manually or standardize ids
    let key = id;
    if (id === 'userName') key = 'name';
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
      setMsg({ text: t('admin.users.create.alert.passwordMismatch'), type: "error" });
      return;
    }

    setMsg({ text: "", type: "" });

    const payload = {
      name: formData.name,
      email: formData.email,
      password: formData.password,
      role: formData.role,
      tenant_id: formData.tenant_id || null
    };

    try {
      await createUser(payload);

      setMsg({ text: t('admin.users.create.alert.createSuccess'), type: "success" });
      setTimeout(() => {
        navigate(ROUTES.ADMIN.USERS.LIST);
      }, 1500);

    } catch (error) {
      console.error("Create user failed", error);
      const errorMsg = error.response?.data?.detail || t('common.errorOccurred');
      setMsg({ text: errorMsg, type: "error" });
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900 transition-colors p-4 md:p-8 flex items-center justify-center">
      <div className="w-full max-w-5xl animate-slide-up">

        {/* Main Unified Card */}
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl border border-white/20 dark:border-gray-700 shadow-2xl rounded-3xl overflow-hidden transition-colors">

          {/* Card Header Section */}
          <div className="px-8 py-6 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between bg-white/50 dark:bg-gray-800/50">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate(ROUTES.ADMIN.USERS.LIST)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition text-gray-500 dark:text-gray-400 hover:text-primary-600"
              >
                <ArrowLeftIcon size={24} weight="bold" />
              </button>
              <div>
                <h1 className="text-xl font-bold text-gray-800 dark:text-white tracking-tight">{t('admin.users.create.title')}</h1>
                <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">{t('admin.users.create.subtitle')}</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-xs font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest bg-gray-100 dark:bg-gray-700/50 px-3 py-1 rounded-full">{t('admin.users.create.stepInfo')}</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="p-8 md:p-10 grid grid-cols-1 lg:grid-cols-12 gap-12">

            {/* LEFT COLUMN: Profile Visual */}
            <div className="lg:col-span-4 flex flex-col items-center border-b lg:border-b-0 lg:border-r border-gray-100 dark:border-gray-700/50 pb-8 lg:pb-0 lg:pr-8">
              <div className="relative group cursor-pointer mb-6">
                <div className="w-40 h-40 rounded-full bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-600 flex items-center justify-center text-gray-400 text-6xl shadow-inner transition transform group-hover:scale-105">
                  <UserIcon size={64} />
                </div>
                <div className="absolute bottom-1 right-1 w-12 h-12 bg-white dark:bg-gray-600 rounded-full shadow-lg border-4 border-white dark:border-gray-800 flex items-center justify-center text-primary-600 dark:text-primary-400">
                  <CameraIcon size={22} weight="fill" />
                </div>
              </div>

              <h3 className="font-bold text-gray-800 dark:text-white text-xl text-center break-all px-4">
                {formData.name || formData.email || t('admin.users.create.newAccount')}
              </h3>
              <p className="text-xs text-primary-600 dark:text-primary-400 mt-2 uppercase tracking-wide font-bold bg-primary-50 dark:bg-primary-900/20 px-3 py-1 rounded-full">
                {formData.role === 'admin' ? t('admin.users.role.admin') : t('admin.users.role.user')}
              </p>

              <div className="mt-10 w-full space-y-4 px-4">
                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">Account Features</h4>
                <div className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-300 p-3 rounded-xl bg-gray-50 dark:bg-gray-700/30">
                  <ShieldCheckIcon size={20} className="text-green-500" weight="fill" />
                  <span>{t('admin.users.create.features.security')}</span>
                </div>
                <div className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-300 p-3 rounded-xl bg-gray-50 dark:bg-gray-700/30">
                  <KeyIcon size={20} className="text-amber-500" weight="fill" />
                  <span>{t('admin.users.create.features.access')}</span>
                </div>
              </div>
            </div>

            {/* RIGHT COLUMN: Form Fields */}
            <div className="lg:col-span-8 space-y-8">

              {/* Msg Alert */}
              {msg.text && (
                <div className={clsx("p-4 rounded-xl text-sm font-medium flex items-center gap-3",
                  msg.type === 'error' ? "bg-red-50 text-red-600 dark:bg-red-900/20 dark:text-red-400" : "bg-green-50 text-green-600 dark:bg-green-900/20 dark:text-green-400"
                )}>
                  {msg.type === 'error' ? <LockIcon size={20} /> : <CheckSquareIcon size={20} />}
                  {msg.text}
                </div>
              )}

              {/* Section: Identity */}
              <div>
                <h4 className="text-xs font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-6 flex items-center gap-2">
                  <IdentificationBadgeIcon size={16} /> {t('admin.users.create.sections.identity')}
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 ml-1">{t('admin.users.create.nameLabel') || "Full Name"}</label>
                    <div className="relative group">
                      <UserIcon size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-primary-500 transition-colors" />
                      <input
                        type="text"
                        id="userName"
                        value={formData.name}
                        onChange={handleChange}
                        required
                        placeholder="John Doe"
                        className="w-full pl-12 pr-4 py-3.5 bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700/50 rounded-xl outline-none text-gray-800 dark:text-gray-100 focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition-all font-medium"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 ml-1">{t('admin.users.create.emailLabel')}</label>
                    <div className="relative group">
                      <EnvelopeIcon size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-primary-500 transition-colors" />
                      <input
                        type="email"
                        id="userEmail"
                        value={formData.email}
                        onChange={handleChange}
                        required
                        placeholder="example@domain.com"
                        className="w-full pl-12 pr-4 py-3.5 bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700/50 rounded-xl outline-none text-gray-800 dark:text-gray-100 focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition-all font-medium"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Section: Credentials */}
              <div>
                <h4 className="text-xs font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-6 flex items-center gap-2">
                  <LockIcon size={16} /> {t('admin.users.create.sections.security')}
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 ml-1">{t('admin.users.create.passwordLabel')}</label>
                    <div className="relative group">
                      <LockIcon size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-primary-500 transition-colors" />
                      <input
                        type="password"
                        id="userPassword"
                        value={formData.password}
                        onChange={handleChange}
                        required
                        placeholder="••••••••"
                        className="w-full pl-12 pr-4 py-3.5 bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700/50 rounded-xl outline-none text-gray-800 dark:text-gray-100 focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition-all font-medium"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 ml-1">{t('admin.users.create.confirmPasswordLabel')}</label>
                    <div className="relative group">
                      <CheckSquareIcon size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-primary-500 transition-colors" />
                      <input
                        type="password"
                        id="confirmPassword"
                        value={formData.confirmPassword}
                        onChange={handleChange}
                        required
                        placeholder="••••••••"
                        className="w-full pl-12 pr-4 py-3.5 bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700/50 rounded-xl outline-none text-gray-800 dark:text-gray-100 focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition-all font-medium"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Section: Role & Tenant */}
              <div>
                <h4 className="text-xs font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-6 flex items-center gap-2">
                  <KeyIcon size={16} /> {t('admin.users.create.sections.permissions')}
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 ml-1">{t('admin.users.create.roleLabel')}</label>
                    <div className="relative group">
                      <IdentificationBadgeIcon size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-primary-500 transition-colors" />
                      <select
                        id="userRole"
                        value={formData.role}
                        onChange={handleChange}
                        className="w-full pl-12 pr-10 py-3.5 bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700/50 rounded-xl outline-none text-gray-800 dark:text-gray-100 appearance-none cursor-pointer focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition-all font-medium"
                      >
                        <option value="user">{t('admin.users.role.user')}</option>
                        <option value="admin">{t('admin.users.role.admin')}</option>
                      </select>
                      <CaretDownIcon size={16} className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 ml-1">Tenant</label>
                    <div className="relative group">
                      <BuildingsIcon size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-primary-500 transition-colors" />
                      <input
                        type="text"
                        id="tenantName"
                        value={formData.tenant_name}
                        onClick={handleOpenTenantModal}
                        readOnly
                        placeholder={t('admin.users.create.tenantPlaceholder') || "Select Tenant"}
                        className="w-full pl-12 pr-4 py-3.5 bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700/50 rounded-xl outline-none text-gray-800 dark:text-gray-100 focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition-all font-medium cursor-pointer"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Tenant Selection Modal */}
              {isTenantModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
                  <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-3xl max-h-[80vh] flex flex-col overflow-hidden animate-scale-up border border-gray-100 dark:border-gray-700">
                    <div className="p-6 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between bg-gray-50/50 dark:bg-gray-800/50">
                      <h3 className="text-lg font-bold text-gray-800 dark:text-white flex items-center gap-2">
                        <BuildingsIcon size={24} className="text-primary-500" />
                        Select Tenant
                      </h3>
                      <button
                        onClick={() => setIsTenantModalOpen(false)}
                        className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full transition text-gray-500"
                      >
                        <XIcon size={20} />
                      </button>
                    </div>

                    <div className="p-6 overflow-y-auto">
                      {loadingTenants ? (
                        <div className="flex justify-center py-12">
                          <SpinnerIcon size={32} className="animate-spin text-primary-500" />
                        </div>
                      ) : tenants.length === 0 ? (
                        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                          No tenants found.
                        </div>
                      ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {tenants.map(tenant => (
                            <div
                              key={tenant.id}
                              onClick={() => handleSelectTenant(tenant)}
                              className={`
p - 4 rounded - xl border border - gray - 200 dark: border - gray - 700 cursor - pointer transition - all duration - 200
hover: border - primary - 500 hover: shadow - md hover: bg - primary - 50 dark: hover: bg - primary - 900 / 10 group
                        ${formData.tenant_id === tenant.id ? 'ring-2 ring-primary-500 bg-primary-50 dark:bg-primary-900/20' : 'bg-white dark:bg-gray-800'}
`}
                            >
                              <div className="flex items-start justify-between mb-2">
                                <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg group-hover:bg-white dark:group-hover:bg-gray-600 transition-colors">
                                  <BuildingsIcon size={20} className="text-gray-500 dark:text-gray-400 group-hover:text-primary-500" />
                                </div>
                                {formData.tenant_id === tenant.id && (
                                  <div className="text-primary-600 dark:text-primary-400">
                                    <CheckSquareIcon size={20} weight="fill" />
                                  </div>
                                )}
                              </div>
                              <h4 className="font-bold text-gray-800 dark:text-white mb-1 truncate" title={tenant.name}>
                                {tenant.name}
                              </h4>
                              <p className="text-xs text-gray-500 dark:text-gray-400 truncate font-mono">
                                {new Date(tenant.created_at).toLocaleDateString()}
                              </p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="pt-8 flex items-center justify-end border-t border-gray-100 dark:border-gray-700/50 gap-4">
                <button
                  type="button"
                  onClick={() => navigate('/admin/users')}
                  className="px-6 py-3 text-gray-500 dark:text-gray-400 font-bold hover:bg-gray-100 dark:hover:bg-gray-700 rounded-xl transition"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-primary-600 hover:bg-primary-700 text-white font-bold rounded-xl shadow-lg hover:shadow-xl hover:-translate-y-0.5 px-8 py-3 transition-all duration-300 flex items-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed disabled:transform-none"
                >
                  {loading ? (
                    <>
                      <SpinnerIcon size={20} className="animate-spin" />
                      <span>{t('common.processing')}</span>
                    </>
                  ) : (
                    <>
                      <span>{t('admin.users.create.submit')}</span>
                      <ArrowRightIcon size={20} weight="bold" />
                    </>
                  )}
                </button>
              </div>

            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CreateUser;
