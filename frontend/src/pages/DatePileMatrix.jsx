import {useState, useEffect} from 'react';
import {format, parseISO, isValid} from 'date-fns';
import {ru} from 'date-fns/locale';

const DatePileMatrix = () => {
  const [predictions, setPredictions] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [pilesForDate, setPilesForDate] = useState([]);
  const [availableDates, setAvailableDates] = useState([]);
  const [dateStats, setDateStats] = useState({
    total: 0,
    critical: 0,
    high: 0,
    medium: 0,
    low: 0
  });

  // Загрузка прогнозов из localStorage
  useEffect(() => {
    const storedPredictions = localStorage.getItem('predictions');
    if (storedPredictions) {
      try {
        const parsedPredictions = JSON.parse(storedPredictions);
        setPredictions(parsedPredictions);

        // Извлечение уникальных дат
        const dates = [...new Set(parsedPredictions.map(p => p.predicted_fire_date))]
          .filter(date => date && isValid(parseISO(date)))
          .sort();

        setAvailableDates(dates);

        // Установка первой даты по умолчанию
        if (dates.length > 0) {
          setSelectedDate(dates[0]);
        }
      } catch (error) {
        console.error('Error loading predictions:', error);
      }
    }
  }, []);

  // Фильтрация штабелей для выбранной даты
  useEffect(() => {
    if (selectedDate && predictions.length > 0) {
      const filtered = predictions.filter(p => p.predicted_fire_date === selectedDate);
      setPilesForDate(filtered);

      // Подсчет статистики по risk_level
      const stats = {
        total: filtered.length,
        critical: filtered.filter(p => p.risk_level === 'critical').length,
        high: filtered.filter(p => p.risk_level === 'high').length,
        medium: filtered.filter(p => p.risk_level === 'medium').length,
        low: filtered.filter(p => p.risk_level === 'low').length
      };
      setDateStats(stats);
    } else {
      setPilesForDate([]);
      setDateStats({ total: 0, critical: 0, high: 0, medium: 0, low: 0 });
    }
  }, [selectedDate, predictions]);

  // Форматирование даты для отображения
  const formatDate = (dateString) => {
    try {
      const date = parseISO(dateString);
      return format(date, 'd MMMM yyyy', { locale: ru });
    } catch {
      return dateString;
    }
  };

  // Обработчик клика на карточку штабеля
  const handlePileClick = (pile) => {
    console.log('Pile details:', pile);
    const riskLabels = {
      critical: 'Критический',
      high: 'Высокий',
      medium: 'Средний',
      low: 'Низкий'
    };
    alert(`Штабель: ${pile.pile_id}\nУровень риска: ${riskLabels[pile.risk_level] || pile.risk_level}\nДата наблюдения: ${formatDate(pile.observation_date)}\nПрогноз возгорания: ${formatDate(pile.predicted_fire_date)}\nПрогноз (дней от наблюдения): ${pile.predicted_days_to_fire_rounded}`);
  };

  return (
    <div className="date-pile-matrix">
      <h2>Матрица прогнозов: Дата → Штабели</h2>

      {/* Селектор даты */}
      <div className="date-selector">
        <h3>Выберите дату прогноза:</h3>
        {availableDates.length > 0 ? (
          <div className="date-buttons">
            {availableDates.map((date) => (
              <button
                key={date}
                className={`date-button ${selectedDate === date ? 'active' : ''}`}
                onClick={() => setSelectedDate(date)}
              >
                {formatDate(date)}
              </button>
            ))}
          </div>
        ) : (
          <p className="no-data">Нет доступных прогнозов. Загрузите данные на странице Dashboard.</p>
        )}
      </div>

      {/* Информация о выбранной дате */}
      {selectedDate && (
        <div className="date-info">
          <h3>Статистика на {formatDate(selectedDate)}</h3>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-label">Всего штабелей</div>
              <div className="stat-value">{dateStats.total}</div>
            </div>
            <div className="stat-card risk-critical">
              <div className="stat-label">Критический риск</div>
              <div className="stat-value">{dateStats.critical}</div>
            </div>
            <div className="stat-card risk-high">
              <div className="stat-label">Высокий риск</div>
              <div className="stat-value">{dateStats.high}</div>
            </div>
            <div className="stat-card risk-medium">
              <div className="stat-label">Средний риск</div>
              <div className="stat-value">{dateStats.medium}</div>
            </div>
            <div className="stat-card risk-low">
              <div className="stat-label">Низкий риск</div>
              <div className="stat-value">{dateStats.low}</div>
            </div>
          </div>
        </div>
      )}

      {/* Матрица штабелей */}
      {selectedDate && pilesForDate.length > 0 && (
        <div className="piles-section">
          <h3>Штабели с прогнозом возгорания</h3>
          <div className="piles-grid">
            {pilesForDate.map((pile, index) => {
              const riskLevel = pile.risk_level || 'low';
              return (
                <div
                  key={`${pile.pile_id}-${index}`}
                  className={`pile-card risk-${riskLevel}`}
                  onClick={() => handlePileClick(pile)}
                >
                  <div className="pile-header">
                    <h4>Штабель {pile.pile_id}</h4>
                    <span className={`risk-badge risk-${riskLevel}`}>
                      {riskLevel === 'critical' && '🔴'}
                      {riskLevel === 'high' && '🟠'}
                      {riskLevel === 'medium' && '🟡'}
                      {riskLevel === 'low' && '🟢'}
                    </span>
                  </div>
                  <div className="pile-details">
                    <div className="detail-row">
                      <span className="detail-label">Дата наблюдения:</span>
                      <span className="detail-value">
                        {formatDate(pile.observation_date)}
                      </span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">Прогноз (дней):</span>
                      <span className="detail-value">
                        {pile.predicted_days_to_fire_rounded} дн.
                      </span>
                    </div>
                    {pile.stockyard && (
                      <div className="detail-row">
                        <span className="detail-label">Склад:</span>
                        <span className="detail-value">{pile.stockyard}</span>
                      </div>
                    )}
                    {pile.coal_grade && (
                      <div className="detail-row">
                        <span className="detail-label">Марка угля:</span>
                        <span className="detail-value">{pile.coal_grade}</span>
                      </div>
                    )}
                    {pile.confidence && (
                      <div className="detail-row">
                        <span className="detail-label">Уверенность:</span>
                        <span className="detail-value">
                          {pile.confidence === 'high' ? 'Высокая' : pile.confidence === 'medium' ? 'Средняя' : 'Низкая'}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {selectedDate && pilesForDate.length === 0 && (
        <div className="no-piles">
          <p>На выбранную дату нет прогнозов возгорания штабелей.</p>
        </div>
      )}
    </div>
  );
};

export default DatePileMatrix;