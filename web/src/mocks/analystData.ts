// Seeded fixtures for the fraud-analyst console demo. Each alert is a stored,
// non-PASS `POST /score` result. Case reports mirror the asset IDs the backend
// would return from `POST /explain` for the same transaction.

import type {
  AlertItem,
  CustomerProfileResponse,
  Decision,
  ExplainResponse,
  FeedbackHistoryEntry,
  FeedbackStats,
  FeatureRow,
  Community,
  CustomerNetwork,
  NetworkEgo,
  NetworkFeatures,
  RiskLevel,
  ScoreResponse,
} from '../types/analyst';

const CUSTOMER_NAMES: Record<number, string> = {
  4716561796955522: 'Amira Farouk',
  4012888888881881: 'Daniel Okoye',
  5105105105105100: 'Lina Haddad',
  5555555555554444: 'Mateo Rios',
  4222222222222: 'Fatima Noor',
};

const currencyOf = (ccNum: number) => (ccNum === 4716561796955522 ? 'EGP' : 'USD');

function feature(name: string, value: string, customerBaseline: string, unit: string): FeatureRow {
  return { name, value, customer_baseline: customerBaseline, unit };
}

function makeRecentTransactions(seed: number, base: number): ScoreResponse['recent_transactions'] {
  const merchants = ['Cafe Napoli', 'Metro Mart', 'FuelStop', 'BookHaven', 'Terra Market', 'Grand Hotel', 'PharmaPlus', 'TechZone', 'Airways', 'Zara Outlet'];
  const categories = ['dining', 'grocery', 'fuel', 'entertainment', 'shopping'];
  const locations = ['Cairo', 'Giza', 'Alexandria', 'Mansoura', 'Tanta', 'Luxor'];
  const out: ScoreResponse['recent_transactions'] = [];
  const now = Date.UTC(2026, 8, 15, 14, 30, 0);
  let amount = Math.round((base * 0.6 + seed) * 100) / 100;
  for (let i = 0; i < 20; i += 1) {
    // Escalating sequence: the last few entries spike sharply.
    const escalator =
      i < 16 ? 1 + (i % 3) * 0.7 + (i % 2) * 0.4 : 4 + (i - 16) * 5;
    amount = Math.round(amount * escalator * 100) / 100;
    const ts = new Date(now - (20 - i) * 60 * 60 * 1000);
    out.push({
      time: ts.toISOString(),
      amount,
      merchant: merchants[(i * 3 + seed) % merchants.length],
      category: categories[i % categories.length],
      location: locations[(i + seed) % locations.length],
    });
  }
  return out;
}

/** Network (graph) context fixtures (PLAN §12). Each demo transaction carries a
 * graph payload so the new "Network" tab is navigable without a running
 * backend. tx_9001 is the marquee shared-merchant mule/ring scenario. */
function networkFor(
  txId: string,
  ccNum: number,
  opts: {
    risk: number;
    available: boolean;
    findings: string[];
    features: NetworkFeatures;
    ego: NetworkEgo;
    community?: Community;
  },
) {
  return {
    network_risk_score: opts.risk,
    network_available: opts.available,
    network_findings: opts.findings,
    network_features: opts.features,
    network_ego: opts.ego,
    network_community: opts.community,
    _tx: txId,
    _cc: ccNum,
  };
}

