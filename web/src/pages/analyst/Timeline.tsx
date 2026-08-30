import type { RecentTransaction } from '../../types/analyst';
import { formatMoney } from '../../components/analyst/ui';

export function Timeline({ txs, currency }: { txs: RecentTransaction[]; currency: string }) {
  const amounts = txs.map((t) => t.amount);
  const max = Math.max(...amounts, 1);
  const min = Math.min(...amounts, 1);

  // Highlight escalation: the most recent large entries get heavier reds.
  const toneFor = (amount: number) => {
    const ratio = (amount - min) / (max - min || 1);
    if (ratio > 0.85) return 'bg-red-500';
    if (ratio > 0.6) return 'bg-red-300';
    if (ratio > 0.35) return 'bg-orange-300';
    return 'bg-[#43cddd]';
  };

  return (
    <div className="max-h-[560px] overflow-y-auto pr-2 vp-scrollbar">
      <ol className="relative space-y-0 border-l-2 border-slate-200 pl-6">
        {txs.map((t, i) => (
          <li key={`${t.time}-${i}`} className="relative pb-5">
            <span className="absolute -left-[31px] top-1 h-2.5 w-2.5 rounded-full border-2 border-white bg-[#43cddd]" />
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <div>
                <p className="text-sm font-medium text-slate-800">{t.merchant}</p>
                <p className="text-xs text-slate-500">
                  {new Date(t.time).toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                  {' · '}
                  {t.category} · {t.location}
                </p>
              </div>
              <span className="font-semibold tabular-nums text-[#201b4b]">{formatMoney(t.amount, currency)}</span>
            </div>
            {/* Progressive amount bar — the escalating "sequence" the transformer learns from. */}
            <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-100">
              <div
                className={`h-full rounded-full ${toneFor(t.amount)}`}
                style={{ width: `${(t.amount / max) * 100}%` }}
              />
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}