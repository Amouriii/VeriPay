// Mirrors libs/veripay_common/veripay_common/enums.py and proto/veripay/*.
// Single source of truth for string values shared with the backend.

export enum DecisionAction {
  ALLOW = 'ALLOW',
  MONITOR = 'MONITOR',
  CHALLENGE = 'CHALLENGE',
  REVIEW = 'REVIEW',
  DECLINE = 'DECLINE',
  REVERSE = 'REVERSE',
}

export enum RiskBand {
  APPROVE = 'APPROVE',
  VERIFY = 'VERIFY',
  BLOCK = 'BLOCK',
}

export enum DcvvStatus {
  MATCH = 'MATCH',
  MISMATCH = 'MISMATCH',
  EXPIRED = 'EXPIRED',
  NOT_APPLICABLE = 'NOT_APPLICABLE',
}

export enum GpvOutcome {
  MATCHED = 'MATCHED',
  LIKELY_MATCH = 'LIKELY_MATCH',
  MISMATCHED = 'MISMATCHED',
}
