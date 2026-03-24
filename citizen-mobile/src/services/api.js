import axios from 'axios';

// The API URL will be overridden by the user after they see it from the bridge output
// Or we can attempt to detect it if running through a specific tunnel configuration
// Smart API detection for mobile/ngrok environments
const getApiBaseUrl = () => {
  // Check for manual override in localStorage (useful for debugging mobile/ngrok)
  const manualUrl = localStorage.getItem('SENTINEL_API_URL');
  if (manualUrl) return manualUrl;

  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL;
  
  const host = window.location.hostname;
  return host.includes('ngrok-free.dev') ? `https://${host}` : 'http://localhost:5000';
};

const API_BASE_URL = getApiBaseUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to include the JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor for handling 401 Unauthorized
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      console.warn("Unauthorized! Clearing stale session...");
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      // window.location.href = '/login'; // Optional: Auto-redirect
    }
    return Promise.reject(error);
  }
);

export default api;
export { API_BASE_URL };
