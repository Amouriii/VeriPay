import { useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { bankTransactions, customers } from '../bankData';

const reasonItems = [
  ['New device', 'The customer normally uses a trusted device.'],
  ['Unusual location', "The location differs from the customer's recent activity."],
  ['Unusual amount', "The purchase is above the customer's usual range."],
  ['Unusual time', "The transaction is outside the customer's normal activity window."],
];

export function TransactionDetail() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();

  const transaction =
    bankTransactions.find((item) => item.id === id) ?? bankTransactions[0];

  /*
   * If this transaction was opened from a customer profile,
   * remember that customer so the back button returns there.
   */
  const fromCustomerId = (
    location.state as { fromCustomerId?: string } | null
  )?.fromCustomerId;

  const customerId =
    fromCustomerId ??
    `CUS-${transaction.customer.replace('Customer #', '')}`;

  const customer = customers.find((item) => item.id === customerId);

  const critical = transaction.level === 'CRITICAL';
  const high = transaction.level === 'HIGH';
  type VerificationMethod = 'push' | 'sms' | 'email' | 'biometric';
  type VerificationState = 'idle' | 'method' | 'processing' | 'sent' | 'passed' | 'failed';
  const [verificationState, setVerificationState] = useState<VerificationState>('idle');
  const [verificationMethod, setVerificationMethod] = useState<VerificationMethod | null>(null);
  const [code, setCode] = useState('');
  const [message, setMessage] = useState('');

  const initiateVerification = (method: VerificationMethod) => {
    setVerificationMethod(method);
    setVerificationState('processing');
    setMessage('');
    window.setTimeout(() => setVerificationState('sent'), 450);
  };

  const completeVerification = () => {
    if ((verificationMethod === 'sms' || verificationMethod === 'email') && code !== '246810') {
      setVerificationState('failed');
      setMessage('Code rejected. Demo code: 246810.');
      return;
    }
    setVerificationState('passed');
    setMessage('Customer verification passed. Transaction can proceed.');
  };

  const levelClass = critical
    ? 'bg-red-600 text-white'
    : high
      ? 'bg-orange-100 text-orange-800'
      : transaction.level === 'MEDIUM'
        ? 'bg-amber-100 text-amber-800'
        : 'bg-emerald-100 text-emerald-800';

  const amount = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: transaction.currency,
  }).format(transaction.amount);

  return (
    <main className="mx-auto max-w-6xl px-6 py-8">

      {/* BACK BUTTON */}
      {fromCustomerId && customer ? (
        <Link
          to={`/bank/customers/${customer.id}`}
          className="inline-flex items-center gap-2 text-sm font-semibold text-[#29265f] transition hover:text-[#43aebe]"
        >
          ← Back to {customer.name}
        </Link>
      ) : (
        <Link
          to="/bank/transactions"
          className="inline-flex items-center gap-2 text-sm font-semibold text-[#29265f] transition hover:text-[#43aebe]"
        >
          ← Back to transactions
        </Link>
      )}

      {/* HEADER */}
      <header className="mt-6 flex flex-col justify-between gap-4 border-b border-[#43cddd]/50 pb-6 md:flex-row md:items-start">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#29265f]">
            Transaction review
          </p>

          <h1 className="mt-2 text-3xl font-semibold text-[#29265f]">
            {transaction.id}
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            {transaction.merchant} · {transaction.customer}
          </p>

          <Link
            to={`/bank/customers/${customerId}`}
            className="mt-2 inline-block text-sm font-bold text-[#29265f] hover:text-[#43aebe]"
          >
            View customer normal behavior →
          </Link>
        </div>

        <span
          className={`rounded-full px-3 py-1.5 text-xs font-bold ${levelClass}`}
        >
          {transaction.status.replaceAll('_', ' ')}
        </span>
      </header>

      {/* TRANSACTION SUMMARY */}
      <section className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-end justify-between">
          <div>
            <p className="text-sm text-slate-500">
              Transaction amount
            </p>

            <p className="mt-2 text-4xl font-semibold tracking-tight text-[#29265f]">
              {amount}
            </p>
          </div>

          <div className="text-right">
            <p className="text-xs text-slate-500">
              Risk score
            </p>

            <p
              className={`mt-1 text-3xl font-semibold ${
                critical
                  ? 'text-red-600'
                  : high
                    ? 'text-orange-600'
                    : transaction.level === 'MEDIUM'
                      ? 'text-amber-600'
                      : 'text-[#007064]'
              }`}
            >
              {transaction.score}
              <span className="text-base text-slate-400">
                /100
              </span>
            </p>

            <p className="mt-1 text-xs font-bold text-slate-500">
              {transaction.level} risk
            </p>
          </div>
        </div>

        <div className="mt-8 grid gap-5 border-t border-slate-200 pt-6 sm:grid-cols-2 lg:grid-cols-3">
          {[
            ['Merchant', transaction.merchant],
            ['Customer', transaction.customer],
            ['Type', transaction.type],
            ['Channel', transaction.channel.replaceAll('_', ' ')],
            ['Location', transaction.location],
            ['Time', `31 Aug, ${transaction.time}`],
          ].map(([label, value]) => (
            <div key={label}>
              <p className="text-xs text-slate-500">
                {label}
              </p>

              <p className="mt-1 font-medium text-[#29265f]">
                {value}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* RISK REASONS */}
      <section className="mt-6 rounded-xl border border-[#43cddd]/70 bg-white p-6 shadow-sm">
        <div className="flex items-start gap-3">
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[#43cddd]/25 text-lg font-bold text-[#29265f]">
            ?
          </span>

          <div>
            <h2 className="text-xl font-semibold text-[#29265f]">
              Risk reasons
            </h2>

            <p className="mt-1 text-sm text-slate-600">
              Specific differences from the customer&apos;s normal behavior.
            </p>
          </div>
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-2">
          {reasonItems.map(([title, detail], index) => (
            <article
              key={title}
              className={`rounded-lg border-l-4 p-4 ${
                critical && index < 2
                  ? 'border-red-600 bg-red-50'
                  : high && index < 3
                    ? 'border-orange-400 bg-orange-50'
                    : 'border-[#43cddd] bg-[#f7fbff]'
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <h3 className="font-semibold text-[#29265f]">
                  {title}
                </h3>

                <span
                  className={`text-xs font-bold ${
                    critical && index < 2
                      ? 'text-red-700'
                      : high && index < 3
                        ? 'text-orange-800'
                        : 'text-[#2e2c83]'
                  }`}
                >
                  {critical && index < 2
                    ? 'Critical'
                    : high && index < 3
                      ? 'High impact'
                      : 'Context'}
                </span>
              </div>

              <p className="mt-2 text-sm leading-5 text-slate-600">
                {detail}
              </p>
            </article>
          ))}
        </div>
      </section>

      {/* VERIFICATION WORKFLOW */}
      {(transaction.decision === 'VERIFY' || transaction.verification !== 'NOT_REQUIRED') && (
        <section className="mt-6 rounded-xl border border-[#fac180] bg-white p-6 shadow-sm">
          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
            <div><p className="text-xs font-bold uppercase tracking-[0.18em] text-[#c56a00]">Verification workflow</p><h2 className="mt-2 text-xl font-semibold text-[#29265f]">Request trusted customer confirmation</h2><p className="mt-1 text-sm text-slate-600">Choose a method and track the request without exposing sensitive customer data.</p></div>
            <StatusBadge value={verificationState === 'passed' ? 'PASSED' : verificationState === 'failed' ? 'FAILED' : verificationState === 'sent' ? 'PENDING' : transaction.verification} />
          </div>
          {verificationState === 'idle' && <div className="mt-5 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">{([['push', 'Push notification'], ['sms', 'SMS code'], ['email', 'Email confirmation'], ['biometric', 'Biometric approval']] as [VerificationMethod, string][]).map(([method, label]) => <button key={method} type="button" onClick={() => initiateVerification(method)} className="rounded-lg border border-slate-200 px-3 py-3 text-left text-sm font-semibold text-[#29265f] transition hover:border-[#43cddd] hover:bg-[#e8f9fc]"><span className="block">{label}</span><span className="mt-1 block text-xs font-normal text-slate-500">Start request →</span></button>)}</div>}
          {verificationState === 'processing' && <p className="mt-5 rounded-lg bg-amber-50 p-4 text-sm font-semibold text-amber-800">Creating a secure verification request…</p>}
          {verificationState === 'sent' && verificationMethod && <div className="mt-5 rounded-lg bg-[#f7fbff] p-4"><p className="text-sm font-semibold text-[#29265f]">{verificationMethod === 'push' ? 'Push request sent to the trusted device.' : verificationMethod === 'email' ? 'Confirmation link sent to the masked email address.' : verificationMethod === 'sms' ? 'One-time code sent to the masked phone number.' : 'Biometric approval is ready on the trusted device.'}</p>{(verificationMethod === 'sms' || verificationMethod === 'email') && <input value={code} onChange={(event) => setCode(event.target.value)} maxLength={6} inputMode="numeric" placeholder="Enter 246810" className="mt-3 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm tracking-[0.3em] outline-none focus:border-[#43cddd]" />}<div className="mt-3 flex flex-wrap gap-2"><button type="button" onClick={completeVerification} className="rounded-lg bg-[#29265f] px-3 py-2 text-xs font-bold text-white">{verificationMethod === 'push' || verificationMethod === 'biometric' ? 'Mark customer verified' : 'Confirm code'}</button><button type="button" onClick={() => setVerificationState('idle')} className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600">Choose another method</button></div></div>}
          {verificationState === 'failed' && <div className="mt-5 rounded-lg bg-red-50 p-4 text-sm font-semibold text-red-700">{message}<button type="button" onClick={() => setVerificationState('sent')} className="ml-3 underline">Try again</button></div>}
          {verificationState === 'passed' && <div className="mt-5 rounded-lg bg-emerald-50 p-4 text-sm font-semibold text-emerald-700">{message}</div>}
        </section>
      )}

      {/* RECOMMENDATIONS */}
      <section className="mt-5 rounded-xl bg-[#29265f] p-5 text-white">
        <div className="flex items-center gap-3">
          <span className="grid h-8 w-8 place-items-center rounded-full bg-[#43cddd] font-bold text-[#29265f]">
            →
          </span>

          <div>
            <h2 className="text-lg font-semibold">
              Recommendations
            </h2>

            <p className="text-sm text-[#e7f5ff]">
              Three practical checks for this review.
            </p>
          </div>
        </div>

        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <Recommendation
            title="Check customer baseline"
            detail="Compare this activity with the linked customer profile."
          />

          <Recommendation
            title={
              critical
                ? 'Keep the block'
                : 'Keep verification active'
            }
            detail="Wait for trusted confirmation before approving the transaction."
          />

          <Recommendation
            title="Record the outcome"
            detail="Save the final decision and reason in the audit log."
          />
        </div>
      </section>

    </main>
  );
}

function StatusBadge({ value }: { value: string }) {
  const styles = value === 'PASSED' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : value === 'FAILED' ? 'bg-red-50 text-red-700 border-red-200' : 'bg-amber-50 text-amber-700 border-amber-200';
  return <span className={`inline-flex rounded-full border px-3 py-1.5 text-[10px] font-extrabold uppercase tracking-wide ${styles}`}>{value.replaceAll('_', ' ')}</span>;
}

function Recommendation({
  title,
  detail,
}: {
  title: string;
  detail: string;
}) {
  return (
    <div className="rounded-lg border border-white/15 bg-white/10 p-4">
      <p className="font-semibold text-[#fffed0]">
        {title}
      </p>

      <p className="mt-2 text-sm leading-5 text-[#e7f5ff]">
        {detail}
      </p>
    </div>
  );
}