const NETWORK_CARD_TEST = networkFor('tx_9001', 4716561796955522, {
  risk: 0.82,
  available: true,
  findings: [
    'Shares merchant(s) with 2 confirmed-fraud account(s) (flagged exposure 100%).',
    'Connected to 2 other customer(s) via 1 shared merchant(s).',
    'Community of 4 account(s) with a 50% confirmed-fraud ratio.',
  ],
  features: {
    merchant_degree: 1,
    merchant_fan_in: 3,
    shared_counterparty_count: 2,
    co_occurrence_count: 1,
    flagged_neighbor_count: 2,
    flagged_exposure: 1.0,
    cluster_size: 4,
    cluster_flagged_ratio: 0.5,
  },
  ego: {
    nodes: [
      { id: 'c:4716561796955522', kind: 'customer', label: '4716561796955522', status: 'self' },
      { id: 'm:fraud_Kerluke', kind: 'merchant', label: 'fraud_Kerluke', status: 'review' },
      { id: 'c:4012888888881881', kind: 'customer', label: '4012888888881881', status: 'flagged' },
      { id: 'c:5555555555554444', kind: 'customer', label: '5555555555554444', status: 'flagged' },
    ],
    edges: [
      { from: 'c:4716561796955522', to: 'm:fraud_Kerluke', weight: 560 },
      { from: 'c:4012888888881881', to: 'm:fraud_Kerluke', weight: 1200 },
      { from: 'c:5555555555554444', to: 'm:fraud_Kerluke', weight: 1405 },
    ],
  },
  community: {
    graph: {
      nodes: [
        { id: 'c:4716561796955522', kind: 'customer', label: '4716561796955522', status: 'self' },
        { id: 'c:4012888888881881', kind: 'customer', label: '4012888888881881', status: 'flagged' },
        { id: 'c:5555555555554444', kind: 'customer', label: '5555555555554444', status: 'flagged' },
        { id: 'c:5105105105105100', kind: 'customer', label: '5105105105105100', status: 'normal' },
        { id: 'm:fraud_Kerluke', kind: 'merchant', label: 'fraud_Kerluke', status: 'review' },
      ],
      edges: [
        { from: 'c:4716561796955522', to: 'm:fraud_Kerluke', weight: 560 },
        { from: 'c:4012888888881881', to: 'm:fraud_Kerluke', weight: 1200 },
        { from: 'c:5555555555554444', to: 'm:fraud_Kerluke', weight: 1405 },
        { from: 'c:5105105105105100', to: 'm:fraud_Kerluke', weight: 2300 },
      ],
    },
    stats: {
      cluster_size: 4,
      flagged_count: 2,
      flagged_ratio: 0.5,
      distinct_shared_merchants: 1,
      total_volume: 5465,
      dominant_pattern: 'fraud_ring',
    },
    members: [
      { cc_num: 4716561796955522, status: 'self' },
      { cc_num: 4012888888881881, status: 'flagged' },
      { cc_num: 5555555555554444, status: 'flagged' },
      { cc_num: 5105105105105100, status: 'normal' },
    ],
  },
});

const NETWORK_IMPOSSIBLE = networkFor('tx_9002', 4012888888881881, {
  risk: 0.41,
  available: true,
  findings: [
    'Connected to 1 other customer(s) via 1 shared merchant(s).',
    '1 temporal co-occurrence(s) — peer transaction(s) at the same merchant within 60s.',
  ],
  features: {
    merchant_degree: 1,
    merchant_fan_in: 2,
    shared_counterparty_count: 1,
    co_occurrence_count: 1,
    flagged_neighbor_count: 0,
    flagged_exposure: 0.0,
    cluster_size: 2,
    cluster_flagged_ratio: 0.0,
  },
  ego: {
    nodes: [
      { id: 'c:4012888888881881', kind: 'customer', label: '4012888888881881', status: 'self' },
      { id: 'm:GlobalAirlines', kind: 'merchant', label: 'GlobalAirlines', status: 'normal' },
      { id: 'c:5105105105105100', kind: 'customer', label: '5105105105105100', status: 'normal' },
    ],
    edges: [
      { from: 'c:4012888888881881', to: 'm:GlobalAirlines', weight: 1240 },
      { from: 'c:5105105105105100', to: 'm:GlobalAirlines', weight: 2300 },
    ],
  },
});

const NETWORK_AMOUNT_SPIKE = networkFor('tx_9003', 5105105105105100, {
  risk: 0.18,
  available: true,
  findings: ['Connected to 1 other customer(s) via 1 shared merchant(s).'],
  features: {
    merchant_degree: 1,
    merchant_fan_in: 2,
    shared_counterparty_count: 1,
    co_occurrence_count: 0,
    flagged_neighbor_count: 0,
    flagged_exposure: 0.0,
    cluster_size: 2,
    cluster_flagged_ratio: 0.0,
  },
  ego: {
    nodes: [
      { id: 'c:5105105105105100', kind: 'customer', label: '5105105105105100', status: 'self' },
      { id: 'm:Grand Hotel', kind: 'merchant', label: 'Grand Hotel', status: 'normal' },
    ],
    edges: [{ from: 'c:5105105105105100', to: 'm:Grand Hotel', weight: 2300 }],
  },
});

