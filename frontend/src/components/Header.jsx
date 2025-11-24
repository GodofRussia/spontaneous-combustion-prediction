import {Link, useLocation} from 'react-router-dom';

const Header = () => {
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <header className="header">
      <div className="header-content">
        <h1 className="header-title">🔥 Прогнозирование возгораний угля</h1>
        <nav className="header-nav">
          <Link
            to="/"
            className={`nav-link ${isActive('/') ? 'active' : ''}`}
          >
            Загрузка данных
          </Link>
          <Link
            to="/calendar"
            className={`nav-link ${isActive('/calendar') ? 'active' : ''}`}
          >
            Календарь
          </Link>
          <Link
            to="/metrics"
            className={`nav-link ${isActive('/metrics') ? 'active' : ''}`}
          >
            Метрики
          </Link>
        </nav>
      </div>
    </header>
  );
};

export default Header;