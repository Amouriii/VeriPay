import type { ShapAttributionDto } from '../types';

export function SHAPReasonList({ attributions }: { attributions: ShapAttributionDto[] }) {
  return (
    <ul className="space-y-2 text-sm">
      {attributions.map((a) => (
        <li key={a.reasonCode} className="glass-field flex items-center justify-between rounded-lg px-3 py-2">
          <span className="font-medium text-ink">{a.reasonCode}</span>
          <span className={a.direction === 'increases' ? 'font-semibold text-red-600 dark:text-red-400' : 'font-semibold text-emerald-600 dark:text-emerald-400'}>
            {a.direction === 'increases' ? '↑' : '↓'} risk
          </span>
        </li>
      ))}
    </ul>
  );
}
