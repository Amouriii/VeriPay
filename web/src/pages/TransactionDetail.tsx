import { useParams } from 'react-router-dom';
import { useRiskScore } from '../api/transactions';
import { RiskScoreGauge } from '../components/RiskScoreGauge';

export function TransactionDetail() {
  const { id } = useParams<{ id: string }>();
  const { data } = useRiskScore(id ?? '');
  return (
    <div className="p-6 md:p-8">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-accent">Transaction</p>
      <h1 className="mt-2 text-2xl font-bold tracking-tight text-ink">Transaction {id}</h1>
      <div className="mt-6 max-w-md">
        {data && <RiskScoreGauge score={data} />}
      </div>
    </div>
  );
}
