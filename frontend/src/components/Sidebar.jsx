import {useState, useEffect} from 'react';

const Sidebar = () => {
  const [dateRange, setDateRange] = useState(null);

  useEffect(() => {
    // Load date range from localStorage
    const storedDateRange = localStorage.getItem('predictionDateRange');
    if (storedDateRange) {
      try {
        const parsedDateRange = JSON.parse(storedDateRange);
        setDateRange(parsedDateRange);
      } catch (e) {
        console.error('Error parsing date range:', e);
      }
    }

    // Listen for storage changes
    const handleStorageChange = () => {
      const updatedDateRange = localStorage.getItem('predictionDateRange');
      if (updatedDateRange) {
        try {
          setDateRange(JSON.parse(updatedDateRange));
        } catch (e) {
          console.error('Error parsing date range:', e);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  return (
    <aside className="sidebar">
      {dateRange && (
        <div className="sidebar-section">
          <h3 className="sidebar-title">📅 Период данных</h3>
          <div className="date-range-info">
            <p className="date-range-text">
              {new Date(dateRange.data_start_date).toLocaleDateString('ru-RU', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
              })}
              {' - '}
              {new Date(dateRange.data_end_date).toLocaleDateString('ru-RU', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
              })}
            </p>
            {dateRange.years && dateRange.years.length > 0 && (
              <p className="years-info">
                <strong>Годы:</strong> {dateRange.years.join(', ')}
              </p>
            )}
          </div>
        </div>
      )}

      <div className="sidebar-section">
        <h3 className="sidebar-title">Уровни риска</h3>
        <div className="risk-legend">
          <div className="risk-item">
            <span className="risk-badge critical"></span>
            <span>Критический (0-2 дня)</span>
          </div>
          <div className="risk-item">
            <span className="risk-badge high"></span>
            <span>Высокий (3-7 дней)</span>
          </div>
          <div className="risk-item">
            <span className="risk-badge medium"></span>
            <span>Средний (8-14 дней)</span>
          </div>
          <div className="risk-item">
            <span className="risk-badge low"></span>
            <span>Низкий ({'>'}14 дней)</span>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;