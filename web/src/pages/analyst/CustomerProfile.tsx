import { Link, useParams } from 'react-router-dom';
import { useCustomerProfile } from '../../api/analyst';
import type { Baseline } from '../../types/analyst';

function BaselineCard({ title, baseline }: { title: string; baseline: Baseline }) {
  const rows: [string, string | number][] = [
    ['Median amount', baseline.median_amount],
    ['Typical hours', baseline.typical_hours],
    ['Location', baseline.home_location],
    ['Distinct merchants', baseline.distinct_merchants],
    ['Daily transaction count', baseline.daily_txn_count],
  ];
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">{title}</h2>
      <dl className="mt-4 space-y-4">
        {rows.map(([label, value]) => (
          <div key={label} className="flex items-center justify-between gap-3">
            <dt className="text-sm text-slate-500">{label}</dt>
            <dd className="text-sm font-semibold text-[#201b4b]">{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

export function CustomerProfile() {
  const { ccNum } = useParams<{ ccNum: string }>();
  const cc = Number(ccNum);
  const { data, isLoading, error } = useCustomerProfile(Number.isFinite(cc) ? cc : undefined);

  if (isLoading || ccNum === undefined) {
    return <p className="py-16 text-center text-slate-500">Loading profile…</p>;
  }
  if (error || !data) {
    return (
      <div className="py-16 text-center">
        <p className="text-slate-500">Could not load this customer.</p>
        <Link to="/analyst" className="mt-3 inline-block text-sm font-semibold text-[#29265f] hover:text-[#43aebe]">
          ← Back to alert queue
        </Link>
      </div>
    );
  }

  const driftBanner =
    data.drift_detected?.severity === 'red'
      ? 'border-red-300 bg-red-50 text-red-800'
      : 'border-amber-300 bg-amber-50 text-amber-800';

  const trustTone =
    data.trust_status.level === 'alert'
      ? 'border-red-200 bg-red-50 text-red-700'
      : data.trust_status.level === 'boosted'
        ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
        : 'border-slate-200 bg-slate-50 text-slate-700';

  return (
    <div>
      <Link
        to="/analyst"
        className="inline-flex items-center gap-2 text-sm font-semibold text-[#29265f] transition hover:text-[#43aebe]"
      >
        ← Back to alert queue
      </Link>

      <div className="mt-4">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#43cddd]">Customer Profile</p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-[#201b4b]">#{data.cc_num}</h1>
      </div>

      <div className="mt-6 grid gap-5 md:grid-cols-2">
        <BaselineCard title="Long-term baseline" baseline={data.long_term_baseline} />
        <BaselineCard title="Last 30 days" baseline={data.recent_behavior} />
      </div>

      {/* Drift indicator */}
      {data.drift_detected && (
        <div className={`mt-5 rounded-xl border px-5 py-4 text-sm ${driftBanner}`}>
          <p className="font-bold">Behavioral drift detected</p>
          <p className="mt-1">{data.drift_detected.message}</p>
        </div>
      )}
      {!data.drift_detected && (
        <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 px-5 py-4 text-sm text-slate-600">
          No drift detected — recent behavior is consistent with the long-term baseline.
        </div>
      )}

      {/* Trust status */}
      <div className={`mt-4 rounded-xl border px-5 py-4 text-sm ${trustTone}`}>
        <p className="font-bold">{data.trust_status.message}</p>
      </div>
    </div>
  );
}