const NETWORK_FAILED_AUTH = networkFor('tx_9004', 5555555555554444, {
  risk: 0.62,
  available: true,
  findings: [
    'Shares merchant(s) with 1 confirmed-fraud account(s) (flagged exposure 100%).',
    'Connected to 2 other customer(s) via 1 shared merchant(s).',
  ],
  features: {
    merchant_degree: 1,
    merchant_fan_in: 3,
    shared_counterparty_count: 2,
    co_occurrence_count: 0,
    flagged_neighbor_count: 1,
    flagged_exposure: 0.5,
    cluster_size: 3,
    cluster_flagged_ratio: 0.33,
  },
  ego: {
    nodes: [
      { id: 'c:5555555555554444', kind: 'customer', label: '5555555555554444', status: 'self' },
      { id: 'm:WireTransferPlus', kind: 'merchant', label: 'WireTransferPlus', status: 'review' },
      { id: 'c:4716561796955522', kind: 'customer', label: '4716561796955522', status: 'flagged' },
    ],
    edges: [
      { from: 'c:5555555555554444', to: 'm:WireTransferPlus', weight: 1405 },
      { from: 'c:4716561796955522', to: 'm:WireTransferPlus', weight: 560 },
    ],
  },
});

const NETWORK_ODD_HOURS = networkFor('tx_9005', 4222222222222, {
  risk: 0.0,
  available: false,
  findings: [],
  features: {
    merchant_degree: 1,
    merchant_fan_in: 1,
    shared_counterparty_count: 0,
    co_occurrence_count: 0,
    flagged_neighbor_count: 0,
    flagged_exposure: 0.0,
    cluster_size: 1,
    cluster_flagged_ratio: 0.0,
  },
  ego: {
    nodes: [
      { id: 'c:4222222222222', kind: 'customer', label: '4222222222222', status: 'self' },
      { id: 'm:MidnightMart', kind: 'merchant', label: 'MidnightMart', status: 'normal' },
    ],
    edges: [{ from: 'c:4222222222222', to: 'm:MidnightMart', weight: 205 }],
  },
});

/** Card-testing example from the guide: velocity + large amount at new merchant. */
const CARD_TEST: ScoreResponse = {
  transaction_id: 'tx_9001',
  cc_num: 4716561796955522,
  decision: 'BLOCK',
  risk_level: 'HIGH',
  fraud_probability: 0.968,
  anomaly_score: 0.94,
  verification_action: 'Payment held. Awaiting biometric verification.',
  features: [
    feature('txn_count_1h', '6', '1.2', 'txn/hour'),
    feature('amt_over_median_90d', '12.4x', '1.0x (by definition)', 'multiplier'),
    feature('amt', '560', '45.23', currencyOf(4716561796955522)),
    feature('dist_from_home_km', '6', '0', 'km'),
    feature('implied_velocity_kmh', '12', 'N/A', 'km/h'),
    feature('is_new_merchant', 'Yes', 'N/A', ''),
    feature('is_known_category', 'No', 'Yes', ''),
    feature('txn_amt_24h_sum', '1,240', '128', currencyOf(4716561796955522)),
    feature('time_of_day', '02:47', '09:00 - 20:00', ''),
    feature('is_weekend', 'Yes', 'No', ''),
    feature('merchant_mcc_risk', '0.72', '0.3', 'score'),
    feature('is_failed_auth', 'Yes', 'No', ''),
    feature('fx_flag', 'No', 'No', ''),
    feature('txn_count_30d', '48', '29', 'txn'),
    feature('distinct_merchants_30d', '9', '12', 'merchants'),
    feature('rapid_fire_precursor', 'Yes', 'No', ''),
  ],
  anomaly_top_contributors: [
    { feature: 'Transaction velocity (1h)', contribution_pct: 31 },
    { feature: 'Amount vs 90-day median', contribution_pct: 27 },
    { feature: 'Implied travel speed', contribution_pct: 22 },
    { feature: 'Time of day', contribution_pct: 12 },
    { feature: 'New merchant', contribution_pct: 8 },
  ],
  xgboost_feature_contributions: [
    { feature: 'Amount (24h sum)', shap_value: 4.7 },
    { feature: 'Amount vs median', shap_value: 1.22 },
    { feature: 'Transaction velocity (1h)', shap_value: 0.98 },
    { feature: 'Failed auth attempts', shap_value: 0.64 },
    { feature: 'Known category', shap_value: -0.45 },
    { feature: 'Distinct merchants (30d)', shap_value: -0.2 },
  ],
  recent_transactions: makeRecentTransactions(1, 10),
  ...NETWORK_CARD_TEST,
} as ScoreResponse;

