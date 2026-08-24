// TanStack Query hooks for transactions & risk scores (PLAN §20 dashboard).
import { useQuery } from '@tanstack/react-query';
import { apiGet } from './client';
import type { RiskScoreDto, TransactionDto } from '../types';

export function useTransactions() {
  return useQuery({
    queryKey: ['transactions'],
    queryFn: () => apiGet<TransactionDto[]>('/transactions'),
  });
}

export function useRiskScore(txId: string) {
  return useQuery({
    queryKey: ['risk', txId],
    queryFn: () => apiGet<RiskScoreDto>(`/transactions/${txId}/risk`),
  });
}
