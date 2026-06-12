import React, { createContext, useState, useEffect, useContext } from 'react';
import api from '../services/api'; // Use the configured axios instance with interceptors

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [loading, setLoading] = useState(true);

  // On mount: verify stored token and load profile
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      // The api.js interceptor will automatically attach the token from localStorage
      fetchProfile();
    } else {
      setUser(null);
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchProfile = async () => {
    try {
      const storedToken = localStorage.getItem('token');
      if (!storedToken) {
        setLoading(false);
        return;
      }
      const response = await api.get('/api/auth/me');
      if (response.data.success) {
        setUser(response.data.user);
      } else {
        clearAuth();
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
      clearAuth();
    } finally {
      setLoading(false);
    }
  };

  const clearAuth = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const login = async (username, password) => {
    setLoading(true);
    try {
      const response = await api.post('/api/auth/login', { username, password });
      if (response.data.success) {
        const { access_token, user: loggedUser } = response.data;
        // Store token FIRST so the api.js interceptor picks it up immediately
        localStorage.setItem('token', access_token);
        setToken(access_token);
        setUser(loggedUser);
        setLoading(false);
        return { success: true, user: loggedUser };
      }
      setLoading(false);
      return { success: false, error: response.data.message || 'Login failed' };
    } catch (error) {
      console.error('Login error:', error);
      const errorMsg = error.response?.data?.detail || 'Invalid username or password';
      setLoading(false);
      return { success: false, error: errorMsg };
    }
  };

  const register = async (userData) => {
    setLoading(true);
    try {
      const response = await api.post('/api/auth/register', userData);
      if (response.data.success) {
        setLoading(false);
        return { success: true };
      }
      setLoading(false);
      return { success: false, error: response.data.message || 'Registration failed' };
    } catch (error) {
      console.error('Registration error:', error);
      let errorMsg = 'Registration failed';
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          errorMsg = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          errorMsg = error.response.data.detail[0].msg || 'Validation error';
        } else {
          errorMsg = JSON.stringify(error.response.data.detail);
        }
      } else if (error.message) {
        errorMsg = error.message;
      }
      setLoading(false);
      return { success: false, error: errorMsg };
    }
  };

  const logout = () => {
    clearAuth();
  };

  const contextValue = { user, token, loading, login, register, logout, fetchProfile };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// Named export for useAuth hook
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
