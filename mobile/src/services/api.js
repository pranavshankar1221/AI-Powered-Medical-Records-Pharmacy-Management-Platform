import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import API_CONFIG from '../config/api';

// Create axios instance
const api = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, clear storage
      await AsyncStorage.removeItem('authToken');
      await AsyncStorage.removeItem('user');
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (email, password) => {
    const response = await api.post('/api/auth/login', { username: email, password });
    return response.data;
  },
  
  register: async (userData) => {
    const response = await api.post('/api/auth/register', userData);
    return response.data;
  },
};

// Patient API
export const patientAPI = {
  getBillDetails: async (token) => {
    const response = await api.get(`/api/billing/scan/${token}`);
    return response.data;
  },
  
  createReminder: async (reminderData) => {
    const payload = {
      medicine_name: reminderData.medicine_name,
      dosage: reminderData.dosage || "",
      time_of_day: reminderData.reminder_type || "morning",
      custom_time: reminderData.reminder_time || null,
      scheduled_date: reminderData.scheduled_date || null,
      notes: reminderData.notes || "",
    };
    const response = await api.post('/api/patient/reminders', payload);
    return response.data;
  },
  
  getReminders: async () => {
    const response = await api.get('/api/patient/reminders');
    return response.data;
  },
};

// Pharmacist API
export const pharmacistAPI = {
  getInventory: async () => {
    const response = await api.get('/api/inventory/medicines');
    return response.data;
  },
  
  addMedicine: async (medicineData) => {
    // 1. Create medicine catalog entry
    const medResponse = await api.post('/api/inventory/medicines', {
      name: medicineData.medicine_name,
      generic_name: medicineData.generic_name || "",
      category: medicineData.category || "",
      unit_price: parseFloat(medicineData.price_per_unit) || 0.0,
    });

    const createdMed = medResponse.data.data;

    // 2. If quantity is specified, create initial stock batch
    if (createdMed && medicineData.quantity > 0) {
      const batchNo = `BCH-${Date.now()}`;
      let expiryDate = medicineData.expiry_date;
      if (!expiryDate) {
        const d = new Date();
        d.setFullYear(d.getFullYear() + 1);
        expiryDate = d.toISOString().split('T')[0];
      }

      await api.post('/api/inventory/batches', {
        medicine_id: createdMed.medicine_id,
        batch_number: batchNo,
        expiry_date: expiryDate,
        quantity_received: parseInt(medicineData.quantity),
        supplier: "Initial Stock",
      });
    }
    return medResponse.data;
  },
  
  createBill: async (billData) => {
    const response = await api.post('/api/billing/create', billData);
    return response.data;
  },
  
  getBill: async (billId) => {
    const response = await api.get(`/api/billing/bills/${billId}`);
    return response.data;
  },
};

// Medicine Graph API (Neo4j)
export const medicineGraphAPI = {
  checkDrugInteractions: async (medicineIds) => {
    const response = await api.post('/api/medicine-graph/check-drug-interactions', {
      medicine_ids: medicineIds,
    });
    return response.data;
  },
  
  checkFoodInteractions: async (medicineIds) => {
    const response = await api.post('/api/medicine-graph/check-food-interactions', {
      medicine_ids: medicineIds,
    });
    return response.data;
  },
  
  getAlternatives: async (medicineId, limit = 5) => {
    const response = await api.post('/api/medicine-graph/get-alternatives', {
      medicine_id: medicineId,
      limit,
    });
    return response.data;
  },
  
  getMedicineDetails: async (medicineId) => {
    const response = await api.post('/api/medicine-graph/medicine-details', {
      medicine_id: medicineId,
    });
    return response.data;
  },
};

export default api;
