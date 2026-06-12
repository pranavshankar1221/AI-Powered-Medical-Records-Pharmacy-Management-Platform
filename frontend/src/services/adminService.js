import api from './api';

export const getAdminDashboardStats = async () => {
  const response = await api.get('/api/admin/dashboard');
  return response.data;
};

export const getSalesTrend = async (months = 12) => {
  const response = await api.get(`/api/admin/analytics/sales-trend?months=${months}`);
  return response.data;
};

export const getCategoryAnalysis = async () => {
  const response = await api.get('/api/admin/analytics/category-analysis');
  return response.data;
};

export const getTopMedicines = async (limit = 10) => {
  const response = await api.get(`/api/admin/analytics/top-medicines?limit=${limit}`);
  return response.data;
};

export const getInventoryDistribution = async () => {
  const response = await api.get('/api/admin/analytics/inventory-distribution');
  return response.data;
};

export const getUsers = async (role) => {
  const response = await api.get(`/api/admin/users${role ? `?role=${role}` : ''}`);
  return response.data;
};
