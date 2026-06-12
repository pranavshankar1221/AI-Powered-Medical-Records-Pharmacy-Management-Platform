import api from './api';

export const getPatientDashboard = async () => {
  const response = await api.get('/api/patient/dashboard');
  return response.data;
};

export const getReminders = async () => {
  const response = await api.get('/api/patient/reminders');
  return response.data;
};

export const createReminder = async (reminderData) => {
  const response = await api.post('/api/patient/reminders', reminderData);
  return response.data;
};

export const updateReminder = async (reminderId, reminderData) => {
  const response = await api.put(`/api/patient/reminders/${reminderId}`, reminderData);
  return response.data;
};

export const deleteReminder = async (reminderId) => {
  const response = await api.delete(`/api/patient/reminders/${reminderId}`);
  return response.data;
};

export const getMedicineExplanation = async (medicineId) => {
  const response = await api.get(`/api/patient/medicine-explanation/${medicineId}`);
  return response.data;
};

export const getPrescriptionSummary = async (billToken) => {
  const response = await api.post('/api/patient/prescription-summary', { bill_token: billToken });
  return response.data;
};

export const autoSetReminders = async (billToken) => {
  const response = await api.post('/api/patient/reminders/auto-set', { bill_token: billToken });
  return response.data;
};
