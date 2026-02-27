import { Outlet } from 'react-router-dom';

const AuthLayout = () => {
    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900 px-4 py-8 transition-colors duration-300">
            <div className="w-full">
                 <Outlet />
            </div>
        </div>
    );
};

export default AuthLayout;
