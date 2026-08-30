import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAlerts } from '../../api/analyst';
import type { Decision, RiskLevel } from '../../types/analyst';
import { DecisionBadge, RiskPill, formatDate, formatMoney, formatPercent } from '../../components/analyst/ui';

interface DecisionFilter {
  key: 'ALL' | 'BLOCK' | 'REVIEW';
  label: string;
}
const DECISION_FILTERS: DecisionFilter[] = [
  { key: 'ALL', label: 'All decisions' },
  { key: 'BLOCK', label: 'BLOCK only' },
  { key: 'REVIEW', label: 'REVIEW only' },
];

const RISK_FILTERS: { key: 'ALL' | RiskLevel; label: string }[] = [
  { key: 'ALL', label: 'All risk' },
  { key: 'HIGH', label: 'HIGH' },
  { key: 'MODERATE', label: 'MODERATE' },
];

const isReview = (d: Decision) => d === 'REVIEW_STEALTH' || d === 'REVIEW_UNUSUAL';

export function AlertQueue() {
  const { data, isLoading, error } = useAlerts();
  const [decision, setDecision] = useState<DecisionFilter['key']>('ALL');
  const [risk, setRisk] = useState<'ALL' | RiskLevel>('ALL');

  const filtered = useMemo(() => {
    return (data ?? []).filter((a) => {
      const okDecision = decision === 'ALL' || (decision === 'BLOCK' ? a.decision === 'BLOCK' : isReview(a.decision));
      const okRisk = risk === 'ALL' || a.risk_level === risk;
      return okDecision && okRisk;
    });
  }, [data, decision, risk]);

  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#43cddd]">Alert Queue</p>
      <h1 className="mt-2 text-2xl font-bold tracking-tight text-[#201b4b]">Flagged transactions</h1>
      <p className="mt-1 text-sm text-slate-500">
        Non-PASS scoring results, most suspicious first. Passed transactions do not appear here.
      </p>

      {/* Filters */}
      <div className="mt-6 flex flex-wrap items-center gap-3">
        <div className="flex overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
          {DECISION_FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setDecision(f.key)}
              className={`px-3 py-2 text-xs font-bold transition ${
                decision === f.key
                  ? 'bg-[#29265f] text-white'
                  : 'text-slate-600 hover:bg-slate-50'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
        <div className="flex overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
          {RISK_FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setRisk(f.key)}
              className={`px-3 py-2 text-xs font-bold transition ${
                risk === f.key ? 'bg-[#29265f] text-white' : 'text-slate-600 hover:bg-slate-50'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
        <span className="ml-auto text-sm text-slate-500">
          {filtered.length} flagged
        </span>
      </div>

      {/* Table */}
      <div className="mt-4 overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="bg-slate-50 text-[11px] uppercase tracking-[0.14em] text-slate-500">
            <tr>
              <th className="px-5 py-3 font-semibold">Transaction</th>
              <th className="px-5 py-3 font-semibold">Customer</th>
              <th className="px-5 py-3 font-semibold">Decision</th>
              <th className="px-5 py-3 font-semibold">Risk</th>
              <th className="px-5 py-3 font-semibold">Score</th>
              <th className="px-5 py-3 font-semibold">Time</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((a) => (
              <tr key={a.transaction_id} className="border-t border-slate-100 transition-colors hover:bg-[#f0f7ff]">
                <td className="px-5 py-4">
                  <Link
                    to={`/analyst/tx/${a.transaction_id}`}
                    className="font-semibold text-[#29265f] hover:text-[#43aebe]"
                  >
                    {a.transaction_id}
                  </Link>
                  <p className="mt-0.5 text-xs text-slate-500">
                    {formatMoney(a.amount, a.currency)} · {a.merchant}
                  </p>
                </td>
                <td className="px-5 py-4">
                  <Link
                    to={`/analyst/customer/${a.cc_num}`}
                    className="text-slate-700 underline decoration-dotted decoration-slate-300 underline-offset-2 hover:text-[#43aebe]"
                  >
                    {a.customer_name}
                  </Link>
                  <p className="mt-0.5 text-xs text-slate-500">{a.cc_num}</p>
                </td>
                <td className="px-5 py-4"><DecisionBadge decision={a.decision} /></td>
                <td className="px-5 py-4"><RiskPill level={a.risk_level} /></td>
                <td className="px-5 py-4">
                  <p className="font-semibold tabular-nums text-slate-800">
                    {formatPercent(a.fraud_probability, 0)}
                    <span className="ml-2 text-xs font-medium text-slate-500">fraud</span>
                  </p>
                  <p className="text-xs tabular-nums text-slate-500">
                    anomaly {formatPercent(a.anomaly_score, 0)}
                  </p>
                </td>
                <td className="px-5 py-4 text-xs tabular-nums text-slate-600">
                  {formatDate(a.time)}
                </td>
              </tr>
            ))}
            {!isLoading && filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="px-5 py-12 text-center text-sm text-slate-500">
                  No flagged transactions match these filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
        {isLoading && <p className="px-5 py-10 text-center text-sm text-slate-500">Loading alerts…</p>}
        {error && <p className="px-5 py-10 text-center text-sm text-red-600">Could not load alerts.</p>}
      </div>
    </div>
  );
}