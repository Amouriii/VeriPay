import { useFeedbackStats } from '../../api/analyst';
import { formatPercent } from '../../components/analyst/ui';

const WEEKLY_FPR = [
  0.412, 0.398, 0.405, 0.372, 0.385, 0.354, 0.361, 0.338,
];
const WEEK_LABELS = ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8'];

function TrendChart() {
  const max = Math.max(...WEEKLY_FPR, 0);
  const min = Math.min(...WEEKLY_FPR, 0);
  const range = max - min || 1;
  const w = 560;
  const h = 180;
  const pad = 24;
  const step = (w - pad * 2) / (WEEKLY_FPR.length - 1);
  const pts = WEEKLY_FPR.map((v, i) => {
    const x = pad + i * step;
    const y = pad + (1 - (v - min) / range) * (h - pad * 2);
    return [x, y] as const;
  });
  const path = pts.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
  const improving = WEEKLY_FPR[0] - WEEKLY_FPR[WEEKLY_FPR.length - 1] > 0;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-[#201b4b]">False-positive rate over time</h3>
        <span className={`text-xs font-bold ${improving ? 'text-emerald-600' : 'text-red-600'}`}>
          {improving ? '↓ improving' : '↑ worsening'}
        </span>
      </div>
      <svg viewBox={`0 0 ${w} ${h}`} className="mt-4 w-full" role="img" aria-label="False positive rate trend line chart">
        <line x1={pad} y1={pad} x2={w - pad} y2={pad} stroke="#e2e8f0" strokeDasharray="3 3" />
        <line x1={pad} y1={h / 2} x2={w - pad} y2={h / 2} stroke="#e2e8f0" strokeDasharray="3 3" />
        <line x1={pad} y1={h - pad} x2={w - pad} y2={h - pad} stroke="#e2e8f0" strokeDasharray="3 3" />
        <path d={path} fill="none" stroke="#32406f" strokeWidth="2.5" strokeLinecap="round" />
        {pts.map(([x, y], i) => (
          <circle key={WEEK_LABELS[i]} cx={x} cy={y} r="4" fill="#43cddd" stroke="#fff" strokeWidth="2" />
        ))}
        {pts.map(([x, y], i) => (
          <text key={`l-${WEEK_LABELS[i]}`} x={x} y={y - 10} textAnchor="middle" fontSize="11" fill="#64748b">
            {formatPercent(WEEKLY_FPR[i], 1)}
          </text>
        ))}
        {WEEK_LABELS.map((label, i) => {
          const x = pad + i * step;
          return (
            <text key={label} x={x} y={h - 6} textAnchor="middle" fontSize="10" fill="#94a3b8">
              {label}
            </text>
          );
        })}
      </svg>
    </div>
  );
}

const CARDS: { key: string; label: string; value: number; className: string }[] = [
  { key: 'total', label: 'Transactions reviewed', value: 0, className: 'bg-[#201b4b] text-white' },
  { key: 'fraud', label: 'Confirmed fraud', value: 0, className: 'bg-red-50 text-red-700' },
  { key: 'false', label: 'False alarms', value: 0, className: 'bg-amber-50 text-amber-800' },
  { key: 'legit', label: 'Customer confirmed legitimate', value: 0, className: 'bg-emerald-50 text-emerald-700' },
];

export function SystemPerformance() {
  const { data, isLoading, error } = useFeedbackStats();

  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#43cddd]">Analytics</p>
      <h1 className="mt-2 text-2xl font-bold tracking-tight text-[#201b4b]">System performance</h1>

      {isLoading && <p className="mt-8 text-slate-500">Loading stats…</p>}
      {error && <p className="mt-8 text-red-600">Could not load performance stats.</p>}
      {!data || error ? null : (
        <>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {CARDS.map((c) => {
              const value =
                c.key === 'total'
                  ? data.total_feedback
                  : c.key === 'fraud'
                    ? data.confirmed_fraud
                    : c.key === 'false'
                      ? data.false_alarm
                      : data.customer_confirmed_legitimate;
              return (
                <div key={c.key} className={`rounded-xl border border-slate-200 px-5 py-4 shadow-sm ${c.className}`}>
                  <p className={`text-xs ${c.key === 'total' ? 'text-white/75' : 'opacity-70'}`}>{c.label}</p>
                  <p className="mt-1 text-3xl font-semibold tabular-nums">{value}</p>
                </div>
              );
            })}
          </div>

          <div className="mt-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">False positive rate</p>
            <p className="mt-1 text-4xl font-bold tabular-nums text-[#201b4b]">
              {formatPercent(data.false_positive_rate, 1)}
            </p>
            <p className="mt-1 text-sm text-slate-500">
              {data.false_alarm} false alarms out of {data.total_feedback} total feedback.
            </p>
          </div>

          <div className="mt-5 overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="w-full min-w-[560px] text-left text-sm">
              <thead className="bg-slate-50 text-[11px] uppercase tracking-[0.14em] text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-semibold">Decision type</th>
                  <th className="px-5 py-3 font-semibold">Total reviewed</th>
                  <th className="px-5 py-3 font-semibold">Confirmed fraud</th>
                  <th className="px-5 py-3 font-semibold">False alarm</th>
                  <th className="px-5 py-3 font-semibold">Fraud rate</th>
                </tr>
              </thead>
              <tbody>
                {data.feedback_by_decision.map((row) => (
                  <tr key={row.decision} className="border-t border-slate-100">
                    <td className="px-5 py-3 font-semibold text-slate-800">{row.decision.replaceAll('_', ' ')}</td>
                    <td className="px-5 py-3 tabular-nums">{row.total_reviewed}</td>
                    <td className="px-5 py-3 tabular-nums">{row.confirmed_fraud}</td>
                    <td className="px-5 py-3 tabular-nums">{row.false_alarm}</td>
                    <td className="px-5 py-3 font-semibold tabular-nums text-[#201b4b]">{formatPercent(row.fraud_rate, 1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-5">
            <TrendChart />
          </div>
        </>
      )}
    </div>
  );
}