export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type Decision = 'ALLOW' | 'VERIFY' | 'BLOCK';
export type TransactionStatus = 'PENDING' | 'APPROVED' | 'BLOCKED' | 'VERIFICATION_REQUIRED' | 'DENIED' | 'FAILED';

export interface BankTransaction {
  id: string;
  customer: string;
  merchant: string;
  amount: number;
  currency: string;
  score: number;
  level: RiskLevel;
  decision: Decision;
  verification: 'NOT_REQUIRED' | 'PENDING' | 'PASSED' | 'FAILED';
  status: TransactionStatus;
  time: string;
  channel: 'CARD_PRESENT' | 'CARD_NOT_PRESENT';
  type: 'PURCHASE' | 'WITHDRAWAL' | 'TRANSFER';
  location: string;
  reason: string;
}


export const bankTransactions: BankTransaction[] = [
  { id: 'TX-89231', customer: 'Customer #18492', merchant: 'Amazon', amount: 850, currency: 'USD', score: 89, level: 'HIGH', decision: 'VERIFY', verification: 'PENDING', status: 'VERIFICATION_REQUIRED', time: '09:42', channel: 'CARD_NOT_PRESENT', type: 'PURCHASE', location: 'Seattle, US', reason: 'New device' },
  { id: 'TX-89230', customer: 'Customer #77104', merchant: 'Northstar Travel', amount: 2340, currency: 'USD', score: 96, level: 'CRITICAL', decision: 'BLOCK', verification: 'FAILED', status: 'BLOCKED', time: '09:37', channel: 'CARD_NOT_PRESENT', type: 'PURCHASE', location: 'Bucharest, RO', reason: 'Unusual location' },
  { id: 'TX-89229', customer: 'Customer #40211', merchant: 'Mercury Market', amount: 74.5, currency: 'USD', score: 18, level: 'LOW', decision: 'ALLOW', verification: 'NOT_REQUIRED', status: 'APPROVED', time: '09:31', channel: 'CARD_PRESENT', type: 'PURCHASE', location: 'Austin, US', reason: 'Normal behavior' },
  { id: 'TX-89228', customer: 'Customer #99518', merchant: 'CloudNine Software', amount: 1299, currency: 'USD', score: 78, level: 'MEDIUM', decision: 'VERIFY', verification: 'PASSED', status: 'APPROVED', time: '09:19', channel: 'CARD_NOT_PRESENT', type: 'PURCHASE', location: 'Boston, US', reason: 'Unusual amount' },
  { id: 'TX-89227', customer: 'Customer #23017', merchant: 'Metro Fuel', amount: 62, currency: 'USD', score: 8, level: 'LOW', decision: 'ALLOW', verification: 'NOT_REQUIRED', status: 'APPROVED', time: '09:10', channel: 'CARD_PRESENT', type: 'PURCHASE', location: 'Chicago, US', reason: 'Normal behavior' },
  { id: 'TX-89226', customer: 'Customer #65420', merchant: 'Atlas Electronics', amount: 4120, currency: 'USD', score: 84, level: 'HIGH', decision: 'VERIFY', verification: 'PENDING', status: 'PENDING', time: '08:56', channel: 'CARD_NOT_PRESENT', type: 'PURCHASE', location: 'Denver, US', reason: 'New location' },
  { id: 'TX-89225', customer: 'Customer #50911', merchant: 'Harbor Pharmacy', amount: 188.2, currency: 'USD', score: 31, level: 'MEDIUM', decision: 'VERIFY', verification: 'PASSED', status: 'APPROVED', time: '08:44', channel: 'CARD_PRESENT', type: 'PURCHASE', location: 'Miami, US', reason: 'Unusual transaction time' },
];

export const notifications = [
  { text: 'Critical fraud spike detected.', detail: '12 minutes ago', severity: 'CRITICAL', unread: true },
  { text: '25 high-risk transactions require investigation.', detail: '34 minutes ago', severity: 'HIGH', unread: true },
  { text: 'Model v1.3 is ready for review.', detail: '2 hours ago', severity: 'INFO', unread: false },
  { text: 'Fraud policy was changed by Risk Manager.', detail: 'Yesterday', severity: 'MEDIUM', unread: false },
];

