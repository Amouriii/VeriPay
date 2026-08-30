import type { TransactionDto } from '../types';

export function TransactionTable({ items }: { items: TransactionDto[] }) {
  return (
    <div className="glass-panel overflow-x-auto rounded-2xl">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead className="bg-white/40 text-[11px] uppercase tracking-[0.14em] text-ink-subtle dark:bg-white/[0.04]">
          <tr>
            <th className="px-5 py-3 font-semibold">Tx ID</th><th className="px-5 py-3 font-semibold">User</th><th className="px-5 py-3 font-semibold">Amount</th><th className="px-5 py-3 font-semibold">Merchant</th>
          </tr>
        </thead>
        <tbody>
          {items.map((t) => (
            <tr key={t.transactionId} className="border-t border-separator transition-colors hover:bg-white/50 dark:hover:bg-white/[0.04]">
              <td className="px-5 py-4 font-semibold text-ink">{t.transactionId}</td>
              <td className="px-5 py-4 text-ink-muted">{t.userId}</td>
              <td className="px-5 py-4 font-semibold tabular-nums text-ink">{new Intl.NumberFormat(undefined, { style: 'currency', currency: t.currency }).format(t.amountMinor / 100)}</td>
              <td className="px-5 py-4 text-ink-muted">{t.merchantId || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {items.length === 0 && <p className="px-5 py-10 text-center text-sm text-ink-muted">No transactions in the current window.</p>}
    </div>
  );
}
