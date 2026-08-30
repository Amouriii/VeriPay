// @vitest-environment node
//
// Contract tests for the fraud-analyst console API. They exercise the actual
// MSW handlers the demo serves against a bundled node server, verifying the
// response shapes and status codes the UI screens depend on.
import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { setupServer } from 'msw/node';
import { analystHandlers } from '../src/mocks/analystHandlers';

const server = setupServer(...analystHandlers);
const BASE = 'http://localhost/api';

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

type JsonHeaders = { 'Content-Type': string };
const json = (value: unknown) => JSON.stringify(value);
const post = (path: string, body: unknown) =>
  fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' } as JsonHeaders,
    body: json(body),
  });

describe('Alert Queue', () => {
  it('returns only non-PASS stored scores with row fields', async () => {
    const res = await fetch(`${BASE}/alerts`);
    expect(res.status).toBe(200);
    const alerts = await res.json();
    expect(alerts.length).toBeGreaterThan(0);
    for (const a of alerts) {
      expect(a.transaction_id).toBeTypeOf('string');
      expect(a.customer_name).toBeTypeOf('string');
      expect(a.merchant).toBeTypeOf('string');
      expect(['BLOCK', 'REVIEW_STEALTH', 'REVIEW_UNUSUAL']).toContain(a.decision);
      expect(['HIGH', 'MODERATE']).toContain(a.risk_level);
    }
  });
});

describe('/score', () => {
  it('returns decision, features, contributors, SHAP, and timeline', async () => {
    const res = await post('/score', { transaction_id: 'tx_9001' });
    expect(res.status).toBe(200);
    const score = await res.json();
    expect(score.decision).toBe('BLOCK');
    expect(score.risk_level).toBe('HIGH');
    expect(score.features.length).toBeGreaterThanOrEqual(16);
    expect(score.recent_transactions.length).toBe(20);
    expect(score.anomaly_top_contributors[0]).toHaveProperty('contribution_pct');
    expect(score.xgboost_feature_contributions[0]).toHaveProperty('shap_value');
  });

  it('returns the network (graph) scoring axis on a high-risk fixture', async () => {
    const res = await post('/score', { transaction_id: 'tx_9001' });
    const score = await res.json();
    expect(score.network_available).toBe(true);
    expect(score.network_risk_score).toBeTypeOf('number');
    expect(score.network_risk_score).toBeGreaterThan(0);
    expect(score.network_findings.length).toBeGreaterThan(0);
    expect(score.network_ego.nodes.length).toBeGreaterThan(0);
    expect(score.network_ego.edges[0]).toHaveProperty('from');
  });

  it('reports network_available=false for an isolated fixture', async () => {
    const res = await post('/score', { transaction_id: 'tx_9005' });
    const score = await res.json();
    expect(score.network_available).toBe(false);
    expect(score.network_risk_score).toBe(0);
  });

  it('returns the full community payload for the fraud-ring fixture', async () => {
    const res = await post('/score', { transaction_id: 'tx_9001' });
    const score = await res.json();
    expect(score.network_community).toBeDefined();
    const comm = score.network_community;
    expect(comm.stats.cluster_size).toBeGreaterThan(1);
    expect(comm.stats.flagged_count).toBeGreaterThan(0);
    expect(comm.stats.dominant_pattern).toBe('fraud_ring');
    expect(comm.graph.nodes.length).toBeGreaterThan(0);
    expect(comm.members.length).toBeGreaterThan(0);
    expect(comm.members[0]).toHaveProperty('cc_num');
  });

  it('looks up by cc_num too', async () => {
    const res = await post('/score', { cc_num: 4716561796955522 });
    expect(res.status).toBe(200);
    expect((await res.json()).transaction_id).toBe('tx_9001');
  });
});

