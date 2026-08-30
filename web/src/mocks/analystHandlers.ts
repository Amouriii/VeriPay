// MSW handlers for the fraud-analyst console. Paths and payloads mirror the
// Analyst API contract described by the dashboard UI guide. The console is fully
// navigable in dev mode without a backend.
import { http, HttpResponse } from 'msw';
import type {
  AnalystDecision,
  FeedbackInput,
  HealthResponse,
  RetrainResponse,
} from '../types/analyst';
import {
  ALERTS,
  FEEDBACK_HISTORY,
  FEEDBACK_STATS,
  getExplain,
  getProfile,
  getScore,
} from './analystData';

const VALID_DECISIONS: AnalystDecision[] = [
  'confirmed_fraud',
  'false_alarm',
  'customer_confirmed_legitimate',
];

// Seed the "already reported" set with past feedback so a resubmission conflicts.
const submitted = new Set<string>(FEEDBACK_HISTORY.map((h) => h.transaction_id));

const health: HealthResponse = {
  status: 'ok',
  models_loaded: ['ECOD (unsupervised)', 'XGBoost (supervised)', 'Transformer (sequence)'],
  model_versions: {
    ecod: 'v12',
    xgboost: 'v38',
    transformer: 'v5',
  },
};

export const analystHandlers = [
  // Screen 1 — the Alert Queue is the stored, non-PASS results of /score.
  http.get('*/api/alerts', () => HttpResponse.json(ALERTS)),

  // Screens 1, 3, 4 — full scoring output (features, contributors, SHAP, timeline).
  http.post('*/api/score', async ({ request }) => {
    const body = (await request.json()) as { cc_num?: number; transaction_id?: string };
    const id = body.transaction_id ?? body.cc_num;
    const score = id === undefined ? undefined : getScore(id);
    if (!score) return HttpResponse.json({ detail: 'Unknown transaction' }, { status: 404 });
    return HttpResponse.json(score);
  }),

  // Screen 2 — natural-language explanation.
  http.post('*/api/explain', async ({ request }) => {
    const body = (await request.json()) as { cc_num?: number; transaction_id?: string };
    const id = body.transaction_id ?? body.cc_num;
    const explain = id === undefined ? undefined : getExplain(String(id));
    if (!explain) return HttpResponse.json({ detail: 'Unknown transaction' }, { status: 404 });
    return HttpResponse.json(explain);
  }),

  // Screen 5 — customer profile with baselines, drift, trust.
  http.get('*/api/customer/:ccNum/profile', ({ params }) => {
    const ccNum = Number(params.ccNum);
    const profile = getProfile(ccNum);
    if (!profile) return HttpResponse.json({ detail: 'Unknown customer' }, { status: 404 });
    return HttpResponse.json(profile);
  }),

  // Screen 6 — feedback submission.
  http.post('*/api/feedback', async ({ request }) => {
    const input = (await request.json()) as FeedbackInput;
    if (
      !input.transaction_id ||
      !VALID_DECISIONS.includes(input.analyst_decision)
    ) {
      return HttpResponse.json(
        { detail: 'Invalid analyst_decision value' },
        { status: 422 },
      );
    }
    if (submitted.has(input.transaction_id)) {
      return HttpResponse.json(
        { detail: 'Feedback already submitted for this transaction' },
        { status: 409 },
      );
    }
    submitted.add(input.transaction_id);
    return HttpResponse.json({ status: 'recorded' }, { status: 201 });
  }),

  // Screen 7 — performance stats.
  http.get('*/api/feedback/stats', () => HttpResponse.json(FEEDBACK_STATS)),

  // Screen 8 — model info + retraining.
  http.get('*/api/health', () => HttpResponse.json(health)),
  http.post('*/api/retrain', () => {
    const result: RetrainResponse = {
      status: 'completed',
      message: 'Retrained on all analyst feedback.',
      new_version: 'v39',
      metrics: {
        roc_auc: 0.931,
        pr_auc: 0.543,
        precision: 0.52,
        recall: 0.48,
        false_positive_rate: 0.323,
      },
    };
    return HttpResponse.json(result);
  }),
];