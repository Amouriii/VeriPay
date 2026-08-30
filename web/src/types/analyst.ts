// DTOs for the fraud-analyst console. These mirror the backend Analyst API
// (`/score`, `/explain`, `/customer/{cc_num}/profile`, `/feedback`,
// `/feedback/stats`, `/retrain`, `/health`) described by the dashboard UI guide.
// The web demo serves them from MSW (mocks/analystHandlers.ts) so the console is
// fully navigable without a running backend.

export type Decision = 'BLOCK' | 'REVIEW_STEALTH' | 'REVIEW_UNUSUAL' | 'PASS';
export type RiskLevel = 'HIGH' | 'MODERATE' | 'LOW';

export interface FeatureRow {
  name: string;
  value: string;
  customer_baseline: string;
  unit: string;
}

export interface ContributorShare {
  feature: string;
  contribution_pct: number;
}

export interface XgbContribution {
  feature: string;
  shap_value: number;
}

export interface NetworkEgoNode {
  id: string;
  kind: 'customer' | 'merchant';
  label: string;
  status: 'self' | 'flagged' | 'review' | 'normal';
}

export interface NetworkEgoEdge {
  from: string;
  to: string;
  weight: number;
}

export interface NetworkEgo {
  nodes: NetworkEgoNode[];
  edges: NetworkEgoEdge[];
}

export interface NetworkFeatures {
  merchant_degree: number;
  merchant_fan_in: number;
  shared_counterparty_count: number;
  co_occurrence_count: number;
  flagged_neighbor_count: number;
  flagged_exposure: number;
  cluster_size: number;
  cluster_flagged_ratio: number;
}

export interface CommunityStats {
  cluster_size: number;
  flagged_count: number;
  flagged_ratio: number;
  distinct_shared_merchants: number;
  total_volume: number;
  dominant_pattern:
    | 'fraud_ring'
    | 'mixed_cluster'
    | 'shared_merchant_collapse'
    | 'normal_cluster'
    | 'isolated';
}

export interface CommunityMember {
  cc_num: number;
  status: 'self' | 'flagged' | 'normal';
}

export interface Community {
  graph: NetworkEgo;
  stats: CommunityStats;
  members: CommunityMember[];
}

/** Network context returned by GET /customer/{cc_num}/network. */
export interface CustomerNetwork {
  cc_num: number;
  network_risk_score: number;
  available: boolean;
  findings: string[];
  features?: NetworkFeatures;
  ego?: NetworkEgo;
  community?: Community;
}

export interface RecentTransaction {
  time: string;
  amount: number;
  merchant: string;
  category: string;
  location: string;
}

export interface ScoreResponse {
  transaction_id: string;
  cc_num: number;
  decision: Decision;
  risk_level: RiskLevel;
  fraud_probability: number; // 0..1
  anomaly_score: number; // 0..1
  verification_action: string;
  feature_mode?: string; // 'basic' | 'rich'
  features: FeatureRow[];
  features16?: FeatureRow[];
  anomaly_top_contributors: ContributorShare[];
  xgboost_feature_contributions: XgbContribution[];
  recent_transactions: RecentTransaction[];
  network_risk_score: number; // 0..1
  network_available: boolean;
  network_findings: string[];
  network_ego?: NetworkEgo;
  network_features?: NetworkFeatures;
  network_community?: Community;
}

export interface CaseReport {
  verdict: string;
  evidence: string[];
  pattern_match: string;
  recommended_action: string;
  crosschecked?: boolean;
  hallucination_flagged?: boolean;
}

export interface ExplainResponse {
  transaction_id: string;
  cc_num: number;
  risk_level: RiskLevel;
  verification_action: string;
  case_report: CaseReport;
}

/** A row in the Alert Queue (a stored, non-PASS /score result). */
export interface AlertItem {
  transaction_id: string;
  cc_num: number;
  customer_name: string;
  amount: number;
  currency: string;
  merchant: string;
  time: string;
  decision: Decision;
  risk_level: RiskLevel;
  fraud_probability: number;
  anomaly_score: number;
}

export interface Baseline {
  median_amount: string;
  typical_hours: string;
  home_location: string;
  distinct_merchants: number;
  daily_txn_count: number;
}

export interface DriftInfo {
  kind: 'gradual' | 'sudden';
  severity: 'yellow' | 'red';
  message: string;
}

export interface TrustStatus {
  level: 'normal' | 'boosted' | 'alert';
  message: string;
}

export interface CustomerProfileResponse {
  cc_num: number;
  long_term_baseline: Baseline;
  recent_behavior: Baseline;
  drift_detected: DriftInfo | null;
  trust_status: TrustStatus;
}

export type AnalystDecision =
  | 'confirmed_fraud'
  | 'false_alarm'
  | 'customer_confirmed_legitimate';

export interface FeedbackInput {
  transaction_id: string;
  analyst_decision: AnalystDecision;
  analyst_id?: string;
  notes?: string;
}

export interface FeedbackHistoryEntry {
  transaction_id: string;
  merchant: string;
  amount: number;
  currency: string;
  time: string;
  decision: Decision;
  analyst_decision: AnalystDecision;
  notes?: string;
}

export interface FeedbackByDecisionRow {
  decision: Decision;
  total_reviewed: number;
  confirmed_fraud: number;
  false_alarm: number;
  fraud_rate: number; // 0..1
}

export interface FeedbackStats {
  total_feedback: number;
  confirmed_fraud: number;
  false_alarm: number;
  customer_confirmed_legitimate: number;
  false_positive_rate: number; // 0..1
  feedback_by_decision: FeedbackByDecisionRow[];
}

export interface HealthResponse {
  status: string;
  models_loaded: string[];
  model_versions: Record<string, string>;
}

export interface RetrainResponse {
  status: string;
  message?: string;
  new_version?: string;
  metrics: {
    roc_auc: number;
    pr_auc: number;
    precision: number;
    recall: number;
    false_positive_rate: number;
  };
}