/** Impossible travel: physically implausible distance in the inter-arrival window. */
const IMPOSSIBLE_TRAVEL: ScoreResponse = {
  transaction_id: 'tx_9002',
  cc_num: 4012888888881881,
  decision: 'REVIEW_STEALTH',
  risk_level: 'MODERATE',
  fraud_probability: 0.62,
  anomaly_score: 0.58,
  verification_action: 'Push notification sent. Expires in 4:32.',
  features: [
    feature('implied_velocity_kmh', '2,400', 'N/A', 'km/h'),
    feature('dist_from_prev_txn_km', '1,200', '18', 'km'),
    feature('amt_over_median_90d', '3.1x', '1.0x', 'multiplier'),
    feature('txn_count_1h', '1', '1.2', 'txn/hour'),
    feature('is_new_merchant', 'No', 'N/A', ''),
    feature('dist_from_home_km', '780', '0', 'km'),
    feature('time_of_day', '21:04', '07:00 - 21:00', ''),
    feature('is_weekend', 'No', 'No', ''),
    feature('merchant_mcc_risk', '0.41', '0.3', 'score'),
    feature('is_failed_auth', 'No', 'No', ''),
    feature('fx_flag', 'Yes', 'No', ''),
    feature('txn_count_30d', '22', '31', 'txn'),
    feature('distinct_merchants_30d', '11', '14', 'merchants'),
    feature('txn_amt_24h_sum', '420', '390', 'USD'),
    feature('rapid_fire_precursor', 'No', 'No', ''),
    feature('is_known_category', 'Yes', 'Yes', ''),
  ],
  anomaly_top_contributors: [
    { feature: 'Implied travel speed', contribution_pct: 46 },
    { feature: 'Distance from last transaction', contribution_pct: 28 },
    { feature: 'Time of day', contribution_pct: 14 },
    { feature: 'Foreign currency flag', contribution_pct: 7 },
    { feature: 'Amount vs 90-day median', contribution_pct: 5 },
  ],
  xgboost_feature_contributions: [
    { feature: 'Implied travel speed', shap_value: 1.9 },
    { feature: 'Distance (km)', shap_value: 0.87 },
    { feature: 'Foreign currency flag', shap_value: 0.55 },
    { feature: 'Merchant MCC risk', shap_value: 0.31 },
    { feature: 'Known category', shap_value: -0.12 },
  ],
  recent_transactions: makeRecentTransactions(2, 80),
  ...NETWORK_IMPOSSIBLE,
} as ScoreResponse;

/** High-value spike at a brand-new merchant during the evening. */
const AMOUNT_SPIKE: ScoreResponse = {
  transaction_id: 'tx_9003',
  cc_num: 5105105105105100,
  decision: 'REVIEW_UNUSUAL',
  risk_level: 'MODERATE',
  fraud_probability: 0.51,
  anomaly_score: 0.47,
  verification_action: 'Push notification sent. Expires in 6:10.',
  features: [
    feature('amt_over_median_90d', '7.8x', '1.0x', 'multiplier'),
    feature('amt', '2,300', '295', 'USD'),
    feature('is_new_merchant', 'Yes', 'N/A', ''),
    feature('txn_count_1h', '2', '1.2', 'txn/hour'),
    feature('time_of_day', '22:38', '09:00 - 21:00', ''),
    feature('dist_from_home_km', '14', '0', 'km'),
    feature('implied_velocity_kmh', '40', 'N/A', 'km/h'),
    feature('is_known_category', 'Yes', 'Yes', ''),
    feature('merchant_mcc_risk', '0.35', '0.3', 'score'),
    feature('is_failed_auth', 'No', 'No', ''),
    feature('fx_flag', 'No', 'No', ''),
    feature('txn_count_30d', '34', '30', 'txn'),
    feature('distinct_merchants_30d', '15', '16', 'merchants'),
    feature('txn_amt_24h_sum', '2,980', '510', 'USD'),
    feature('rapid_fire_precursor', 'No', 'No', ''),
    feature('is_weekend', 'Yes', 'Yes', ''),
  ],
  anomaly_top_contributors: [
    { feature: 'Amount vs 90-day median', contribution_pct: 39 },
    { feature: 'New merchant', contribution_pct: 25 },
    { feature: 'Time of day', contribution_pct: 18 },
    { feature: 'Transaction velocity (1h)', contribution_pct: 10 },
    { feature: 'Distance from home', contribution_pct: 8 },
  ],
  xgboost_feature_contributions: [
    { feature: 'Amount vs median', shap_value: 2.1 },
    { feature: 'Amount (24h sum)', shap_value: 1.4 },
    { feature: 'New merchant', shap_value: 0.9 },
    { feature: 'Time of day', shap_value: 0.42 },
    { feature: 'Is weekend', shap_value: -0.28 },
    { feature: 'Known category', shap_value: -0.15 },
  ],
  recent_transactions: makeRecentTransactions(3, 40),
  ...NETWORK_AMOUNT_SPIKE,
} as ScoreResponse;

