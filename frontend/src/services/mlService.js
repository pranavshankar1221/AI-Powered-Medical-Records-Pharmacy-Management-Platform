import api from './api';

export const predictDemand = async (data) => {
  const response = await api.post('/api/ml/predict-demand', data);
  return response.data;
};

export const predictExpiryRisk = async (data) => {
  const response = await api.post('/api/ml/predict-expiry-risk', data);
  return response.data;
};

export const getModelInfo = async () => {
  const response = await api.get('/api/ml/model-info');
  return response.data;
};

export const getBatchPredictions = async () => {
  const response = await api.get('/api/ml/batch-predictions');
  return response.data;
};

export const getSystemStatus = async () => {
  const response = await api.get('/api/monitoring/system');
  return response.data;
};
