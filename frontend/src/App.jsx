import {BrowserRouter, Routes, Route, Navigate} from 'react-router-dom';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import PredictionsCalendar from './pages/PredictionsCalendar';
import ModelMetrics from './pages/ModelMetrics';
import DatePileMatrix from './pages/DatePileMatrix';

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Header />
        <div className="app-container">
          <Sidebar />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/calendar" element={<PredictionsCalendar />} />
              <Route path="/metrics" element={<ModelMetrics />} />
              <Route path="/matrix" element={<DatePileMatrix />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;