describe('/explain', () => {
  it('returns a case report with verdict, evidence, pattern, and action', async () => {
    const res = await post('/explain', { transaction_id: 'tx_9001' });
    expect(res.status).toBe(200);
    const explain = await res.json();
    expect(explain.case_report.verdict).toContain('BLOCK');
    expect(explain.case_report.evidence.length).toBeGreaterThanOrEqual(3);
    expect(explain.case_report.pattern_match).toBeTypeOf('string');
    expect(explain.case_report.recommended_action).toBeTypeOf('string');
    expect(explain.verification_action).toBeTypeOf('string');
  });
});

describe('/customer/{cc_num}/profile', () => {
  it('returns baselines, drift, and trust status', async () => {
    const res = await fetch(`${BASE}/customer/4716561796955522/profile`);
    expect(res.status).toBe(200);
    const profile = await res.json();
    expect(profile.long_term_baseline).toHaveProperty('median_amount');
    expect(profile.recent_behavior).toHaveProperty('daily_txn_count');
    expect(profile.drift_detected).toHaveProperty('severity');
    expect(profile.trust_status).toHaveProperty('message');
  });
});

describe('/customer/{cc_num}/network', () => {
  it('returns the ego graph + community for a fraud-ring customer', async () => {
    const res = await fetch(`${BASE}/customer/4716561796955522/network`);
    expect(res.status).toBe(200);
    const net = await res.json();
    expect(net.cc_num).toBe(4716561796955522);
    expect(net.available).toBe(true);
    expect(net.network_risk_score).toBeGreaterThan(0);
    expect(net.findings.length).toBeGreaterThan(0);
    expect(net.ego.nodes.length).toBeGreaterThan(0);
    expect(net.community.stats.dominant_pattern).toBe('fraud_ring');
  });

  it('returns available=false for an isolated customer', async () => {
    const res = await fetch(`${BASE}/customer/4222222222222/network`);
    expect(res.status).toBe(200);
    const net = await res.json();
    expect(net.available).toBe(false);
    expect(net.network_risk_score).toBe(0);
  });
});

describe('/feedback', () => {
  it('returns 201 on the first valid submission', async () => {
    const res = await post('/feedback', {
      transaction_id: 'tx_7777',
      analyst_decision: 'confirmed_fraud',
      notes: 'Customer confirmed fraud.',
    });
    expect(res.status).toBe(201);
  });

  it('returns 409 once feedback has already been given for a transaction', async () => {
    // tx_8901 is pre-seeded as already submitted.
    const res = await post('/feedback', {
      transaction_id: 'tx_8901',
      analyst_decision: 'false_alarm',
    });
    expect(res.status).toBe(409);
  });

  it('returns 422 for an invalid decision value', async () => {
    const res = await post('/feedback', {
      transaction_id: 'tx_8888',
      analyst_decision: 'maybe',
    });
    expect(res.status).toBe(422);
  });
});

describe('/feedback/stats', () => {
  it('returns totals and a false-positive rate equal to false alarms over total', async () => {
    const res = await fetch(`${BASE}/feedback/stats`);
    expect(res.status).toBe(200);
    const stats = await res.json();
    expect(stats.total_feedback).toBeGreaterThan(0);
    expect(stats.feedback_by_decision.length).toBe(3);
    expect(stats.false_positive_rate).toBeCloseTo(
      stats.false_alarm / stats.total_feedback,
      3,
    );
  });
});

describe('/retrain and /health', () => {
  it('retrains and returns evaluation metrics', async () => {
    const res = await fetch(`${BASE}/retrain`, { method: 'POST' });
    expect(res.status).toBe(200);
    const out = await res.json();
    expect(out.status).toBe('completed');
    expect(out.metrics).toHaveProperty('roc_auc');
    expect(out.metrics).toHaveProperty('false_positive_rate');
  });

  it('reports loaded models and versions', async () => {
    const res = await fetch(`${BASE}/health`);
    expect(res.status).toBe(200);
    const health = await res.json();
    expect(health.status).toBe('ok');
    expect(health.models_loaded).toHaveLength(3);
    expect(health.model_versions.xgboost).toBeTypeOf('string');
  });
});