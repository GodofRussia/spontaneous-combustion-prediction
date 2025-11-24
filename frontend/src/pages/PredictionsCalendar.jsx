import {useState, useEffect, useRef, useMemo} from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import {processCalendarEvents} from '../services/dataProcessor';
import {getPredictions, evaluatePredictions} from '../services/api';
import PredictionCard from '../components/PredictionCard';

const PredictionsCalendar = () => {
  const [predictions, setPredictions] = useState([]);
  const [selectedPrediction, setSelectedPrediction] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState(null);
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [availableYears, setAvailableYears] = useState([]);
  const [realFiresData, setRealFiresData] = useState(null);
  const [showComparison, setShowComparison] = useState(false);
  const [evaluationMetrics, setEvaluationMetrics] = useState(null);
  const [selectedPiles, setSelectedPiles] = useState(new Set());
  const [availablePiles, setAvailablePiles] = useState([]);
  const [showPileFilter, setShowPileFilter] = useState(false);
  const calendarRef = useRef(null);

  useEffect(() => {
    const fetchPredictions = async () => {
      setLoading(true);
      try {
        const response = await getPredictions({ horizon_days: 30 });
        setPredictions(response.predictions);

        // Извлекаем уникальные штабели
        const piles = [...new Set(response.predictions.map(p => p.pile_id))].sort((a, b) => a - b);
        setAvailablePiles(piles);
        // По умолчанию выбираем все штабели
        setSelectedPiles(new Set(piles));

        if (response.date_range) {
          setDateRange(response.date_range);
          localStorage.setItem('predictionDateRange', JSON.stringify(response.date_range));

          const years = response.date_range.data_years || [];
          setAvailableYears(years);

          const primaryYear = response.date_range.primary_year || (years.length > 0 ? years[years.length - 1] : new Date().getFullYear());
          setCurrentYear(primaryYear);

          // Update calendar view to last date with data
          if (calendarRef.current) {
            const calendarApi = calendarRef.current.getApi();
            calendarApi.gotoDate(response.date_range.data_end_date);
          }
        }
      } catch (error) {
        console.error("Error fetching predictions:", error);
        // Try to load from local storage as a fallback
        const storedPredictions = localStorage.getItem('predictions');
        if (storedPredictions) {
          setPredictions(JSON.parse(storedPredictions));
        }
      } finally {
        setLoading(false);
      }
    };

    fetchPredictions();
  }, []);

  const loadRealFiresData = async () => {
    const firesUploaded = localStorage.getItem('firesUploaded') === 'true';
    if (!firesUploaded) {
      alert('Для сравнения необходимо сначала загрузить файл fires.csv на странице Dashboard.');
      return;
    }

    try {
      setLoading(true);
      const response = await evaluatePredictions();
      if (!response || !response.matched_predictions) {
        throw new Error("Ответ от сервера не содержит данных для сравнения.");
      }
      setRealFiresData(response.matched_predictions || []);
      setEvaluationMetrics({
        mae: response.mae,
        accuracy_pm1: response.accuracy_pm1,
        accuracy_pm2: response.accuracy_pm2,
        accuracy_pm3: response.accuracy_pm3,
        total_predictions: response.total_predictions,
        correct_pm2: response.correct_pm2
      });
      setShowComparison(true);
    } catch (error) {
      console.error('Error loading real fires data:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Не удалось загрузить данные о реальных возгораниях. Убедитесь, что файл fires.csv загружен и сервер доступен.';
      alert(errorMessage);
      setShowComparison(false);
    } finally {
      setLoading(false);
    }
  };

  const events = useMemo(() => {
    if (!predictions || predictions.length === 0) {
      return [];
    }

    // Фильтруем предсказания по выбранным штабелям
    const filteredPredictions = predictions.filter(p =>
      selectedPiles.size === 0 || selectedPiles.has(p.pile_id)
    );

    let allEvents = [];

    if (showComparison && realFiresData && realFiresData.length > 0) {
      // Фильтруем realFiresData по выбранным штабелям
      const filteredRealFires = realFiresData.filter(match =>
        selectedPiles.size === 0 || selectedPiles.has(match.pile_id)
      );

      // Show comparison: predictions, real fires, and matches
      filteredRealFires.forEach(match => {
        const predDate = new Date(match.predicted_fire_date);
        const realDate = new Date(match.real_fire_date);

        if (match.is_match) {
          // Show as a match (green)
          allEvents.push({
            title: `✅ Совпадение: Штабель #${match.pile_id}`,
            start: realDate,
            backgroundColor: '#16a34a',
            borderColor: '#16a34a',
            extendedProps: {
              type: 'match',
              pileId: match.pile_id,
              predictedDate: match.predicted_fire_date,
              realDate: match.real_fire_date,
              daysDifference: match.days_difference,
              stockyard: match.stockyard,
              coalGrade: match.coal_grade
            }
          });
        } else {
          // Show both prediction and real fire separately
          allEvents.push({
            title: `🔮 Прогноз: Штабель #${match.pile_id}`,
            start: predDate,
            backgroundColor: '#3b82f6',
            borderColor: '#3b82f6',
            extendedProps: {
              type: 'prediction',
              pileId: match.pile_id,
              predictedDate: match.predicted_fire_date,
              stockyard: match.stockyard,
              coalGrade: match.coal_grade
            }
          });

          allEvents.push({
            title: `🔥 Реальное: Штабель #${match.pile_id}`,
            start: realDate,
            backgroundColor: '#dc2626',
            borderColor: '#dc2626',
            extendedProps: {
              type: 'real',
              pileId: match.pile_id,
              realDate: match.real_fire_date,
              stockyard: match.stockyard,
              coalGrade: match.coal_grade
            }
          });
        }
      });
    } else {
      allEvents = processCalendarEvents(filteredPredictions);
    }

    const filteredEvents = allEvents.filter(event => {
      const eventYear = new Date(event.start).getFullYear();
      return eventYear === currentYear;
    });

    return filteredEvents;
  }, [predictions, currentYear, showComparison, realFiresData, selectedPiles]);

  const togglePileSelection = (pileId) => {
    setSelectedPiles(prev => {
      const newSet = new Set(prev);
      if (newSet.has(pileId)) {
        newSet.delete(pileId);
      } else {
        newSet.add(pileId);
      }
      return newSet;
    });
  };

  const selectAllPiles = () => {
    setSelectedPiles(new Set(availablePiles));
  };

  const deselectAllPiles = () => {
    setSelectedPiles(new Set());
  };

  const handleEventClick = (info) => {
    const pileId = info.event.extendedProps.pileId;
    const prediction = predictions.find((p) => p.pile_id === pileId);
    setSelectedPrediction(prediction);
  };

  const handleYearChange = (year) => {
    setCurrentYear(year);
    if (calendarRef.current) {
      const calendarApi = calendarRef.current.getApi();
      calendarApi.gotoDate(`${year}-01-01`);
    }
  };

  const getInitialDate = () => {
    if (dateRange && dateRange.data_end_date) {
      return dateRange.data_end_date;
    }
    const storedDateRange = localStorage.getItem('predictionDateRange');
    if (storedDateRange) {
      try {
        const parsed = JSON.parse(storedDateRange);
        if (parsed.data_end_date) {
          return parsed.data_end_date;
        }
      } catch (e) {
        // ignore
      }
    }
    return new Date().toISOString().split('T')[0];
  };

  return (
    <div className="calendar-page">
      <div className="page-header">
        <h2>Календарь прогнозов возгораний</h2>
        <p className="page-description">
          Визуализация прогнозируемых дат возгораний по штабелям
        </p>
        {dateRange && (
          <div className="date-info">
            <span className="info-badge">
              📅 Период данных: {new Date(dateRange.data_start_date).toLocaleDateString('ru-RU')} - {new Date(dateRange.data_end_date).toLocaleDateString('ru-RU')}
            </span>
          </div>
        )}

        {evaluationMetrics && showComparison && (
          <div className="metrics-summary">
            <h3>Метрики точности прогнозов</h3>
            <div className="metrics-grid">
              <div className="metric-item">
                <span className="metric-label">MAE (средняя ошибка):</span>
                <span className="metric-value">{evaluationMetrics.mae.toFixed(2)} дней</span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Точность ±1 день:</span>
                <span className="metric-value">{(evaluationMetrics.accuracy_pm1 * 100).toFixed(1)}%</span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Точность ±2 дня:</span>
                <span className="metric-value">{(evaluationMetrics.accuracy_pm2 * 100).toFixed(1)}%</span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Точность ±3 дня:</span>
                <span className="metric-value">{(evaluationMetrics.accuracy_pm3 * 100).toFixed(1)}%</span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Всего совпадений:</span>
                <span className="metric-value">{evaluationMetrics.total_predictions}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="view-mode-toggle">
        <button
          className={`btn ${!showComparison ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setShowComparison(false)}
        >
          Только прогнозы
        </button>
        <button
          className={`btn ${showComparison ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => {
            if (!realFiresData) {
              loadRealFiresData();
            } else {
              setShowComparison(true);
            }
          }}
          disabled={loading}
        >
          {loading ? 'Загрузка...' : 'Сравнение с реальными данными'}
        </button>
      </div>

      {/* Фильтр по штабелям */}
      <div className="pile-filter-section">
        <button
          className="btn btn-secondary"
          onClick={() => setShowPileFilter(!showPileFilter)}
        >
          {showPileFilter ? '▼' : '▶'} Фильтр по штабелям ({selectedPiles.size} из {availablePiles.length})
        </button>

        {showPileFilter && (
          <div className="pile-filter-content">
            <div className="pile-filter-actions">
              <button className="btn btn-sm btn-secondary" onClick={selectAllPiles}>
                Выбрать все
              </button>
              <button className="btn btn-sm btn-secondary" onClick={deselectAllPiles}>
                Снять все
              </button>
            </div>
            <div className="pile-checkboxes">
              {availablePiles.map(pileId => (
                <label key={pileId} className="pile-checkbox-label">
                  <input
                    type="checkbox"
                    checked={selectedPiles.has(pileId)}
                    onChange={() => togglePileSelection(pileId)}
                  />
                  <span>Штабель {pileId}</span>
                </label>
              ))}
            </div>
          </div>
        )}
      </div>

      {availableYears.length > 1 && (
        <div className="year-selector">
          <label>Выберите год:</label>
          <div className="year-buttons">
            {availableYears.map((year) => (
              <button
                key={year}
                className={`btn ${currentYear === year ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => handleYearChange(year)}
              >
                {year}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="calendar-container">
        <FullCalendar
          ref={calendarRef}
          plugins={[dayGridPlugin, interactionPlugin]}
          initialView="dayGridMonth"
          initialDate={getInitialDate()}
          events={events}
          eventClick={handleEventClick}
          headerToolbar={{
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,dayGridWeek',
          }}
          height="auto"
          locale="ru"
        />
      </div>

      {selectedPrediction && (
        <div className="modal-overlay" onClick={() => setSelectedPrediction(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedPrediction(null)}>
              ×
            </button>
            <PredictionCard prediction={selectedPrediction} />
          </div>
        </div>
      )}
    </div>
  );
};

export default PredictionsCalendar;