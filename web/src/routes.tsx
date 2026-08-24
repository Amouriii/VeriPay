// Centralized route definitions for the analyst dashboard.
export const ROUTES = {
  dashboard: '/',
  transaction: '/tx/:id',
  investigation: '/investigation/:id',
  feedback: '/feedback',
  fiOps: '/fi-ops',
  treasury: '/treasury',
} as const;
