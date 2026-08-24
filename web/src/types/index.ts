// DTOs mirroring proto/veripay for the analyst dashboard.
export interface TransactionDto {
  transactionId: string;
  userId: string;
  amountMinor: number;
  currency: string;
  merchantId: string;
}
export interface ComponentScoreDto {
  component: string;
  score: number;
  weight: number;
  available: boolean;
  reasonCode?: string;
}
export interface RiskScoreDto {
  transactionId: string;
  unifiedScore: number;
  band: 'APPROVE' | 'VERIFY' | 'BLOCK';
  components: ComponentScoreDto[];
}
export interface ShapAttributionDto {
  reasonCode: string;
  shapValue: number;
  direction: 'increases' | 'decreases';
}
