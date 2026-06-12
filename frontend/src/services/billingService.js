import api from './api';

export const createBill = async (billData) => {
  const response = await api.post('/api/billing/create', billData);
  return response.data;
};

export const getBills = async (params) => {
  const response = await api.get('/api/billing/bills', { params });
  return response.data;
};

export const getBill = async (billId) => {
  const response = await api.get(`/api/billing/bills/${billId}`);
  return response.data;
};

export const getScanBill = async (billToken) => {
  // Public endpoint
  const response = await api.get(`/api/billing/scan/${billToken}`);
  return response.data;
};

export const getQrCodeUrl = (billToken) => {
  return `${api.defaults.baseURL}/api/billing/qr/${billToken}`;
};
