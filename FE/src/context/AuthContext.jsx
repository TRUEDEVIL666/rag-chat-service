import { createContext, useContext, useState, useEffect } from 'react';
import { jwtDecode } from "jwt-decode";
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
      try {
        const decoded = jwtDecode(storedToken);
        setUser(decoded);
      } catch (e) {
        console.error("Invalid token", e);
        logout();
      }
    }
    setLoading(false);
  }, []);

  const login = async (username, password) => {
    try {
      const data = await authService.login(username, password);
      const newToken = data.token; // Adjust based on actual API response
      if (newToken) {
        localStorage.setItem('token', newToken);
        setToken(newToken);
        const decoded = jwtDecode(newToken);
        setUser(decoded);
        return decoded;
      }
      return false;
    } catch (e) {
      console.error("Login failed", e);
      throw e;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  useEffect(() => {
    // Expose logout to window for api.js
    window.logout = logout;

    // Listen for storage events (e.g. from other tabs)
    const handleStorageChange = (e) => {
      if (e.key === 'token' && !e.newValue) {
        logout();
      }
    };
    window.addEventListener('storage', handleStorageChange);
    return () => {
      delete window.logout;
      window.removeEventListener('storage', handleStorageChange);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ token, user, isAuthenticated: !!token, login, logout, loading }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
