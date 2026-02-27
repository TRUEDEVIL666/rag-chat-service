import React from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import {
  GearIcon,
  UserCircleIcon,
  SlidersIcon,
  ShieldCheckIcon,
  PasswordIcon,
  SignOutIcon,
  CaretRightIcon,
  ListIcon
} from '@phosphor-icons/react';
import { useAuth } from '../../context/AuthContext';

const UserSettings = () => {
  const { toggleSidebar } = useOutletContext();
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <>
      {/* Header */}
      <header className="h-16 border-b border-slate-200 bg-white/50 backdrop-blur flex items-center justify-between px-6 shrink-0">
        <div className="flex items-center gap-3">
          <button onClick={toggleSidebar} className="md:hidden p-2 text-slate-500 hover:bg-white/50 rounded-lg">
            <ListIcon className="text-xl" />
          </button>
          <h1 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            <GearIcon weight="fill" className="text-indigo-600" /> Cài đặt tài khoản
          </h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto space-y-6">

          {/* Profile Section */}
          <div className="bg-white/80 backdrop-blur border border-slate-200 rounded-2xl p-6 shadow-sm">
            <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
              <UserCircleIcon weight="duotone" className="text-2xl text-indigo-600" /> Thông tin cá nhân
            </h2>

            <div className="flex items-start gap-6 flex-col md:flex-row">
              <div className="flex flex-col items-center gap-2 self-center md:self-start">
                <img
                  src="https://ui-avatars.com/api/?name=Dat+Nguyen&background=random"
                  className="w-24 h-24 rounded-full shadow-md border-4 border-white"
                  alt="Profile"
                />
                <button className="text-xs font-semibold text-indigo-600 hover:text-indigo-700">Đổi ảnh đại diện</button>
              </div>

              <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1">Họ và tên</label>
                  <input type="text" defaultValue="Nguyễn Hữu Đạt" className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1">Mã sinh viên</label>
                  <input type="text" defaultValue="20206267" disabled className="w-full px-4 py-2 bg-slate-100 border border-slate-200 rounded-lg text-sm text-slate-500 cursor-not-allowed" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1">Email</label>
                  <input type="email" defaultValue="dat.nh206267@sis.hust.edu.vn" className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1">Số điện thoại</label>
                  <input type="tel" defaultValue="0987654321" className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition" />
                </div>
              </div>
            </div>
          </div>

          {/* Preferences Settings */}
          <div className="bg-white/80 backdrop-blur border border-slate-200 rounded-2xl p-6 shadow-sm">
            <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
              <SlidersIcon weight="duotone" className="text-2xl text-indigo-600" /> Tùy chỉnh
            </h2>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 transition">
                <div>
                  <h4 className="text-sm font-semibold text-slate-700">Chế độ tối (Dark Mode)</h4>
                  <p className="text-xs text-slate-400">Chuyển sang giao diện tối giúp bảo vệ mắt</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" />
                  <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                </label>
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 transition">
                <div>
                  <h4 className="text-sm font-semibold text-slate-700">Thông báo (Notifications)</h4>
                  <p className="text-xs text-slate-400">Nhận thông báo về lịch học và câu trả lời mới</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" defaultChecked className="sr-only peer" />
                  <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                </label>
              </div>
            </div>
          </div>

          {/* Security */}
          <div className="bg-white/80 backdrop-blur border border-slate-200 rounded-2xl p-6 shadow-sm">
            <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
              <ShieldCheckIcon weight="duotone" className="text-2xl text-indigo-600" /> Bảo mật
            </h2>
            <button className="flex items-center justify-between w-full p-4 bg-slate-50 border border-slate-200 rounded-lg hover:bg-slate-100 transition">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center text-slate-500 shadow-sm">
                  <PasswordIcon weight="bold" />
                </div>
                <div className="text-left">
                  <h4 className="text-sm font-semibold text-slate-700">Đổi mật khẩu</h4>
                  <p className="text-xs text-slate-400">Cập nhật mật khẩu định kỳ để bảo vệ tài khoản</p>
                </div>
              </div>
              <CaretRightIcon weight="bold" className="text-slate-400" />
            </button>

            <div className="mt-4 pt-4 border-t border-slate-100">
              <button
                onClick={handleLogout}
                className="text-sm font-medium text-red-600 hover:text-red-700 flex items-center gap-2"
              >
                <SignOutIcon weight="bold" /> Đăng xuất
              </button>
            </div>
          </div>

        </div>
      </main>
    </>
  );
};

export default UserSettings;
