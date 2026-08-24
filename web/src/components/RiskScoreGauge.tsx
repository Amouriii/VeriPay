// Displays the unified 0-100 risk score with band color (PLAN §7).
import type { RiskScoreDto } from '../types';

export function RiskScoreGauge({ score }: { score: RiskScoreDto }) {
  const bandColor =
    score.band === 'BLOCK' ? 'bg-red-500'
    : score.band === 'VERIFY' ? 'bg-amber-500'
    : 'bg-emerald-500';
  return (
    <div className={`rounded-lg p-4 text-white ${bandColor}`}>
      <div className="text-4xl font-bold">{score.unifiedScore}</div>
      <div className="text-sm">{score.band}</div>
    </div>
  );
}