/** Repeated failures followed by a large success — credential-stuffing signal. */
const FAILED_AUTH: ScoreResponse = {
  transaction_id: 'tx_9004',
  cc_num: 5555555555554444,
  decision: 'BLOCK',
  risk_level: 'HIGH',
  fraud_probability: 0.91,
  anomaly_score: 0.86,
  verification_action: 'Payment held. Awaiting biometric verification.',
  features: [
    feature('is_failed_auth', 'Yes', 'No', ''),
    feature('failed_auth_24h', '7', '0.2', 'attempts'),
    feature('txn_count_1h', '1', '1.1', 'txn/hour'),
    feature('amt_over_median_90d', '5.2x', '1.0x', 'multiplier'),
    feature('is_new_merchant', 'No', 'N/A', ''),
    feature('dist_from_home_km', '9', '0', 'km'),
    feature('time_of_day', '03:12', '08:00 - 22:00', ''),
    feature('is_weekend', 'No', 'No', ''),
    feature('merchant_mcc_risk', '0.66', '0.3', 'score'),
    feature('fx_flag', 'No', 'No', ''),
    feature('txn_count_30d', '26', '34', 'txn'),
    feature('distinct_merchants_30d', '10', '13', 'merchants'),
    feature('txn_amt_24h_sum', '1,405', '420', 'USD'),
    feature('rapid_fire_precursor', 'No', 'No', ''),
    feature('implied_velocity_kmh', '18', 'N/A', 'km/h'),
    feature('is_known_category', 'Yes', 'Yes', ''),
  ],
  anomaly_top_contributors: [
    { feature: 'Failed auth attempts (24h)', contribution_pct: 42 },
    { feature: 'Time of day', contribution_pct: 22 },
    { feature: 'Amount vs 90-day median', contribution_pct: 18 },
    { feature: 'Merchant MCC risk', contribution_pct: 11 },
    { feature: 'Transaction velocity (1h)', contribution_pct: 7 },
  ],
  xgboost_feature_contributions: [
    { feature: 'Failed auth attempts', shap_value: 3.2 },
    { feature: 'Amount vs median', shap_value: 1.1 },
    { feature: 'Merchant MCC risk', shap_value: 0.8 },
    { feature: 'Time of day', shap_value: 0.5 },
    { feature: 'Is weekend', shap_value: -0.1 },
    { feature: 'Known category', shap_value: -0.3 },
  ],
  recent_transactions: makeRecentTransactions(4, 30),
  ...NETWORK_FAILED_AUTH,
} as ScoreResponse;

