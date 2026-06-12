import api from './api';

export const login = async (username, password) => {
  const response = await api.post('/api/auth/login', { username, password });
  return response.data;
};

export const register = async (userData) => {
  const response = await api.post('/api/auth/register', userData);
  return response.data;
};

export const getProfile = async () => {
  const response = await api.get('/api/auth/me');
  return response.data;
};

export const updateProfile = async (data) => {
  const response = await api.put('/api/auth/me', data);
  return response.data;
};
