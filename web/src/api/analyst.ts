// TanStack Query hooks + mutations for the fraud-analyst console.
// Wire to the Analyst API described in the dashboard UI guide.
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { analystGet, analystPost } from './client';
import { ALERTS, FEEDBACK_STATS, getExplain, getScore } from '../mocks/analystData';

const DEMO_HEALTH: HealthResponse = {
  status: 'demo',
  models_loaded: ['ECOD (unsupervised)', 'XGBoost (supervised)', 'Transformer (sequence)'],
  model_versions: { ecod: 'v12', xgboost: 'v38', transformer: 'v5' },
};

const DEMO_RETRAIN: RetrainResponse = {
  status: 'completed',
  message: 'Retraining simulated using the seeded analyst feedback.',
  new_version: 'v39',
  metrics: { roc_auc: 0.931, pr_auc: 0.543, precision: 0.52, recall: 0.48, false_positive_rate: 0.323 },
};
import type {
  AlertItem,
  CustomerNetwork,
  CustomerProfileResponse,
  ExplainResponse,
  FeedbackInput,
  FeedbackStats,
  HealthResponse,
  RetrainResponse,
  ScoreResponse,
} from '../types';

function scorePayload(txId?: string, ccNum?: number) {
  return txId ? { transaction_id: txId } : { cc_num: ccNum };
}

export function useAlerts() {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: async () => {
      try {
        return await analystGet<AlertItem[]>('/alerts');
      } catch (error) {
        // Keep the demo queue populated when the optional analyst backend
        // is unavailable. This also keeps deployed executive demos usable
        // when the backend URL is configured but not reachable.
        void error;
        return ALERTS;
      }
    },
  });
}

export function useScore(txId: string, enabled = true) {
  return useQuery({
    queryKey: ['score', txId],
    queryFn: async () => {
      try {
        return await analystPost<ScoreResponse>('/score', scorePayload(txId));
      } catch (error) {
        const seeded = ALERTS.find((alert) => alert.transaction_id === txId);
        const fallback = seeded ? getScore(txId) : undefined;
        if (fallback) return fallback;
        throw error;
      }
    },
    enabled,
  });
}

export function useExplain(txId: string, enabled = true) {
  return useQuery({
    queryKey: ['explain', txId],
    queryFn: async () => {
      try {
        return await analystPost<ExplainResponse>('/explain', scorePayload(txId));
      } catch (error) {
        const fallback = getExplain(txId);
        if (fallback) return fallback;
        throw error;
      }
    },
    enabled,
  });
}

export function useCustomerProfile(ccNum?: number) {
  return useQuery({
    queryKey: ['customer-profile', ccNum],
    queryFn: () =>
      ccNum !== undefined
        ? analystGet<CustomerProfileResponse>(`/customer/${ccNum}/profile`)
        : Promise.reject(new Error('Customer not selected')),
    enabled: ccNum !== undefined,
  });
}

export function useCustomerNetwork(ccNum?: number) {
  return useQuery({
    queryKey: ['customer-network', ccNum],
    queryFn: () =>
      ccNum !== undefined
        ? analystGet<CustomerNetwork>(`/customer/${ccNum}/network`)
        : Promise.reject(new Error('Customer not selected')),
    enabled: ccNum !== undefined,
  });
}

export function useFeedbackStats() {
  return useQuery({
    queryKey: ['feedback-stats'],
    queryFn: async () => {
      try {
        return await analystGet<FeedbackStats>('/feedback/stats');
      } catch (error) {
        // Keep deployed demos usable when the optional analyst backend is
        // unavailable by showing the bundled performance fixture.
        void error;
        return FEEDBACK_STATS;
      }
    },
  });
}

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      try {
        return await analystGet<HealthResponse>('/health');
      } catch (error) {
        void error;
        return DEMO_HEALTH;
      }
    },
    refetchInterval: 30_000,
  });
}

export function useSubmitFeedback() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: FeedbackInput) =>
      analystPost<{ status: string }>('/feedback', input),
    onSuccess: () => {
      // Invalidate stats so the performance page reflects the new verdict.
      void queryClient.invalidateQueries({ queryKey: ['feedback-stats'] });
    },
  });
}

export function useRetrain() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      try {
        return await analystPost<RetrainResponse>('/retrain');
      } catch (error) {
        void error;
        return DEMO_RETRAIN;
      }
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['health'] });
    },
  });
}