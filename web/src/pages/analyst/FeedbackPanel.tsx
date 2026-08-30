import { useState } from 'react';
import { useSubmitFeedback } from '../../api/analyst';
import { FEEDBACK_HISTORY } from '../../mocks/analystData';
import type { AnalystDecision, Decision, FeedbackHistoryEntry } from '../../types/analyst';
import { DecisionBadge, formatDate, formatMoney } from '../../components/analyst/ui';

const OPTIONS: { value: AnalystDecision; label: string; className: string }[] = [
  {
    value: 'confirmed_fraud',
    label: 'Confirmed Fraud',
    className: 'bg-red-600 text-white hover:bg-red-700',
  },
  {
    value: 'false_alarm',
    label: 'False Alarm',
    className: 'bg-slate-200 text-slate-800 hover:bg-slate-300',
  },
  {
    value: 'customer_confirmed_legitimate',
    label: 'Customer Confirmed Legitimate',
    className: 'bg-emerald-600 text-white hover:bg-emerald-700',
  },
];

interface Props {
  transactionId: string;
  ccNum: number;
  customerName: string;
  merchant: string;
  amount: number;
  currency: string;
  decision: Decision;
}

export function FeedbackPanel({
  transactionId,
  ccNum,
  customerName,
  merchant,
  amount,
  currency,
  decision,
}: Props) {
  const mutation = useSubmitFeedback();
  const [selected, setSelected] = useState<AnalystDecision | null>(null);
  const [notes, setNotes] = useState('');
  const [history, setHistory] = useState<FeedbackHistoryEntry[]>(FEEDBACK_HISTORY);

  const submit = () => {
    if (!selected) return;
    mutation.mutate(
      { transaction_id: transactionId, analyst_decision: selected, analyst_id: 'Avalanche', notes: notes.trim() || undefined },
      {
        onSuccess: () => {
          setHistory((prev) => [
            {
              transaction_id: transactionId,
              merchant,
              amount,
              currency,
              time: new Date().toISOString(),
              decision,
              analyst_decision: selected,
              notes: notes.trim() || undefined,
            },
            ...prev,
          ]);
          setSelected(null);
          setNotes('');
        },
      },
    );
  };

  const errorStatus = (mutation.error as { status?: number } | null)?.status;

  return (
    <section className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-[#201b4b]">Record your verdict</h2>
      <p className="mt-1 text-sm text-slate-500">
        Logging feedback for {transactionId} ({customerName}, #{ccNum}) retrains the models.
      </p>

      <div className="mt-4 flex flex-wrap gap-2">
        {OPTIONS.map((o) => (
          <button
            key={o.value}
            onClick={() => setSelected(o.value)}
            className={`rounded-lg px-4 py-2 text-sm font-bold transition ${o.className} ${
              selected === o.value ? 'ring-2 ring-offset-2 ring-[#29265f]' : ''
            }`}
          >
            {o.label}
          </button>
        ))}
      </div>

      <textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder='Optional context — e.g. "Customer called and confirmed they are traveling."'
        className="mt-4 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-[#00a79d]"
        rows={2}
      />

      <div className="mt-3 flex flex-wrap items-center gap-3">
        <button
          onClick={submit}
          disabled={!selected || mutation.isPending}
          className="rounded-lg bg-[#29265f] px-5 py-2 text-sm font-bold text-white transition hover:bg-[#201b4b] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {mutation.isPending ? 'Submitting…' : 'Submit feedback'}
        </button>

        {mutation.isSuccess && (
          <span className="text-sm font-semibold text-emerald-600">✓ Feedback recorded.</span>
        )}
        {mutation.isError && (
          <span className="text-sm font-semibold text-red-600">
            {errorStatus === 409
              ? 'Feedback already submitted for this transaction.'
              : errorStatus === 422
                ? 'Invalid decision value.'
                : 'Could not submit feedback.'}
          </span>
        )}
      </div>

      {/* Feedback history for this customer */}
      <div className="mt-8 border-t border-slate-100 pt-5">
        <h3 className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">
          Past feedback for this customer
        </h3>
        <ul className="mt-3 space-y-2">
          {history.map((h) => (
            <li
              key={h.transaction_id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-sm"
            >
              <div>
                <p className="font-medium text-slate-800">
                  {h.merchant} · {formatMoney(h.amount, h.currency)}
                </p>
                <p className="text-xs text-slate-500">
                  {h.transaction_id} · {formatDate(h.time)}
                  {h.notes ? ` · “${h.notes}”` : ''}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <DecisionBadge decision={h.decision} />
                <span className="rounded-full bg-[#201b4b] px-2.5 py-1 text-xs font-bold text-white">
                  {h.analyst_decision.replaceAll('_', ' ')}
                </span>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}