/** Low-hum odd-hours cluster — REVIEW_UNUSUAL, live customer confirm. */
const ODD_HOURS: ScoreResponse = {
  transaction_id: 'tx_9005',
  cc_num: 4222222222222,
  decision: 'REVIEW_UNUSUAL',
  risk_level: 'MODERATE',
  fraud_probability: 0.44,
  anomaly_score: 0.41,
  verification_action: 'Customer confirmation requested.',
  features: [
    feature('time_of_day', '04:52', '08:00 - 23:00', ''),
    feature('is_weekend', 'No', 'No', ''),
    feature('txn_count_1h', '3', '0.8', 'txn/hour'),
    feature('amt_over_median_90d', '1.4x', '1.0x', 'multiplier'),
    feature('is_new_merchant', 'No', 'N/A', ''),
    feature('dist_from_home_km', '4', '0', 'km'),
    feature('implied_velocity_kmh', '15', 'N/A', 'km/h'),
    feature('is_known_category', 'Yes', 'Yes', ''),
    feature('merchant_mcc_risk', '0.28', '0.3', 'score'),
    feature('is_failed_auth', 'No', 'No', ''),
    feature('fx_flag', 'No', 'No', ''),
    feature('txn_count_30d', '29', '33', 'txn'),
    feature('distinct_merchants_30d', '12', '14', 'merchants'),
    feature('txn_amt_24h_sum', '205', '180', 'USD'),
    feature('rapid_fire_precursor', 'Yes', 'No', ''),
    feature('is_online', 'No', 'No', ''),
  ],
  anomaly_top_contributors: [
    { feature: 'Time of day', contribution_pct: 44 },
    { feature: 'Transaction velocity (1h)', contribution_pct: 27 },
    { feature: 'Rapid-fire precursor', contribution_pct: 15 },
    { feature: 'Amount vs 90-day median', contribution_pct: 8 },
    { feature: 'Distance from home', contribution_pct: 6 },
  ],
  xgboost_feature_contributions: [
    { feature: 'Time of day', shap_value: 0.84 },
    { feature: 'Transaction velocity (1h)', shap_value: 0.5 },
    { feature: 'Merchant MCC risk', shap_value: -0.18 },
    { feature: 'Known category', shap_value: -0.12 },
  ],
  recent_transactions: makeRecentTransactions(5, 25),
  ...NETWORK_ODD_HOURS,
} as ScoreResponse;

export const SCORES: ScoreResponse[] = [
  CARD_TEST,
  IMPOSSIBLE_TRAVEL,
  AMOUNT_SPIKE,
  FAILED_AUTH,
  ODD_HOURS,
];

const MERCHANTS: Record<string, string> = {
  tx_9001: 'fraud_Kerluke',
  tx_9002: 'GlobalAirlines',
  tx_9003: 'Grand Hotel',
  tx_9004: 'WireTransferPlus',
  tx_9005: 'MidnightMart',
};

const TIMES: Record<string, string> = {
  tx_9001: '2026-09-15 02:47:00',
  tx_9002: '2026-09-14 21:04:00',
  tx_9003: '2026-09-14 22:38:00',
  tx_9004: '2026-09-15 03:12:00',
  tx_9005: '2026-09-13 04:52:00',
};

export const ALERTS: AlertItem[] = SCORES.map((s) => ({
  transaction_id: s.transaction_id,
  cc_num: s.cc_num,
  customer_name: CUSTOMER_NAMES[s.cc_num] ?? `Customer #${s.cc_num}`,
  amount: Number(s.features.find((f) => f.name === 'amt')?.value ?? 0),
  currency: currencyOf(s.cc_num),
  merchant: MERCHANTS[s.transaction_id],
  time: TIMES[s.transaction_id],
  decision: s.decision as Decision,
  risk_level: s.risk_level as RiskLevel,
  fraud_probability: s.fraud_probability,
  anomaly_score: s.anomaly_score,
}));

