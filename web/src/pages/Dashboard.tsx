import { useTransactions } from '../api/transactions';
import { TransactionTable } from '../components/TransactionTable';

export function Dashboard() {
  const { data } = useTransactions();
  return (
    <div className="p-6 md:p-8">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-accent">Analyst workspace</p>
      <h1 className="mt-2 text-2xl font-bold tracking-tight text-ink">VeriPay Analyst Dashboard</h1>
      <div className="mt-6">
        <TransactionTable items={data ?? []} />
      </div>
    </div>
  );
}
