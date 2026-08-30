import type { FeatureRow, ScoreResponse } from '../../types/analyst';
import { formatPercent } from '../../components/analyst/ui';

function baselineTone(value: string, baseline: string): string {
  if (!baseline || baseline === 'N/A') return 'border-slate-300 bg-white text-slate-700';
  const num = parseFloat(String(value).replace(/[^0-9.]/g, ''));
  const base = parseFloat(String(baseline).replace(/[^0-9.]/g, ''));
  if (Number.isNaN(num) || Number.isNaN(base)) return 'border-slate-300 bg-white text-slate-700';
  const ratio = base === 0 ? (num > 0 ? 99 : 1) : num / base;
  // Heuristic coloring: near baseline = green, moderately far = yellow, extreme = red.
  if (ratio <= 1.5 && ratio >= 0.5) return 'border-emerald-300 bg-emerald-50 text-emerald-800';
  if (ratio <= 4 && ratio >= 0.25) return 'border-amber-300 bg-amber-50 text-amber-800';
  return 'border-red-300 bg-red-50 text-red-800';
}

export function AnomalyContributors({ score }: { score: ScoreResponse }) {
  return (
    <ul className="space-y-2">
      {score.anomaly_top_contributors.map((c) => (
        <li key={c.feature} className="flex items-center justify-between gap-3">
          <span className="max-w-[60%] text-sm text-slate-700">{c.feature}</span>
          <span className="w-24 shrink-0 text-right font-semibold tabular-nums text-[#201b4b]">
            {formatPercent(c.contribution_pct / 100, 0)}
          </span>
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-[#29265f]"
              style={{ width: `${c.contribution_pct}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}

export function ShapValues({ score }: { score: ScoreResponse }) {
  return (
    <ul className="space-y-2">
      {score.xgboost_feature_contributions.map((c) => {
        const towardFraud = c.shap_value >= 0;
        return (
          <li
            key={c.feature}
            className={`rounded-lg border-l-4 px-3 py-2 text-sm ${
              towardFraud
                ? 'border-red-400 bg-red-50'
                : 'border-emerald-400 bg-emerald-50'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-medium text-slate-800">{c.feature}</span>
              <span
                className={`font-semibold tabular-nums ${
                  towardFraud ? 'text-red-700' : 'text-emerald-700'
                }`}
              >
                {c.shap_value > 0 ? '+' : ''}
                {c.shap_value.toFixed(2)}
              </span>
            </div>
            <p className={`mt-0.5 text-xs ${towardFraud ? 'text-red-600' : 'text-emerald-700'}`}>
              {towardFraud ? 'pushes toward fraud' : 'pushes toward legitimate'}
            </p>
          </li>
        );
      })}
    </ul>
  );
}

export function FeatureTable({ features }: { features: FeatureRow[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[560px] text-left text-sm">
        <thead className="bg-slate-50 text-[11px] uppercase tracking-[0.14em] text-slate-500">
          <tr>
            <th className="px-3 py-2 font-semibold">Feature</th>
            <th className="px-3 py-2 font-semibold">Current Value</th>
            <th className="px-3 py-2 font-semibold">Customer Baseline</th>
            <th className="px-3 py-2 font-semibold">Unit</th>
          </tr>
        </thead>
        <tbody>
          {features.map((f) => {
            const value = `${f.value}${f.unit ? ` ${f.unit}` : ''}`;
            const base = f.customer_baseline === 'N/A' ? 'N/A' : `${f.customer_baseline}${f.unit ? ` ${f.unit}` : ''}`;
            return (
              <tr key={f.name} className="border-t border-slate-100">
                <td className="px-3 py-2 font-mono text-xs text-slate-800">{f.name}</td>
                <td className="px-3 py-2">
                  <span
                    className={`inline-block rounded-md border px-2 py-0.5 text-xs font-semibold tabular-nums ${baselineTone(f.value, f.customer_baseline)}`}
                  >
                    {value}
                  </span>
                </td>
                <td className="px-3 py-2 text-xs text-slate-600">{base}</td>
                <td className="px-3 py-2 text-xs text-slate-500">{f.unit || '—'}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}