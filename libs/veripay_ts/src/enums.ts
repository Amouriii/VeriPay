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

export enum RiskTier {
  NO_RISK = 'NO_RISK',
  LOW = 'LOW',
  MODERATE = 'MODERATE',
  HIGH = 'HIGH',
}

export enum RiskBand {
  APPROVE = 'APPROVE',
  VERIFY = 'VERIFY',
  BLOCK = 'BLOCK',
}

export enum FrictionType {
  NONE = 'NONE',
  PUSH = 'PUSH',
  BIOMETRIC = 'BIOMETRIC',
  MULTI_FACTOR = 'MULTI_FACTOR',
}

export enum PaymentRail {
  CARD = 'CARD',
  ISO_8583 = 'ISO_8583',
  FEDNOW = 'FEDNOW',
  RTP = 'RTP',
  ACH = 'ACH',
  SWIFT = 'SWIFT',
  ISO_20022 = 'ISO_20022',
  DOMESTIC_INSTANT = 'DOMESTIC_INSTANT',
}

export enum ProcessingPath {
  FAST = 'FAST',
  SECONDARY = 'SECONDARY',
}

export enum VerificationOutcome {
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  DENIED = 'DENIED',
  TIMED_OUT = 'TIMED_OUT',
  EXPIRED = 'EXPIRED',
  LOCKED = 'LOCKED',
  ESCALATED = 'ESCALATED',
}

export enum IntegrityStatus {
  PASS = 'PASS',
  FAIL = 'FAIL',
  UNAVAILABLE = 'UNAVAILABLE',
}

export enum EscalationStatus {
  OPEN = 'OPEN',
  ASSIGNED = 'ASSIGNED',
  RESOLVED = 'RESOLVED',
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
