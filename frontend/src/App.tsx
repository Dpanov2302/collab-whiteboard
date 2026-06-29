import { Link, Navigate, Route, Routes } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import LoginPage from './pages/LoginPage';
import BoardPage from './pages/BoardPage';
import { getToken, setToken } from './api/client';

function App() {
  const token = getToken();
  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/" className="brand">Collab Whiteboard</Link>
        <nav>
          {token ? <button onClick={() => { setToken(null); location.href = '/login'; }}>Выйти</button> : <Link to="/login">Войти</Link>}
        </nav>
      </header>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={token ? <DashboardPage /> : <Navigate to="/login" replace />} />
        <Route path="/boards/:boardId" element={token ? <BoardPage /> : <Navigate to="/login" replace />} />
      </Routes>
    </div>
  );
}

export default App;
