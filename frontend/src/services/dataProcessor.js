import {format, parseISO} from 'date-fns';
import {ru} from 'date-fns/locale';

export const formatDate = (date) => {
  if (!date) return '';
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return format(dateObj, 'dd.MM.yyyy', { locale: ru });
};

export const formatDateTime = (date) => {
  if (!date) return '';
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return format(dateObj, 'dd.MM.yyyy HH:mm', { locale: ru });
};

export const getRiskColor = (riskLevel) => {
  const colors = {
    critical: '#dc2626',
    high: '#ea580c',
    medium: '#eab308',
    low: '#16a34a',
  };
  return colors[riskLevel] || colors.low;
};

// Safe value formatter to handle NaN, null, undefined
export const formatValue = (value, defaultValue = '—') => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return defaultValue;
  }
  return value;
};

// Safe number formatter
export const formatNumber = (value, decimals = 1, defaultValue = '—') => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return defaultValue;
  }
  return Number(value).toFixed(decimals);
};

// Safe percentage formatter
export const formatPercentage = (value, decimals = 0, defaultValue = '—') => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return defaultValue;
  }
  return `${(Number(value) * 100).toFixed(decimals)}%`;
};

// Format confidence level from string to Russian text
export const formatConfidence = (confidence, defaultValue = '—') => {
  if (!confidence) {
    return defaultValue;
  }
  const confidenceMap = {
    high: 'Высокая',
    medium: 'Средняя',
    low: 'Низкая',
  };
  return confidenceMap[confidence.toLowerCase()] || defaultValue;
};

export const getRiskLabel = (riskLevel) => {
  const labels = {
    critical: 'Критический',
    high: 'Высокий',
    medium: 'Средний',
    low: 'Низкий',
  };
  return labels[riskLevel] || 'Неизвестно';
};

export const processCalendarEvents = (predictions) => {
  return predictions.map((pred) => ({
    id: `pile_${pred.pile_id}`,
    title: `Штабель #${pred.pile_id} - ${pred.coal_grade}\nСклад ${pred.stockyard} | ${pred.predicted_days_to_fire_rounded} дней`,
    start: pred.predicted_fire_date,
    extendedProps: {
      ...pred,
      pileId: pred.pile_id,
      daysToFire: pred.predicted_days_to_fire_rounded,
    },
    backgroundColor: getRiskColor(pred.risk_level),
    borderColor: getRiskColor(pred.risk_level),
  }));
};

export const calculateMetricsSummary = (metrics) => {
  if (!metrics) return null;

  return {
    mae: metrics.mae?.toFixed(2) || 'N/A',
    accuracyPm2: `${(metrics.accuracy_pm2 * 100).toFixed(1)}%`,
    totalPredictions: metrics.total_predictions || 0,
    correctPm2: metrics.correct_pm2 || 0,
    meetsTarget: metrics.accuracy_pm2 >= 0.7,
  };
};

export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
};

export const validateCSVFile = (file) => {
  const maxSize = import.meta.env.VITE_MAX_FILE_SIZE || 52428800; // 50MB

  if (!file.name.endsWith('.csv')) {
    return { valid: false, error: 'Файл должен быть в формате CSV' };
  }

  if (file.size > maxSize) {
    return { valid: false, error: `Размер файла не должен превышать ${formatFileSize(maxSize)}` };
  }

  return { valid: true };
};