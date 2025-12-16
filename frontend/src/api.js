import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
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

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    return api.post('/api/v1/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
  },
  register: (userData) => 
    api.post('/api/v1/auth/register', userData),
  getCurrentUser: () => 
    api.get('/api/v1/auth/me'),
};

// Tickets API
export const ticketsAPI = {
  list: (params) => 
    api.get('/api/v1/tickets/', { params }),
  get: (ticketId) => 
    api.get(`/api/v1/tickets/${ticketId}`),
  create: (ticketData) => 
    api.post('/api/v1/tickets/', ticketData),
  update: (ticketId, updateData) => 
    api.patch(`/api/v1/tickets/${ticketId}`, updateData),
  close: (ticketId) => 
    api.post(`/api/v1/tickets/${ticketId}/close`),
  getAuditLogs: (ticketId) => 
    api.get(`/api/v1/tickets/${ticketId}/audit-logs`),
};

// Dashboard API
export const dashboardAPI = {
  getStats: () => 
    api.get('/api/v1/dashboard/stats'),
  getActivity: (limit = 50) => 
    api.get('/api/v1/dashboard/activity', { params: { limit } }),
  getResolutionMetrics: (days = 30) => 
    api.get('/api/v1/dashboard/metrics/resolution-time', { params: { days } }),
  getCategoryPerformance: () => 
    api.get('/api/v1/dashboard/metrics/category-performance'),
};

// Automation API
export const automationAPI = {
  listExecutions: (params) => 
    api.get('/api/v1/automation/executions', { params }),
  retryExecution: (executionId) => 
    api.post(`/api/v1/automation/executions/${executionId}/retry`),
  listApprovals: (status = 'pending') => 
    api.get('/api/v1/automation/approvals', { params: { status } }),
  approveAutomation: (approvalId, data) => 
    api.post(`/api/v1/automation/approvals/${approvalId}/approve`, data),
  listPolicies: () => 
    api.get('/api/v1/automation/policies'),
  createPolicy: (policyData) => 
    api.post('/api/v1/automation/policies', policyData),
  updatePolicy: (policyId, policyData) => 
    api.patch(`/api/v1/automation/policies/${policyId}`, policyData),
  deletePolicy: (policyId) => 
    api.delete(`/api/v1/automation/policies/${policyId}`),
};

export default api;
