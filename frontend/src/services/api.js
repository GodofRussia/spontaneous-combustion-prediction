import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_TIMEOUT = import.meta.env.VITE_API_TIMEOUT || 30000;

const apiClient = axios.create({
  baseURL: `${API_URL}/api`,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.message || error.message || 'Произошла ошибка';
    return Promise.reject(new Error(message));
  }
);

// Upload methods
const uploadFile = async (file, fileType) => {
  const formData = new FormData();
  formData.append('file', file);
  return apiClient.post(`/upload/csv?file_type=${fileType}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const uploadSupplies = (file) => uploadFile(file, 'supplies');
export const uploadFires = (file) => uploadFile(file, 'fires');
export const uploadTemperature = (file) => uploadFile(file, 'temperature');
export const uploadWeather = (file) => uploadFile(file, 'weather');

// Prediction methods
export const triggerPrediction = async (horizonDays = 3) => {
  return apiClient.post('/predict', { horizon_days: horizonDays });
};

export const getPredictions = async (params) => {
  return apiClient.post('/predict', params);
};

export const getPrediction = async (predictionId) => {
  return apiClient.get(`/predict/${predictionId}`);
};

// Metrics methods
export const evaluateMetrics = async (predictionId, firesUploadId) => {
  return apiClient.post('/metrics/evaluate', {
    prediction_id: predictionId,
    fires_upload_id: firesUploadId,
  });
};

export const evaluatePredictions = async () => {
  return apiClient.post('/evaluate', {
    prediction_id: 'latest',
    reference_data_path: null,
  });
};

export const getMetricsSummary = async () => {
  return apiClient.get('/metrics/summary');
};

// Data methods
export const getPiles = async (filters = {}) => {
  return apiClient.get('/data/piles', { params: filters });
};

export const getCalendarData = async (startDate, endDate, stockyard = null) => {
  const params = { start_date: startDate, end_date: endDate };
  if (stockyard) params.stockyard = stockyard;
  return apiClient.get('/data/calendar', { params });
};

export default apiClient;