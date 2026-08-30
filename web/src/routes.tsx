// Centralized route definitions for the analyst dashboard.
export const ROUTES = {
  dashboard: '/',
  transaction: '/tx/:id',
  investigation: '/investigation/:id',
  feedback: '/feedback',
  fiOps: '/fi-ops',
  treasury: '/treasury',
  analyst: '/analyst',
  analystTransaction: '/analyst/tx/:id',
  analystCustomer: '/analyst/customer/:ccNum',
  analystPerformance: '/analyst/performance',
  analystModels: '/analyst/models',
} as const;
