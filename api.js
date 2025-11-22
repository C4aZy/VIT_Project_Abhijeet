// src/services/api.js
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
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

// Response interceptor - handle errors
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

export default api;


// src/services/auth.js
import api from './api';

export const authService = {
  async register(userData) {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },

  async login(credentials) {
    const response = await api.post('/auth/login', credentials, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    const { access_token } = response.data;
    localStorage.setItem('token', access_token);
    return response.data;
  },

  async getCurrentUser() {
    const response = await api.get('/auth/me');
    return response.data;
  },

  logout() {
    localStorage.removeItem('token');
    window.location.href = '/login';
  },

  isAuthenticated() {
    return !!localStorage.getItem('token');
  },
};


// src/services/projects.js
import api from './api';

export const projectService = {
  async createProject(projectData) {
    const response = await api.post('/projects', projectData);
    return response.data;
  },

  async getProjects() {
    const response = await api.get('/projects');
    return response.data;
  },

  async getProject(projectId) {
    const response = await api.get(`/projects/${projectId}`);
    return response.data;
  },

  async deleteProject(projectId) {
    await api.delete(`/projects/${projectId}`);
  },

  async uploadFiles(projectId, files) {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await api.post(`/projects/${projectId}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};


// src/services/analysis.js
import api from './api';

export const analysisService = {
  async startAnalysis(projectId) {
    const response = await api.post(`/analysis/run/${projectId}`);
    return response.data;
  },

  async getAnalysisStatus(projectId) {
    const response = await api.get(`/analysis/status/${projectId}`);
    return response.data;
  },

  async getAnalysisResults(projectId) {
    const response = await api.get(`/analysis/results/${projectId}`);
    return response.data;
  },
};


// src/context/AuthContext.jsx
import React, { createContext, useState, useContext, useEffect } from 'react';
import { authService } from '../services/auth';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      if (authService.isAuthenticated()) {
        const userData = await authService.getCurrentUser();
        setUser(userData);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      authService.logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (credentials) => {
    const data = await authService.login(credentials);
    await checkAuth();
    return data;
  };

  const register = async (userData) => {
    const data = await authService.register(userData);
    return data;
  };

  const logout = () => {
    authService.logout();
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};


// src/hooks/useAnalysis.js
import { useState, useEffect } from 'react';
import { analysisService } from '../services/analysis';

export const useAnalysis = (projectId) => {
  const [analysis, setAnalysis] = useState(null);
  const [status, setStatus] = useState('not_started');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const startAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      await analysisService.startAnalysis(projectId);
      setStatus('processing');
      pollStatus();
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const pollStatus = async () => {
    const interval = setInterval(async () => {
      try {
        const statusData = await analysisService.getAnalysisStatus(projectId);
        setStatus(statusData.status);

        if (statusData.status === 'completed') {
          clearInterval(interval);
          await fetchResults();
        }
      } catch (err) {
        clearInterval(interval);
        setError(err.message);
        setLoading(false);
      }
    }, 3000); // Poll every 3 seconds

    return () => clearInterval(interval);
  };

  const fetchResults = async () => {
    try {
      const results = await analysisService.getAnalysisResults(projectId);
      setAnalysis(results);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    if (projectId) {
      fetchResults().catch(() => {
        // Analysis not available yet
        setLoading(false);
      });
    }
  }, [projectId]);

  return {
    analysis,
    status,
    loading,
    error,
    startAnalysis,
    refetch: fetchResults,
  };
};


// src/utils/constants.js
export const SEVERITY_COLORS = {
  critical: 'text-red-600 bg-red-50',
  high: 'text-orange-500 bg-orange-50',
  medium: 'text-yellow-500 bg-yellow-50',
  low: 'text-blue-500 bg-blue-50',
  info: 'text-gray-500 bg-gray-50',
};

export const CATEGORY_LABELS = {
  bug: 'Bug',
  security: 'Security',
  performance: 'Performance',
  code_smell: 'Code Smell',
  complexity: 'Complexity',
  documentation: 'Documentation',
  style: 'Style',
  duplication: 'Duplication',
};

export const LANGUAGE_EXTENSIONS = {
  python: '.py',
  javascript: '.js',
  typescript: '.ts',
  java: '.java',
  cpp: '.cpp',
  csharp: '.cs',
  go: '.go',
  rust: '.rs',
  ruby: '.rb',
  php: '.php',
};


// src/utils/helpers.js
export const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const getQualityColor = (score) => {
  if (score >= 90) return 'text-green-600';
  if (score >= 70) return 'text-blue-600';
  if (score >= 50) return 'text-yellow-600';
  return 'text-red-600';
};

export const getQualityLabel = (score) => {
  if (score >= 90) return 'Excellent';
  if (score >= 70) return 'Good';
  if (score >= 50) return 'Fair';
  return 'Poor';
};

export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
};

export const truncateText = (text, maxLength = 50) => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};