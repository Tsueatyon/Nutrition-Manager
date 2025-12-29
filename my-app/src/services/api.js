import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (import.meta.env.PROD 
    ? 'https://nutrition-app-669815551448.us-central1.run.app'
    : 'https://nutrition-app-669815551448.us-central1.run.app');

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {'Content-Type': 'application/json'},
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 || error.response?.status === 999) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (data) => api.post('/register', data),
  login: (data) => api.post('/login', data),
};

export const profileAPI = {
  get: () => api.get('/my_profile'),
  update: (data) => api.post('/profile_edit', data),
};

export const foodLogAPI = {
  create: (data) => api.post('/insert_log', data),
  update: (data) => api.post('/update_log', data),
  delete: (data) => api.post('/delete_log', data),
  getAll: (date) => api.get('/retrieve_log', { params: { date } }),
};

export const dailySummaryAPI = {
  get: () => api.get('/dv_summation'),
};

export const dailyNeedsAPI = {
  get: () => api.get('/daily_needs'),
};

export const historyAPI = {
  get30Days: () => api.get('/history_30days'),
};

export const chatAPI = {
  sendMessage: (message, history) => api.post('/api/chat', { message, history }),
};

export default api;