export const customers = [
  {
    id: 'CUS-18492',
    name: 'Customer #18492',
    email: 'c•••••@example.com',
    cardLast4: '4521',
    transactions: 148,
    volume: '$18,420',
    alerts: 3,
    risk: 'HIGH',
    account: 'ACTIVE',

    behavior: {
      currency: 'USD',
      averageAmount: '$124.50',
      amountRange: '$35 - $450',
      frequency: '3 - 5 transactions/day',
      velocity: '1 - 2 transactions/hour',
      normalTime: '12 PM - 8 PM',
      location: 'New York · 82%',
      device: 'iPhone 15 Pro · 72%',
      category: 'Online shopping · 34%',
    },
  },

  {
    id: 'CUS-77104',
    name: 'Customer #77104',
    email: 'j•••••@example.com',
    cardLast4: '0837',
    transactions: 62,
    volume: '$7,890',
    alerts: 1,
    risk: 'MEDIUM',
    account: 'ACTIVE',

    behavior: {
      currency: 'USD',
      averageAmount: '$186.30',
      amountRange: '$50 - $900',
      frequency: '1 - 3 transactions/day',
      velocity: '1 transaction/hour',
      normalTime: '8 AM - 6 PM',
      location: 'Chicago · 76%',
      device: 'iPhone 14 · 68%',
      category: 'Travel · 41%',
    },
  },

  {
    id: 'CUS-40211',
    name: 'Customer #40211',
    email: 'm•••••@example.com',
    cardLast4: '6310',
    transactions: 231,
    volume: '$32,104',
    alerts: 0,
    risk: 'LOW',
    account: 'ACTIVE',

    behavior: {
      currency: 'USD',
      averageAmount: '$74.20',
      amountRange: '$15 - $180',
      frequency: '5 - 8 transactions/day',
      velocity: '2 - 3 transactions/hour',
      normalTime: '10 AM - 9 PM',
      location: 'Austin · 91%',
      device: 'iPhone 15 · 81%',
      category: 'Groceries · 32%',
    },
  },

  {
    id: 'CUS-99518',
    name: 'Customer #99518',
    email: 'a•••••@example.com',
    cardLast4: '1198',
    transactions: 89,
    volume: '$14,201',
    alerts: 2,
    risk: 'MEDIUM',
    account: 'REVIEW',

    behavior: {
      currency: 'USD',
      averageAmount: '$159.60',
      amountRange: '$30 - $500',
      frequency: '2 - 4 transactions/day',
      velocity: '1 - 2 transactions/hour',
      normalTime: '9 AM - 7 PM',
      location: 'Boston · 79%',
      device: 'MacBook Pro · 64%',
      category: 'Software & subscriptions · 38%',
    },
  },
    {
    id: 'CUS-23017',
    name: 'Customer #23017',
    email: 'r•••••@example.com',
    cardLast4: '7742',
    transactions: 174,
    volume: '$11,680',
    alerts: 0,
    risk: 'LOW',
    account: 'ACTIVE',

    behavior: {
      currency: 'USD',
      averageAmount: '$68.40',
      amountRange: '$20 - $160',
      frequency: '4 - 6 transactions/day',
      velocity: '1 - 2 transactions/hour',
      normalTime: '7 AM - 8 PM',
      location: 'Chicago · 88%',
      device: 'iPhone 14 · 75%',
      category: 'Fuel & transportation · 29%',
    },
  },

  {
    id: 'CUS-65420',
    name: 'Customer #65420',
    email: 'd•••••@example.com',
    cardLast4: '2904',
    transactions: 96,
    volume: '$21,540',
    alerts: 2,
    risk: 'HIGH',
    account: 'REVIEW',

    behavior: {
      currency: 'USD',
      averageAmount: '$215.80',
      amountRange: '$40 - $700',
      frequency: '2 - 4 transactions/day',
      velocity: '1 transaction/hour',
      normalTime: '9 AM - 6 PM',
      location: 'Denver · 83%',
      device: 'MacBook Air · 61%',
      category: 'Electronics · 27%',
    },
  },

  {
    id: 'CUS-50911',
    name: 'Customer #50911',
    email: 's•••••@example.com',
    cardLast4: '5168',
    transactions: 113,
    volume: '$16,870',
    alerts: 1,
    risk: 'MEDIUM',
    account: 'ACTIVE',

    behavior: {
      currency: 'USD',
      averageAmount: '$92.70',
      amountRange: '$25 - $240',
      frequency: '2 - 5 transactions/day',
      velocity: '1 - 2 transactions/hour',
      normalTime: '8 AM - 7 PM',
      location: 'Miami · 86%',
      device: 'iPhone 13 · 70%',
      category: 'Health & pharmacy · 31%',
    },
  },
];

export const merchants = [
  { id: 'MER-1002', name: 'Amazon', category: 'E-commerce', volume: '$1.84M', transactions: 8210, fraudRate: '1.8%', score: 42, blockRate: '0.6%', status: 'MONITORED' },
  { id: 'MER-1044', name: 'Northstar Travel', category: 'Travel', volume: '$640K', transactions: 1042, fraudRate: '4.7%', score: 68, blockRate: '2.4%', status: 'REVIEW' },
  { id: 'MER-1168', name: 'Mercury Market', category: 'Retail', volume: '$920K', transactions: 18204, fraudRate: '0.4%', score: 19, blockRate: '0.1%', status: 'HEALTHY' },
];

export const auditLogs = [
  ['09:44', 'A. Morgan', 'Risk Manager', 'Viewed transaction', 'Transaction', 'TX-89231', 'SUCCESS'],
  ['09:12', 'S. Patel', 'Administrator', 'Changed fraud threshold', 'Fraud Policy', 'POL-001', 'SUCCESS'],
  ['08:51', 'A. Morgan', 'Risk Manager', 'Assigned investigation', 'Alert', 'ALT-4412', 'SUCCESS'],
  ['Yesterday', 'J. Chen', 'Fraud Manager', 'Resolved alert', 'Alert', 'ALT-4401', 'SUCCESS'],
];
