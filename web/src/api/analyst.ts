// TanStack Query hooks + mutations for the fraud-analyst console.
// Wire to the Analyst API described in the dashboard UI guide.
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { analystGet, analystPost } from './client';
import { ALERTS } from '../mocks/analystData';
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
        // is unavailable; use the same seeded alerts as local MSW.
        if (import.meta.env.DEV || !import.meta.env.VITE_ANALYST_API_BASE) {
          return ALERTS;
        }
        throw error;
      }
    },
  });
}

export function useScore(txId: string, enabled = true) {
  return useQuery({
    queryKey: ['score', txId],
    queryFn: () => analystPost<ScoreResponse>('/score', scorePayload(txId)),
    enabled,
  });
}

export function useExplain(txId: string, enabled = true) {
  return useQuery({
    queryKey: ['explain', txId],
    queryFn: () => analystPost<ExplainResponse>('/explain', scorePayload(txId)),
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
    queryFn: () => analystGet<FeedbackStats>('/feedback/stats'),
  });
}

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => analystGet<HealthResponse>('/health'),
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
    mutationFn: () => analystPost<RetrainResponse>('/retrain'),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['health'] });
    },
  });
}