import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import DashboardPage from './pages/DashboardPage';
import MarketIntelPage from './pages/MarketIntelPage';
import EmailPage from './pages/EmailPage';
import ActionsPage from './pages/ActionsPage';
import SettingsPage from './pages/SettingsPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="market" element={<MarketIntelPage />} />
          <Route path="email" element={<EmailPage />} />
          <Route path="actions" element={<ActionsPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
