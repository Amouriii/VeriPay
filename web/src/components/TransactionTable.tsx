import type { TransactionDto } from '../types';

export function TransactionTable({ items }: { items: TransactionDto[] }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-left border-b">
          <th>Tx ID</th><th>User</th><th>Amount</th><th>Merchant</th>
        </tr>
      </thead>
      <tbody>
        {items.map((t) => (
          <tr key={t.transactionId} className="border-b hover:bg-slate-50">
            <td>{t.transactionId}</td><td>{t.userId}</td>
            <td>{t.amountMinor}</td><td>{t.merchantId}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
