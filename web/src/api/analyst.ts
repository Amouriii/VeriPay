// TanStack Query hooks + mutations for the fraud-analyst console.
// Wire to the Analyst API described in the dashboard UI guide.
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from './client';
import type {
  AlertItem,
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
    queryFn: () => apiGet<AlertItem[]>('/alerts'),
  });
}

export function useScore(txId: string, enabled = true) {
  return useQuery({
    queryKey: ['score', txId],
    queryFn: () => apiPost<ScoreResponse>('/score', scorePayload(txId)),
    enabled,
  });
}

export function useExplain(txId: string, enabled = true) {
  return useQuery({
    queryKey: ['explain', txId],
    queryFn: () => apiPost<ExplainResponse>('/explain', scorePayload(txId)),
    enabled,
  });
}

export function useCustomerProfile(ccNum?: number) {
  return useQuery({
    queryKey: ['customer-profile', ccNum],
    queryFn: () =>
      ccNum !== undefined
        ? apiGet<CustomerProfileResponse>(`/customer/${ccNum}/profile`)
        : Promise.reject(new Error('Customer not selected')),
    enabled: ccNum !== undefined,
  });
}

export function useFeedbackStats() {
  return useQuery({
    queryKey: ['feedback-stats'],
    queryFn: () => apiGet<FeedbackStats>('/feedback/stats'),
  });
}

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => apiGet<HealthResponse>('/health'),
    refetchInterval: 30_000,
  });
}

export function useSubmitFeedback() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: FeedbackInput) =>
      apiPost<{ status: string }>('/feedback', input),
    onSuccess: () => {
      // Invalidate stats so the performance page reflects the new verdict.
      void queryClient.invalidateQueries({ queryKey: ['feedback-stats'] });
    },
  });
}

export function useRetrain() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiPost<RetrainResponse>('/retrain'),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['health'] });
    },
  });
}