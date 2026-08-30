import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useExplain, useScore } from '../../api/analyst';
import { ALERTS } from '../../mocks/analystData';
import { ScoreBar, formatDate, formatMoney } from '../../components/analyst/ui';
import { FeatureTable, AnomalyContributors, ShapValues } from './FeatureBreakdown';
import { Timeline } from './Timeline';
import { FeedbackPanel } from './FeedbackPanel';

type Tab = 'breakdown' | 'timeline';

export function TxDetail() {
  const { id } = useParams<{ id: string }>();
  const txId = id ?? '';
  const { data: score, isLoading, error } = useScore(txId);
  const { data: explain } = useExplain(txId);
  const [tab, setTab] = useState<Tab>('breakdown');

  const alert = ALERTS.find((a) => a.transaction_id === txId);
  const currency = alert?.currency ?? 'USD';

  if (isLoading) {
    return <p className="py-16 text-center text-slate-500">Loading transaction…</p>;
  }
  if (error || !score) {
    return (
      <div className="py-16 text-center">
        <p className="text-slate-500">Could not load this transaction.</p>
        <Link to="/analyst" className="mt-3 inline-block text-sm font-semibold text-[#29265f] hover:text-[#43aebe]">
          ← Back to alert queue
        </Link>
      </div>
    );
  }

  const high = score.risk_level === 'HIGH';

  return (
    <div>
      <Link
        to="/analyst"
        className="inline-flex items-center gap-2 text-sm font-semibold text-[#29265f] transition hover:text-[#43aebe]"
      >
        ← Back to alert queue
      </Link>

      {/* Section A — Verdict banner */}
      <div
        className={`mt-4 rounded-xl border p-5 text-white shadow-sm ${high ? 'border-red-700 bg-red-600' : 'border-orange-600 bg-orange-500'}`}
      >
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-white/85">
          {explain?.case_report?.verdict?.split(' — ')[0] ?? score.decision} · {score.risk_level} risk
        </p>
        <p className="mt-2 text-lg font-medium leading-6">
          {explain?.case_report?.verdict ?? `Scored ${score.decision} with ${score.fraud_probability * 100}% fraud probability.`}
        </p>
      </div>

      {/* Transaction header */}
      <div className="mt-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#201b4b]">{score.transaction_id}</h1>
          <p className="mt-1 text-sm text-slate-500">
            {alert?.customer_name ?? `Customer #${score.cc_num}`}{' '}
            <Link to={`/analyst/customer/${score.cc_num}`} className="underline decoration-dotted underline-offset-2 hover:text-[#43aebe]">
              #{score.cc_num}
            </Link>
            {' · '}
            {alert?.merchant}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-right shadow-sm">
          <p className="text-xs text-slate-500">Amount</p>
          <p className="text-xl font-semibold text-[#201b4b]">
            {formatMoney(alert?.amount ?? 0, currency)}
          </p>
          <p className="text-xs text-slate-500">{formatDate(alert?.time ?? '')}</p>
        </div>
      </div>

      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <ScoreBar value={score.fraud_probability} label="Fraud probability" />
        <ScoreBar value={score.anomaly_score} label="Anomaly score" />
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        {/* Section B — Key evidence */}
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="font-semibold text-[#201b4b]">Key evidence</h2>
          <ul className="mt-3 space-y-3">
            {explain?.case_report?.evidence.map((e) => (
              <li key={e} className="flex gap-3 text-sm text-slate-700">
                <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-[#29265f] text-[10px] font-bold text-white">
                  {explain.case_report.evidence.indexOf(e) + 1}
                </span>
                <span>{e}</span>
              </li>
            ))}
          </ul>
        </section>

        <div className="space-y-5">
          {/* Section C — Pattern match + recommended action */}
          <section className="rounded-xl border border-[#43cddd]/70 bg-[#f0f9ff] p-5 shadow-sm">
            <h2 className="text-xs font-bold uppercase tracking-[0.16em] text-[#0b7f7a]">
              Pattern match
            </h2>
            <p className="mt-2 text-sm text-slate-700">
              {explain?.case_report?.pattern_match ?? 'No match pattern returned.'}
            </p>
            <h2 className="mt-4 text-xs font-bold uppercase tracking-[0.16em] text-[#0b7f7a]">
              Recommended action
            </h2>
            <p className="mt-2 text-sm font-medium text-slate-800">
              {explain?.case_report?.recommended_action ?? 'Review the transaction manually.'}
            </p>
          </section>

          {/* Section D — Verification status */}
          <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">
              Verification status
            </h2>
            <p className="mt-2 text-sm font-semibold text-[#201b4b]">{score.verification_action}</p>
          </section>
        </div>
      </div>

      {/* Screens 3 & 4 — tabs */}
      <section className="mt-6 rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="flex gap-1 border-b border-slate-100 px-4 pt-3">
          {([
            ['breakdown', 'Feature Breakdown'],
            ['timeline', 'Transaction Timeline'],
          ] as [Tab, string][]).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`-mb-px border-b-2 px-4 py-2 text-sm font-semibold transition ${
                tab === key
                  ? 'border-[#29265f] text-[#29265f]'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="p-5">
          {tab === 'breakdown' ? (
            <div className="space-y-8">
              <div>
                <h3 className="mb-3 text-xs font-bold uppercase tracking-[0.16em] text-slate-500">
                  Anomaly contributors
                </h3>
                <AnomalyContributors score={score} />
              </div>
              <div className="grid gap-6 lg:grid-cols-2">
                <div>
                  <h3 className="mb-3 text-xs font-bold uppercase tracking-[0.16em] text-slate-500">
                    XGBoost SHAP values
                  </h3>
                  <ShapValues score={score} />
                </div>
                <div>
                  <h3 className="mb-3 text-xs font-bold uppercase tracking-[0.16em] text-slate-500">
                    Anomaly score
                  </h3>
                  <p className="rounded-lg bg-slate-50 px-3 py-4 text-2xl font-semibold text-[#201b4b]">
                    {score.anomaly_score.toFixed(2)}
                    <span className="ml-1 text-sm text-slate-500">/ 1.00</span>
                  </p>
                  <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
                    <div className="h-full rounded-full bg-gradient-to-r from-emerald-500 via-orange-400 to-red-500" style={{ width: `${score.anomaly_score * 100}%` }} />
                  </div>
                </div>
              </div>
              <div>
                <h3 className="mb-3 text-xs font-bold uppercase tracking-[0.16em] text-slate-500">
                  Full feature table (all 16 features)
                </h3>
                <FeatureTable features={score.features} />
              </div>
            </div>
          ) : (
            <div className="grid gap-6 lg:grid-cols-[1fr_260px]">
              <Timeline txs={score.recent_transactions} currency={currency} />
              <aside className="rounded-xl border border-slate-100 bg-slate-50 p-4 text-sm text-slate-600">
                <h3 className="font-semibold text-[#201b4b]">Why this matters</h3>
                <p className="mt-2">
                  Bars grow as amounts escalate. This is the <em>sequence</em> the Transformer
                  model learns from — many small authorizations followed by one large debit is
                  the card-testing signature.
                </p>
              </aside>
            </div>
          )}
        </div>
      </section>

      {/* Screen 6 — feedback */}
      <FeedbackPanel
        transactionId={score.transaction_id}
        ccNum={score.cc_num}
        customerName={alert?.customer_name ?? `Customer #${score.cc_num}`}
        merchant={alert?.merchant ?? 'Unknown'}
        amount={alert?.amount ?? 0}
        currency={currency}
        decision={score.decision}
      />
    </div>
  );
}