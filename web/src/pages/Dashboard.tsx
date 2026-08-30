import { useTransactions } from '../api/transactions';
import { TransactionTable } from '../components/TransactionTable';

export function Dashboard() {
  const { data } = useTransactions();
  return (
    <div className="p-6">
      <h1 className="text-xl font-semibold mb-4">VeriPay Analyst Dashboard</h1>
      <TransactionTable items={data ?? []} />
    </div>
  );
}
