import { Routes, Route } from 'react-router-dom';
import { TransactionDetail } from './pages/TransactionDetail';
import { Investigation } from './pages/Investigation';
import { Feedback } from './pages/Feedback';
import { BusinessTreasury } from './pages/BusinessTreasury';
import { BankLayout } from './components/BankLayout';
import { BankDashboard, TransactionsPage, AlertsPage, AnalyticsPage, CustomersPage, MerchantsPage, PoliciesPage, ModelsPage, ReportsPage, AuditPage, SettingsPage } from './pages/BankPages';

export function App() {
  return (
    <BankLayout>
      <Routes>
        <Route path="/" element={<BankDashboard />} />
        <Route path="/fi-ops" element={<BankDashboard />} />
        <Route path="/bank/transactions" element={<TransactionsPage />} />
        <Route path="/bank/alerts" element={<AlertsPage />} />
        <Route path="/bank/analytics" element={<AnalyticsPage />} />
        <Route path="/bank/customers" element={<CustomersPage />} />
        <Route path="/bank/merchants" element={<MerchantsPage />} />
        <Route path="/bank/policies" element={<PoliciesPage />} />
        <Route path="/bank/models" element={<ModelsPage />} />
        <Route path="/bank/reports" element={<ReportsPage />} />
        <Route path="/bank/audit" element={<AuditPage />} />
        <Route path="/bank/settings" element={<SettingsPage />} />
        <Route path="/tx/:id" element={<TransactionDetail />} />
        <Route path="/investigation/:id" element={<Investigation />} />
        <Route path="/feedback" element={<Feedback />} />
        <Route path="/treasury" element={<BusinessTreasury />} />
      </Routes>
    </BankLayout>
  );
}
