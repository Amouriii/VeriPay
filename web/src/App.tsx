import { Navigate, Routes, Route } from 'react-router-dom';

import { BankLayout } from './components/BankLayout';
import { CustomerLayout } from './components/CustomerLayout';

import {
  CustomerDashboard,
  CustomerAccountsPage,
  CustomerTransactionsPage,
  CustomerTransactionDetail,
  SecurityPage,
  DevicesPage,
  ActivityPage,
  NotificationsPage,
  ReportFraudPage,
  ProfilePage,
  HelpPage,
  NormalBehaviorPage,
} from './pages/CustomerPages';

import {
  TransactionsPage,
  AlertsPage,
  AnalyticsPage,
  MerchantsPage,
  PoliciesPage,
  ModelsPage,
  ReportsPage,
  AuditPage,
  BankNotificationsPage,
  BankDashboard,
} from './pages/BankPages';

import { BankSettings } from './pages/BankSettings';
import { BankLogin } from './pages/BankLogin';
import { CustomerLogin } from './pages/CustomerLogin';
import { BankCustomerProfile } from './pages/BankCustomerProfile';
import { BankCustomers } from './pages/BankCustomers';

import { TransactionDetail } from './pages/TransactionDetail';
import { Investigation } from './pages/Investigation';
import { Feedback } from './pages/Feedback';
import { BusinessTreasury } from './pages/BusinessTreasury';
import { AnalystLayout } from './components/AnalystLayout';
import { AlertQueue } from './pages/analyst/AlertQueue';
import { TxDetail } from './pages/analyst/TxDetail';
import { CustomerProfile } from './pages/analyst/CustomerProfile';
import { SystemPerformance } from './pages/analyst/SystemPerformance';
import { ModelInfo } from './pages/analyst/ModelInfo';
import { ExecutiveDemo } from './pages/ExecutiveDemo';

/* -------------------------------------------------------------------------- */
/* Customer routes                                                            */
/* -------------------------------------------------------------------------- */

function CustomerApp() {
  return (
    <CustomerLayout>
      <Routes>
        <Route index element={<CustomerDashboard />} />

        <Route path="accounts" element={<CustomerAccountsPage />} />

        <Route
          path="transactions"
          element={<CustomerTransactionsPage />}
        />

        <Route
          path="transactions/:id"
          element={<CustomerTransactionDetail />}
        />

        <Route
          path="normal-activity"
          element={<NormalBehaviorPage />}
        />

        <Route path="security" element={<SecurityPage />} />

        <Route
          path="security/devices"
          element={<DevicesPage />}
        />

        <Route
          path="security/activity"
          element={<ActivityPage />}
        />

        <Route
          path="notifications"
          element={<NotificationsPage />}
        />

        <Route
          path="report-fraud"
          element={<ReportFraudPage />}
        />

        <Route path="profile" element={<ProfilePage />} />

        <Route path="help" element={<HelpPage />} />

        <Route path="settings" element={<ProfilePage />} />
      </Routes>
    </CustomerLayout>
  );
}

/* -------------------------------------------------------------------------- */
/* Main application                                                           */
/* -------------------------------------------------------------------------- */

function AnalystApp() {
  return (
    <AnalystLayout>
      <Routes>
        <Route index element={<AlertQueue />} />
        <Route path="tx/:id" element={<TxDetail />} />
        <Route path="customer/:ccNum" element={<CustomerProfile />} />
        <Route path="performance" element={<SystemPerformance />} />
        <Route path="models" element={<ModelInfo />} />
      </Routes>
    </AnalystLayout>
  );
}

export function App() {
  return (
    <Routes>
      <Route path="/executive-demo" element={<ExecutiveDemo />} />

      <Route
        path="/customer/login"
        element={<CustomerLogin />}
      />

      <Route
        path="/customer/*"
        element={<CustomerApp />}
      />

      <Route
        path="/login"
        element={<BankLogin />}
      />

      <Route
        path="/analyst/*"
        element={<AnalystApp />}
      />

      <Route
        path="/"
        element={<Navigate to="/login" replace />}
      />

      <Route
        path="/fi-ops"
        element={
          <BankLayout>
            <BankDashboard />
          </BankLayout>
        }
      />

      <Route
        path="/bank/transactions"
        element={
          <BankLayout>
            <TransactionsPage />
          </BankLayout>
        }
      />

      <Route
        path="/bank/alerts"
        element={
          <BankLayout>
            <AlertsPage />
          </BankLayout>
        }
      />

      <Route
        path="/bank/analytics"
        element={
          <BankLayout>
            <AnalyticsPage />
          </BankLayout>
        }
      />

      <Route
        path="/bank/customers"
        element={
          <BankLayout>
            <BankCustomers />
          </BankLayout>
        }
      />

      <Route
        path="/bank/customers/:id"
        element={
          <BankLayout>
            <BankCustomerProfile />
          </BankLayout>
        }
      />

      <Route
        path="/bank/merchants"
        element={
          <BankLayout>
            <MerchantsPage />
          </BankLayout>
        }
      />

      <Route
        path="/bank/policies"
        element={
          <BankLayout>
            <PoliciesPage />
          </BankLayout>
        }
      />

      <Route
        path="/bank/models"
        element={
          <BankLayout>
            <ModelsPage />
          </BankLayout>
        }
      />

      <Route
        path="/bank/reports"
        element={
          <BankLayout>
            <ReportsPage />
          </BankLayout>
        }
      />

      <Route
        path="/bank/audit"
        element={
          <BankLayout>
            <AuditPage />
          </BankLayout>
        }
      />

      <Route
        path="/bank/settings"
        element={
          <BankLayout>
            <BankSettings />
          </BankLayout>
        }
      />

      <Route
        path="/bank/notifications"
        element={
          <BankLayout>
            <BankNotificationsPage />
          </BankLayout>
        }
      />

      <Route
        path="/tx/:id"
        element={
          <BankLayout>
            <TransactionDetail />
          </BankLayout>
        }
      />

      <Route
        path="/investigation/:id"
        element={
          <BankLayout>
            <Investigation />
          </BankLayout>
        }
      />

      <Route
        path="/feedback"
        element={
          <BankLayout>
            <Feedback />
          </BankLayout>
        }
      />

      <Route
        path="/treasury"
        element={
          <BankLayout>
            <BusinessTreasury />
          </BankLayout>
        }
      />

      <Route
        path="*"
        element={<Navigate to="/login" replace />}
      />
    </Routes>
  );
}
