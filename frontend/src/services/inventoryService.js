import api from './api';

export const getMedicines = async (params) => {
  const response = await api.get('/api/inventory/medicines', { params });
  return response.data;
};

export const getMedicine = async (medicineId) => {
  const response = await api.get(`/api/inventory/medicines/${medicineId}`);
  return response.data;
};

export const createMedicine = async (medicineData) => {
  const response = await api.post('/api/inventory/medicines', medicineData);
  return response.data;
};

export const updateMedicine = async (medicineId, medicineData) => {
  const response = await api.put(`/api/inventory/medicines/${medicineId}`, medicineData);
  return response.data;
};

export const deleteMedicine = async (medicineId) => {
  const response = await api.delete(`/api/inventory/medicines/${medicineId}`);
  return response.data;
};

export const getBatches = async (params) => {
  const response = await api.get('/api/inventory/batches', { params });
  return response.data;
};

export const createBatch = async (batchData) => {
  const response = await api.post('/api/inventory/batches', batchData);
  return response.data;
};

export const getCategories = async () => {
  const response = await api.get('/api/inventory/categories');
  return response.data;
};

export const getAlerts = async () => {
  const response = await api.get('/api/inventory/alerts');
  return response.data;
};
