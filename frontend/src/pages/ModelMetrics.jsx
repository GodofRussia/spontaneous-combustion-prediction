import {useState, useEffect} from 'react';
import MetricsChart from '../components/MetricsChart';
import {calculateMetricsSummary} from '../services/dataProcessor';

const ModelMetrics = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // В реальном приложении здесь будет загрузка данных из API
    // Для демонстрации используем моковые данные
    const mockMetrics = {
      mae: 1.85,
      rmse: 2.34,
      accuracy_pm1: 0.52,
      accuracy_pm2: 0.73,
      accuracy_pm3: 0.85,
      total_predictions: 100,
      correct_pm2: 73,
    };
    setMetrics(mockMetrics);
  }, []);

  const summary = calculateMetricsSummary(metrics);

  return (
    <div className="metrics-page">
      <div className="page-header">
        <h2>Метрики модели</h2>
        <p className="page-description">
          Оценка качества прогнозирования возгораний угля
        </p>
      </div>

      {metrics && (
        <>
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-label">MAE (дни)</div>
              <div className="metric-value">{summary.mae}</div>
              <div className="metric-description">Средняя абсолютная ошибка</div>
            </div>

            <div className={`metric-card ${summary.meetsTarget ? 'success' : 'warning'}`}>
              <div className="metric-label">Точность ±2 дня</div>
              <div className="metric-value">{summary.accuracyPm2}</div>
              <div className="metric-description">
                {summary.meetsTarget ? '✓ Цель достигнута (≥70%)' : '⚠ Ниже целевого значения'}
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-label">Всего прогнозов</div>
              <div className="metric-value">{summary.totalPredictions}</div>
              <div className="metric-description">Количество штабелей</div>
            </div>

            <div className="metric-card">
              <div className="metric-label">Верных прогнозов</div>
              <div className="metric-value">{summary.correctPm2}</div>
              <div className="metric-description">В пределах ±2 дня</div>
            </div>
          </div>

          <div className="chart-section">
            <MetricsChart metrics={metrics} />
          </div>

          <div className="metrics-details">
            <h3>Детальная статистика</h3>
            <table className="metrics-table">
              <thead>
                <tr>
                  <th>Метрика</th>
                  <th>Значение</th>
                  <th>Описание</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>MAE</td>
                  <td>{metrics.mae.toFixed(2)} дней</td>
                  <td>Средняя абсолютная ошибка прогноза</td>
                </tr>
                <tr>
                  <td>RMSE</td>
                  <td>{metrics.rmse.toFixed(2)} дней</td>
                  <td>Среднеквадратичная ошибка</td>
                </tr>
                <tr>
                  <td>Точность ±1 день</td>
                  <td>{(metrics.accuracy_pm1 * 100).toFixed(1)}%</td>
                  <td>Прогнозы с точностью до 1 дня</td>
                </tr>
                <tr className="highlight">
                  <td>Точность ±2 дня</td>
                  <td>{(metrics.accuracy_pm2 * 100).toFixed(1)}%</td>
                  <td>Целевая метрика (≥70%)</td>
                </tr>
                <tr>
                  <td>Точность ±3 дня</td>
                  <td>{(metrics.accuracy_pm3 * 100).toFixed(1)}%</td>
                  <td>Прогнозы с точностью до 3 дней</td>
                </tr>
              </tbody>
            </table>
          </div>
        </>
      )}

      {loading && (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Загрузка метрик...</p>
        </div>
      )}
    </div>
  );
};

export default ModelMetrics;