const CASE_REPORTS: Record<string, ExplainResponse['case_report']> = {
  tx_9001: {
    verdict:
      'BLOCK — high confidence fraud. This transaction is 12x the customer\u2019s typical spend, at a merchant they\u2019ve never visited, after 6 transactions in the past hour.',
    evidence: [
      'Transaction velocity: 6 in the past hour (customer\u2019s norm: ~1.2/hour). Rapid-fire small transactions followed by a large one is a common card-testing pattern.',
      'Amount: 560, which is 12.4x this customer\u2019s 90-day median of 45.23.',
      'Preceded by 5 small authorize attempts that all failed — a credential-stuffing signature.',
      'The merchant (fraud_Kerluke) has never appeared in this customer\u2019s history.',
    ],
    pattern_match:
      'This matches the card-testing typology: rapid small transactions followed by a large one.',
    recommended_action:
      'Freeze the card and contact the customer to verify. If confirmed fraud, escalate to disputes.',
  },
  tx_9002: {
    verdict:
      'REVIEW_STEALTH — likely fraud. The previous transaction was in Cairo minutes before this 1,200 km-away purchase; no flight makes that trip in time.',
    evidence: [
      'Implied travel speed: 2,400 km/h between this and the previous transaction — physically impossible.',
      'Distance from the previous transaction: 1,200 km while the customer\u2019s norm is ~18 km.',
      'Foreign-currency flag set to \u2018yes\u2019 and the destination is a new locale.',
    ],
    pattern_match:
      'This matches the impossible-travel typology: more than one transaction is unlikely to be genuinely from the cardholder in this time window.',
    recommended_action:
      'Send a stealth push verification (no visible fraud language). If the customer confirms a lost/stolen card, block and file a dispute.',
  },
  tx_9003: {
    verdict:
      'REVIEW_UNUSUAL — possible fraud. One unusually large purchase at a merchant the customer has never used before, outside their typical hours.',
    evidence: [
      'Amount: 2,300, which is 7.8x this customer\u2019s 90-day median of 295.',
      'The merchant (Grand Hotel) has never appeared in this customer\u2019s history.',
      'The purchase occurred at 22:38, well outside the customer\u2019s normal 09:00–21:00 window.',
    ],
    pattern_match:
      'This does not match any single known fraud typology; the flag is driven by an amount spike combined with a new merchant.',
    recommended_action:
      'Verify with the customer before settling. If legitimate (e.g., booking a trip), log the merchant to the allowlist.',
  },
  tx_9004: {
    verdict:
      'BLOCK — high confidence fraud. Seven failed sign-in attempts preceded a far-above-baseline transfer to a high-risk wire merchant.',
    evidence: [
      'Failed authentication: 7 failed attempts in the last 24h (customer\u2019s norm: ~0.2/hour).',
      'Amount: 1,405, which is 5.2x this customer\u2019s 90-day median.',
      'Merchant MCC risk score of 0.66, above this customer\u2019s usual non-card-present spend.',
      'Occurred at 03:12 local time, outside the customer\u2019s 08:00–22:00 window.',
    ],
    pattern_match:
      'This matches the account-takeover typology: credential stuffing followed by a high-value card-not-present transfer.',
    recommended_action:
      'Block immediately, force a password reset and biometric re-enrolment, then alert the customer.',
  },
  tx_9005: {
    verdict:
      'REVIEW_UNUSUAL — a cluster of small purchases in the early hours; low fraud probability but outside normal behavior.',
    evidence: [
      'Time: 04:52, well outside the customer\u2019s 08:00–23:00 activity window.',
      'Transaction velocity: 3 in the past hour, all from nearby known merchants.',
      'Amounts are within normal bounds (1.4x median), so this is behavioral-anomaly rather than spend-fraud.',
    ],
    pattern_match:
    'This does not match any known fraud pattern. The flag is driven by behavioral anomaly alone.',
    recommended_action:
      'Request customer confirmation. If they confirm (e.g., a night-shift start), no action is needed beyond a note in the profile.',
  },
};

export function getScore(txIdOrCcNum: string | number): ScoreResponse | undefined {
  const key = String(txIdOrCcNum);
  return SCORES.find(
    (s) => s.transaction_id === key || String(s.cc_num) === key,
  );
}

export function getExplain(txId: string): ExplainResponse | undefined {
  const score = getScore(txId);
  if (!score) return undefined;
  const base = CASE_REPORTS[score.transaction_id];
  // Append network context to the case report so the explanation surfaces the
  // graph findings alongside the per-transaction evidence (PLAN §12).
  const networkEvidence: string[] = score.network_available
    ? [
        `Network risk score ${score.network_risk_score.toFixed(4)} (graph axis available).`,
        ...score.network_findings,
      ]
    : [];
  const case_report = {
    ...base,
    evidence: [...base.evidence, ...networkEvidence],
    crosschecked: true,
    hallucination_flagged: false,
  };
  return {
    transaction_id: score.transaction_id,
    cc_num: score.cc_num,
    risk_level: score.risk_level,
    verification_action: score.verification_action,
    case_report,
  };
}

const median = (value: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'EGP', maximumFractionDigits: 0 }).format(value);

