export type CustomerTransactionStatus = 'Completed' | 'Pending' | 'Verification Required' | 'Blocked' | 'Denied' | 'Failed';

export interface CustomerTransaction {
  id: string;
  merchant: string;
  amount: number;
  currency: string;
  date: string;
  status: CustomerTransactionStatus;
  type: 'Purchase' | 'Transfer' | 'Withdrawal';
  channel: 'Online' | 'Card';
  location: string;
  securityNote?: string;
}

export const customerAccounts = [
  { name: 'Checking Account', last4: '4521', balance: 8430.20, type: 'Everyday spending', status: 'Active' },
  { name: 'Savings Account', last4: '9124', balance: 4020.60, type: 'Emergency savings', status: 'Active' },
];

export const customerTransactions: CustomerTransaction[] = [
  { id: 'TX-89231', merchant: 'Amazon', amount: 850, currency: 'USD', date: 'Today, 9:42 AM', status: 'Verification Required', type: 'Purchase', channel: 'Online', location: 'Seattle, US', securityNote: 'This purchase is larger than your usual activity.' },
  { id: 'TX-89224', merchant: 'Amazon', amount: -45.20, currency: 'USD', date: 'Today, 8:10 AM', status: 'Completed', type: 'Purchase', channel: 'Online', location: 'New York, US' },
  { id: 'TX-89223', merchant: 'Starbucks', amount: -7.50, currency: 'USD', date: 'Today, 7:45 AM', status: 'Completed', type: 'Purchase', channel: 'Card', location: 'New York, US' },
  { id: 'TX-89221', merchant: 'Apple', amount: -129.99, currency: 'USD', date: 'Yesterday, 4:30 PM', status: 'Completed', type: 'Purchase', channel: 'Online', location: 'New York, US' },
  { id: 'TX-89218', merchant: 'Metro Transit', amount: -32, currency: 'USD', date: 'Yesterday, 8:18 AM', status: 'Completed', type: 'Purchase', channel: 'Card', location: 'New York, US' },
  { id: 'TX-89210', merchant: 'Brightline Payroll', amount: 3250, currency: 'USD', date: 'Aug 22, 2:00 PM', status: 'Completed', type: 'Transfer', channel: 'Online', location: 'New York, US' },
  { id: 'TX-89202', merchant: 'Northstar Travel', amount: -2340, currency: 'USD', date: 'Aug 20, 11:24 PM', status: 'Blocked', type: 'Purchase', channel: 'Online', location: 'Bucharest, RO', securityNote: 'Blocked because it came from an unfamiliar location.' },
];

export const customerDevices = [
  { name: 'iPhone 15 Pro', os: 'iOS 18.5', lastActive: 'Today', firstSeen: 'Jan 12, 2025', trusted: true },
  { name: 'MacBook Pro', os: 'macOS Sequoia', lastActive: 'Yesterday', firstSeen: 'Mar 04, 2025', trusted: true },
  { name: 'Windows PC', os: 'Windows 11', lastActive: 'Aug 20', firstSeen: 'Aug 20, 2026', trusted: false },
];

export const customerNotifications = [
  { title: 'Transaction verification required', description: 'Your $850.00 Amazon transaction needs verification.', time: '12 minutes ago', severity: 'attention', unread: true },
  { title: 'Transaction approved', description: 'Your $45.20 transaction at Amazon was approved.', time: '2 hours ago', severity: 'safe', unread: true },
  { title: 'New device detected', description: 'A new Windows PC was used to access your account.', time: 'Aug 20', severity: 'attention', unread: false },
];

export const activityEvents = [
  ['Today, 9:42 AM', 'Transaction verification requested', 'Amazon - $850.00', 'attention'],
  ['Today, 8:10 AM', 'Transaction approved', 'Amazon - $45.20', 'safe'],
  ['Yesterday, 4:30 PM', 'Successful login', 'iPhone 15 Pro', 'safe'],
  ['Aug 20, 11:26 PM', 'New device detected', 'Windows PC', 'attention'],
  ['Aug 18, 3:20 PM', 'Password changed', 'Security settings', 'safe'],
];
