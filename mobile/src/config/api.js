// API Configuration for MEDIQR
// Frontend and Flask backend are deployed on the same Render service.

const API_CONFIG = {
  // Empty string means use the same domain as the frontend.
  // Example:
  // https://your-app.onrender.com/api/auth/register
  BASE_URL: "",
  
  TIMEOUT: 10000,
};

export default API_CONFIG;