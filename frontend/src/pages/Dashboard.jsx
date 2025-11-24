import {useState} from 'react';
import FileUpload from '../components/FileUpload';
import {uploadSupplies, uploadFires, uploadTemperature, uploadWeather, triggerPrediction} from '../services/api';
import {useNavigate} from 'react-router-dom';

const Dashboard = () => {
  const navigate = useNavigate();
  const [files, setFiles] = useState({
    supplies: null,
    fires: null,
    temperature: null,
    weather: [],
  });
  const [predicting, setPredicting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [dateRange, setDateRange] = useState(null);

  const handleUpload = async (type, file) => {
    const uploadFunctions = {
      supplies: uploadSupplies,
      fires: uploadFires,
      temperature: uploadTemperature,
      weather: uploadWeather,
    };

    try {
      await uploadFunctions[type](file);

      if (type === 'weather') {
        // Add to weather files array
        setFiles((prev) => ({
          ...prev,
          weather: [...prev.weather, file]
        }));
      } else {
        setFiles((prev) => ({ ...prev, [type]: file }));
      }

      // Set a flag in localStorage for the fires file
      if (type === 'fires') {
        localStorage.setItem('firesUploaded', 'true');
      }

      setSuccess(`Файл ${file.name} успешно загружен`);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      throw err;
    }
  };

  const handleRemoveWeatherFile = (index) => {
    setFiles((prev) => ({
      ...prev,
      weather: prev.weather.filter((_, i) => i !== index)
    }));
  };

  const handlePredict = async () => {
    if (!files.supplies || !files.temperature || files.weather.length === 0) {
      setError('Необходимо загрузить обязательные файлы: поставки, температура и хотя бы один файл погоды');
      return;
    }

    setPredicting(true);
    setError(null);

    try {
      const result = await triggerPrediction(3);

      // Store date range info if available
      if (result.date_range) {
        setDateRange(result.date_range);
        localStorage.setItem('predictionDateRange', JSON.stringify(result.date_range));
      }

      setSuccess('Прогноз успешно выполнен!');
      setTimeout(() => {
        navigate('/calendar');
      }, 1500);
    } catch (err) {
      setError(err.message || 'Ошибка при выполнении прогноза');
    } finally {
      setPredicting(false);
    }
  };

  const canPredict = files.supplies && files.temperature && files.weather.length > 0;

  return (
    <div className="dashboard">
      <div className="page-header">
        <h2>Загрузка данных</h2>
        <p className="page-description">
          Загрузите CSV файлы с данными для прогнозирования возгораний угля
        </p>
      </div>

      {error && (
        <div className="alert alert-error">
          <span className="alert-icon">⚠️</span>
          {error}
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          <span className="alert-icon">✓</span>
          {success}
        </div>
      )}

      <div className="upload-grid">
        <FileUpload
          label="Поставки (supplies.csv)"
          required
          onUpload={(file) => handleUpload('supplies', file)}
          uploadedFile={files.supplies}
        />

        <FileUpload
          label="Температура (temperature.csv)"
          required
          onUpload={(file) => handleUpload('temperature', file)}
          uploadedFile={files.temperature}
        />

        <div className="file-upload">
          <label className="file-upload-label">
            Погода (weather_data_*.csv)
            <span className="required">*</span>
          </label>
          <FileUpload
            label=""
            required={false}
            onUpload={(file) => handleUpload('weather', file)}
            uploadedFile={null}
            multiple={true}
          />
          {files.weather.length > 0 && (
            <div className="uploaded-files-list">
              <p className="uploaded-files-title">Загружено файлов погоды: {files.weather.length}</p>
              {files.weather.map((file, index) => (
                <div key={index} className="uploaded-file-item">
                  <span className="file-icon">📄</span>
                  <span className="file-name">{file.name}</span>
                  <button
                    className="btn-remove"
                    onClick={() => handleRemoveWeatherFile(index)}
                    title="Удалить файл"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <FileUpload
          label="Возгорания (fires.csv) - опционально"
          onUpload={(file) => handleUpload('fires', file)}
          uploadedFile={files.fires}
        />
      </div>

      <div className="action-section">
        <button
          className="btn btn-primary btn-large"
          onClick={handlePredict}
          disabled={!canPredict || predicting}
        >
          {predicting ? (
            <>
              <span className="spinner small"></span>
              Выполняется прогноз...
            </>
          ) : (
            '🔮 Выполнить прогноз'
          )}
        </button>

        {!canPredict && (
          <p className="help-text">
            Загрузите обязательные файлы для выполнения прогноза
          </p>
        )}

        {dateRange && (
          <div className="date-range-info">
            <h3>Информация о данных</h3>
            <p>Период данных: {new Date(dateRange.data_start_date).toLocaleDateString('ru-RU')} - {new Date(dateRange.data_end_date).toLocaleDateString('ru-RU')}</p>
            {dateRange.years && <p>Годы: {dateRange.years.join(', ')}</p>}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;