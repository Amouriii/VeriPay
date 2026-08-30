// FI Ops Console page — institutional fraud operations (Expansion §1 Dev5).
import { Link } from 'react-router-dom';
import { useTransactions, useRiskScore } from '../api/transactions';
import type { RiskScoreDto, TransactionDto } from '../types';

function RiskPill({ risk }: { risk: RiskScoreDto }) {
  const style = risk.band === 'BLOCK'
    ? 'bg-red-50 text-red-700 ring-red-600/20'
    : risk.band === 'VERIFY'
      ? 'bg-amber-50 text-amber-700 ring-amber-600/20'
      : 'bg-emerald-50 text-emerald-700 ring-emerald-600/20';
  return <span className={`inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-xs font-bold ring-1 ring-inset ${style}`}><span>{risk.unifiedScore}</span><span>{risk.band}</span></span>;
}

function RiskRow({ transaction }: { transaction: TransactionDto }) {
  const { data: risk, isLoading } = useRiskScore(transaction.transactionId);
  const amount = new Intl.NumberFormat(undefined, { style: 'currency', currency: transaction.currency }).format(transaction.amountMinor / 100);
  return (
    <tr className="border-b border-slate-200/80 last:border-0 hover:bg-slate-50">
      <td className="px-5 py-4"><Link className="font-semibold text-slate-900 hover:text-teal-700" to={`/tx/${transaction.transactionId}`}>{transaction.transactionId}</Link><div className="mt-1 text-xs text-slate-500">Customer {transaction.userId}</div></td>
      <td className="px-5 py-4 text-slate-600">{transaction.merchantId || 'Unknown merchant'}</td>
      <td className="px-5 py-4 font-medium text-slate-900">{amount}</td>
      <td className="px-5 py-4">{isLoading || !risk ? <span className="text-xs text-slate-400">Evaluating</span> : <RiskPill risk={risk} />}</td>
      <td className="px-5 py-4 text-right"><Link className="text-sm font-semibold text-teal-700 hover:text-teal-900" to={`/tx/${transaction.transactionId}`}>Review <span aria-hidden="true">-&gt;</span></Link></td>
    </tr>
  );
}

function Metric({ label, value, detail, accent = 'slate' }: { label: string; value: string; detail: string; accent?: 'slate' | 'amber' | 'teal' }) {
  const border = accent === 'amber' ? 'border-amber-300' : accent === 'teal' ? 'border-teal-300' : 'border-slate-200';
  return <div className={`rounded-xl border ${border} bg-white p-5 shadow-sm`}><p className="text-sm font-medium text-slate-500">{label}</p><p className="mt-3 text-3xl font-semibold tracking-tight">{value}</p><p className="mt-2 text-xs text-slate-500">{detail}</p></div>;
}

function Module({ label, detail }: { label: string; detail: string }) {
  return <div className="border-l-2 border-slate-300 px-4 py-2"><p className="font-semibold text-slate-800">{label}</p><p className="mt-1 text-sm text-slate-500">{detail}</p><span className="mt-3 inline-block text-xs font-bold uppercase tracking-[0.12em] text-slate-400">Backend integration pending</span></div>;
}

export function FiOpsConsole() {
  const { data: transactions, isLoading, isError } = useTransactions();
  const items = transactions ?? [];
  const totalVolume = items.reduce((sum, transaction) => sum + transaction.amountMinor, 0);
  return (
    <main className="min-h-screen bg-[#f4f7f6] text-slate-900">
      <header className="border-b border-slate-200 bg-[#102a2a] text-white"><div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5"><div><p className="text-xs font-bold uppercase tracking-[0.22em] text-teal-300">VeriPay / FI operations</p><h1 className="mt-2 text-2xl font-semibold tracking-tight">Institutional risk desk</h1></div><div className="hidden items-center gap-6 text-sm text-teal-100 md:flex"><span>Portfolio overview</span><span className="text-teal-300">Bank console</span><span className="rounded-full border border-teal-700 px-3 py-1.5">Operations online</span></div></div></header>
      <div className="mx-auto max-w-7xl px-6 py-8">
        <div className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-end"><div><p className="text-sm font-semibold text-teal-700">Today&apos;s control room</p><h2 className="mt-1 text-3xl font-semibold tracking-tight">Portfolio risk overview</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">Monitor authorization exposure and route high-risk activity to review.</p></div><div className="text-left text-sm text-slate-500 md:text-right"><p className="font-semibold text-slate-700">Live transaction feed</p><p>Risk scores are evaluated per transaction</p></div></div>
        <section aria-label="Portfolio metrics" className="grid gap-4 md:grid-cols-3"><Metric label="Transactions observed" value={isLoading ? '...' : String(items.length)} detail="Current API window" /><Metric label="Review queue" value={isLoading ? '...' : String(items.length)} detail="Requires analyst attention" accent="amber" /><Metric label="Observed volume" value={isLoading ? '...' : formatCompactAmount(totalVolume)} detail="Across returned currencies" accent="teal" /></section>
        <section className="mt-8 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm" aria-labelledby="queue-title"><div className="flex flex-col gap-3 border-b border-slate-200 px-5 py-5 md:flex-row md:items-center md:justify-between"><div><h3 id="queue-title" className="text-lg font-semibold">Authorization review queue</h3><p className="mt-1 text-sm text-slate-500">Open a transaction to inspect contributing risk signals.</p></div><span className="w-fit rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">{items.length} records</span></div>{isLoading && <p className="px-5 py-10 text-sm text-slate-500">Loading portfolio activity...</p>}{isError && <p className="px-5 py-10 text-sm text-red-700">Portfolio activity could not be loaded. Check the API connection and try again.</p>}{!isLoading && !isError && items.length === 0 && <p className="px-5 py-10 text-sm text-slate-500">No transactions are in the current review window.</p>}{!isLoading && !isError && items.length > 0 && <div className="overflow-x-auto"><table className="min-w-[680px] w-full text-left text-sm"><thead className="bg-slate-50 text-xs uppercase tracking-[0.12em] text-slate-500"><tr><th className="px-5 py-3 font-bold">Transaction</th><th className="px-5 py-3 font-bold">Merchant</th><th className="px-5 py-3 font-bold">Amount</th><th className="px-5 py-3 font-bold">Risk</th><th className="px-5 py-3 text-right font-bold">Action</th></tr></thead><tbody>{items.map((transaction) => <RiskRow key={transaction.transactionId} transaction={transaction} />)}</tbody></table></div>}</section>
        <section className="mt-8 grid gap-4 md:grid-cols-3" aria-label="Bank operations modules"><Module label="Settlement monitoring" detail="Issuer batches and network settlement" /><Module label="Dispute lifecycle" detail="Chargebacks, evidence, and resolution" /><Module label="Regulatory audit" detail="Immutable actions and access history" /></section>
      </div>
    </main>
  );
}

function formatCompactAmount(amountMinor: number) {
  return new Intl.NumberFormat(undefined, { notation: 'compact', maximumFractionDigits: 1 }).format(amountMinor / 100);
}
