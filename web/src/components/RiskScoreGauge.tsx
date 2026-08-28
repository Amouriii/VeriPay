// Displays the unified 0-100 risk score with band color (PLAN §7).
import type { RiskScoreDto } from '../types';

export function RiskScoreGauge({ score }: { score: RiskScoreDto }) {
  const band =
    score.band === 'BLOCK'
      ? { chip: 'bg-red-500/10 text-red-600 ring-red-500/25 dark:bg-red-400/15 dark:text-red-300 dark:ring-red-400/30', bar: 'bg-red-500' }
      : score.band === 'VERIFY'
        ? { chip: 'bg-amber-400/15 text-amber-700 ring-amber-500/30 dark:bg-amber-400/10 dark:text-amber-300 dark:ring-amber-400/25', bar: 'bg-amber-400' }
        : { chip: 'bg-emerald-500/10 text-emerald-700 ring-emerald-500/25 dark:bg-emerald-400/10 dark:text-emerald-300 dark:ring-emerald-400/25', bar: 'bg-emerald-500' };
  return (
    <div className="glass-panel rounded-2xl p-5">
      <div className="flex items-center justify-between">
        <p className="text-[13px] font-medium text-ink-muted">Unified risk score</p>
        <span className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ring-1 ring-inset ${band.chip}`}>{score.band}</span>
      </div>
      <p className="mt-3 text-4xl font-bold tracking-tight text-ink">{score.unifiedScore}</p>
      <div className="mt-4 h-2 rounded-full bg-ink/[0.08] dark:bg-white/10">
        <div className={`h-2 rounded-full ${band.bar}`} style={{ width: `${Math.max(0, Math.min(100, score.unifiedScore))}%` }} />
      </div>
    </div>
  );
}
