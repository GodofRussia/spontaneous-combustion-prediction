import {formatDate, formatNumber, formatConfidence, formatValue} from '../services/dataProcessor';
import RiskBadge from './RiskBadge';

const PredictionCard = ({ prediction }) => {
  return (
    <div className="prediction-card">
      <div className="card-header">
        <h3>Штабель #{prediction.pile_id}</h3>
        <RiskBadge level={prediction.risk_level} />
      </div>

      <div className="card-body">
        <div className="card-row">
          <span className="label">Склад:</span>
          <span className="value">{formatValue(prediction.stockyard, 'Нет данных')}</span>
        </div>

        <div className="card-row">
          <span className="label">Марка угля:</span>
          <span className="value">{formatValue(prediction.coal_grade, 'Нет данных')}</span>
        </div>

        <div className="card-row">
          <span className="label">Дата наблюдения:</span>
          <span className="value">{formatDate(prediction.observation_date) || '—'}</span>
        </div>

        <div className="card-row">
          <span className="label">Прогноз возгорания:</span>
          <span className="value highlight">{formatDate(prediction.predicted_fire_date) || '—'}</span>
        </div>

        <div className="card-row">
          <span className="label">Прогноз (дней от наблюдения):</span>
          <span className="value">{formatValue(prediction.predicted_days_to_fire_rounded || Math.round(prediction.days_to_fire))}</span>
        </div>

        <div className="card-row">
          <span className="label">Запас (тонн):</span>
          <span className="value">{formatNumber(prediction.features?.stock_tons || prediction.stock_tons, 1)}</span>
        </div>

        <div className="card-row">
          <span className="label">Средняя температура:</span>
          <span className="value">{formatNumber(prediction.features?.temp_max_mean || prediction.temp_max_mean, 1) !== '—' ? `${formatNumber(prediction.features?.temp_max_mean || prediction.temp_max_mean, 1)}°C` : '—'}</span>
        </div>

        <div className="card-row">
          <span className="label">Уверенность:</span>
          <span className="value">{formatConfidence(prediction.confidence)}</span>
        </div>
      </div>
    </div>
  );
};

export default PredictionCard;