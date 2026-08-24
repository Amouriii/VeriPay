import { Routes, Route } from 'react-router-dom';
import { Dashboard } from './pages/Dashboard';
import { TransactionDetail } from './pages/TransactionDetail';
import { Investigation } from './pages/Investigation';
import { Feedback } from './pages/Feedback';
import { FiOpsConsole } from './pages/FiOpsConsole';
import { BusinessTreasury } from './pages/BusinessTreasury';

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/tx/:id" element={<TransactionDetail />} />
      <Route path="/investigation/:id" element={<Investigation />} />
      <Route path="/feedback" element={<Feedback />} />
      <Route path="/fi-ops" element={<FiOpsConsole />} />
      <Route path="/treasury" element={<BusinessTreasury />} />
    </Routes>
  );
}
