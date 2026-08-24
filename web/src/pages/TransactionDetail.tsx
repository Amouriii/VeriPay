import { useParams } from 'react-router-dom';
import { useRiskScore } from '../api/transactions';
import { RiskScoreGauge } from '../components/RiskScoreGauge';

export function TransactionDetail() {
  const { id } = useParams<{ id: string }>();
  const { data } = useRiskScore(id ?? '');
  return (
    <div className="p-6">
      <h1 className="text-xl font-semibold mb-4">Transaction {id}</h1>
      {data && <RiskScoreGauge score={data} />}
    </div>
  );
}
