import { Routes, Route } from 'react-router-dom';
import { TransactionDetail } from './pages/TransactionDetail';
import { Investigation } from './pages/Investigation';
import { Feedback } from './pages/Feedback';
import { BusinessTreasury } from './pages/BusinessTreasury';
import { BankLayout } from './components/BankLayout.tsx';
import { BankDashboard, TransactionsPage, AlertsPage, AnalyticsPage, CustomersPage, MerchantsPage, PoliciesPage, ModelsPage, ReportsPage, AuditPage, SettingsPage, BankNotificationsPage } from './pages/BankPages';
import { CustomerLayout } from './components/CustomerLayout';
import { CustomerDashboard, CustomerAccountsPage, CustomerTransactionsPage, CustomerTransactionDetail, SecurityPage, DevicesPage, ActivityPage, NotificationsPage, ReportFraudPage, ProfilePage, HelpPage } from './pages/CustomerPages';

function CustomerApp() {
  return (
    <CustomerLayout>
      <Routes>
        <Route index element={<CustomerDashboard />} />
        <Route path="accounts" element={<CustomerAccountsPage />} />
        <Route path="transactions" element={<CustomerTransactionsPage />} />
        <Route path="transactions/:id" element={<CustomerTransactionDetail />} />
        <Route path="security" element={<SecurityPage />} />
        <Route path="security/devices" element={<DevicesPage />} />
        <Route path="security/activity" element={<ActivityPage />} />
        <Route path="notifications" element={<NotificationsPage />} />
        <Route path="report-fraud" element={<ReportFraudPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="help" element={<HelpPage />} />
        <Route path="settings" element={<ProfilePage />} />
      </Routes>
    </CustomerLayout>
  );
}

export function App() {
  return (
    <Routes>
      <Route path="/customer/*" element={<CustomerApp />} />
      <Route path="*" element={<BankLayout><Routes>
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
        <Route path="/bank/notifications" element={<BankNotificationsPage />} />
        <Route path="/tx/:id" element={<TransactionDetail />} />
        <Route path="/investigation/:id" element={<Investigation />} />
        <Route path="/feedback" element={<Feedback />} />
        <Route path="/treasury" element={<BusinessTreasury />} />
      </Routes></BankLayout>} />
    </Routes>
  );
}