export function getProfile(ccNum: number): CustomerProfileResponse | undefined {
  const score = getScore(ccNum);
  if (!score) return undefined;

  const fraud = score.fraud_probability >= 0.8;
  const drifty = ccNum === 4012888888881881; // impossible-travel customer
  const boosted = ccNum === 4716561796955522; // card-testing customer

  return {
    cc_num: ccNum,
    long_term_baseline: {
      median_amount: median(45),
      typical_hours: '9am – 8pm',
      home_location: 'Cairo',
      distinct_merchants: 12,
      daily_txn_count: 1.8,
    },
    recent_behavior: {
      median_amount: median(drifty ? 190 : 600),
      typical_hours: '10am – 10pm',
      home_location: drifty ? 'Alexandria' : 'Cairo',
      distinct_merchants: 8,
      daily_txn_count: 3.2,
    },
    drift_detected: drifty
      ? {
          kind: 'sudden',
          severity: 'red',
          message:
            'Sudden behavioral shift: location jumped 650 km in the last 2 hours. Possible account takeover.',
        }
      : {
          kind: 'gradual',
          severity: 'yellow',
          message:
            'Behavioral drift detected: location shifted 30 km, spending up 2.7x, gradual shift over 3 weeks. Likely lifestyle change.',
        },
    trust_status: boosted
      ? {
          level: 'boosted',
          message:
            '3 recent false alarms confirmed — trust boosted (anomaly score reduced by 30%)',
        }
      : fraud
        ? {
            level: 'alert',
            message:
              'Recent fraud confirmed — heightened alert (fraud probability boosted by +0.1)',
          }
        : {
            level: 'normal',
            message: 'Normal — no recent feedback',
          },
  };
}

/** Network (graph) context for the customer profile page (PLAN §12). Derives
 * the ego + community payload from the same fixture scores so the profile's
 * Network panel is navigable without an open alert. */
export function getNetwork(ccNum: number): CustomerNetwork | undefined {
  const score = getScore(ccNum);
  if (!score) return undefined;
  return {
    cc_num: ccNum,
    network_risk_score: score.network_risk_score,
    available: score.network_available,
    findings: score.network_findings,
    features: score.network_features ?? {
      merchant_degree: 0,
      merchant_fan_in: 0,
      shared_counterparty_count: 0,
      co_occurrence_count: 0,
      flagged_neighbor_count: 0,
      flagged_exposure: 0,
      cluster_size: 0,
      cluster_flagged_ratio: 0,
    },
    ego: score.network_ego ?? { nodes: [], edges: [] },
    community: score.network_community,
  };
}

export const FEEDBACK_HISTORY: FeedbackHistoryEntry[] = [
  {
    transaction_id: 'tx_8901',
    merchant: 'fraud_Kerluke',
    amount: 88,
    currency: 'USD',
    time: '2026-09-10 19:20:00',
    decision: 'REVIEW_UNUSUAL',
    analyst_decision: 'false_alarm',
    notes: 'Customer called and confirmed they are traveling.',
  },
  {
    transaction_id: 'tx_8902',
    merchant: 'WireTransferPlus',
    amount: 1240,
    currency: 'USD',
    time: '2026-09-08 02:05:00',
    decision: 'BLOCK',
    analyst_decision: 'confirmed_fraud',
    notes: 'Card reported stolen; funds recovered.',
  },
  {
    transaction_id: 'tx_8903',
    merchant: 'Cafe Napoli',
    amount: 22,
    currency: 'USD',
    time: '2026-09-05 12:10:00',
    decision: 'REVIEW_STEALTH',
    analyst_decision: 'customer_confirmed_legitimate',
  },
];

export const FEEDBACK_STATS: FeedbackStats = {
  total_feedback: 142,
  confirmed_fraud: 89,
  false_alarm: 48,
  customer_confirmed_legitimate: 5,
  false_positive_rate: 48 / 142, // 33.8% — false alarms over total feedback
  feedback_by_decision: [
    { decision: 'BLOCK', total_reviewed: 80, confirmed_fraud: 72, false_alarm: 8, fraud_rate: 72 / 80 },
    { decision: 'REVIEW_STEALTH', total_reviewed: 35, confirmed_fraud: 15, false_alarm: 20, fraud_rate: 15 / 35 },
    { decision: 'REVIEW_UNUSUAL', total_reviewed: 27, confirmed_fraud: 2, false_alarm: 25, fraud_rate: 2 / 27 },
  ],
};