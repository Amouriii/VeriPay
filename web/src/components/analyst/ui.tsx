import type { Decision, RiskLevel } from '../../types/analyst';

export function formatMoney(
  amount: number,
  currency = 'USD',
  maximumFractionDigits = 2,
): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    maximumFractionDigits,
  }).format(amount);
}

export function formatDate(value: string): string {
  const iso = value.includes('T')
    ? value
    : `${value.replace(' ', 'T')}Z`;
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso));
}

export function formatPercent(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`;
}

const DECISION_STYLES: Record<Decision, string> = {
  BLOCK: 'bg-red-100 text-red-700 ring-red-600/25',
  REVIEW_STEALTH: 'bg-orange-100 text-orange-800 ring-orange-600/25',
  REVIEW_UNUSUAL: 'bg-amber-100 text-amber-800 ring-amber-500/30',
  PASS: 'bg-emerald-100 text-emerald-700 ring-emerald-600/25',
};

export function DecisionBadge({ decision }: { decision: Decision }) {
  return (
    <span
      className={`inline-flex items-center whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-bold ring-1 ring-inset ${DECISION_STYLES[decision]}`}
    >
      {decision.replaceAll('_', ' ')}
    </span>
  );
}

const RISK_STYLES: Record<RiskLevel, string> = {
  HIGH: 'bg-red-100 text-red-700 ring-red-600/25',
  MODERATE: 'bg-orange-100 text-orange-800 ring-orange-600/25',
  LOW: 'bg-emerald-100 text-emerald-700 ring-emerald-600/25',
};

export function RiskPill({ level }: { level: RiskLevel }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-bold ring-1 ring-inset ${RISK_STYLES[level]}`}
    >
      {level}
    </span>
  );
}

export function ScoreBar({ value, label }: { value: number; label: string }) {
  const pct = Math.round(value * 100);
  const tone =
    value >= 0.8 ? 'bg-red-500' : value >= 0.5 ? 'bg-orange-400' : 'bg-emerald-500';
  return (
    <div>
      <div className="flex items-center justify-between text-xs">
        <span className="font-medium text-ink-muted">{label}</span>
        <span className="font-semibold tabular-nums text-ink">{pct}%</span>
      </div>
      <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-ink/[0.08]">
        <div className={`h-full rounded-full ${tone}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}