import { useState } from 'react';
import { useFeedbackStats, useHealth, useRetrain } from '../../api/analyst';
import { formatPercent } from '../../components/analyst/ui';

export function ModelInfo() {
  const { data: health } = useHealth();
  const { data: stats } = useFeedbackStats();
  const retrain = useRetrain();
  const [confirming, setConfirming] = useState(false);

  const openConfirm = () => setConfirming(true);
  const runRetrain = () => {
    setConfirming(false);
    retrain.mutate();
  };

  const models = [
    { name: 'ECOD', type: 'unsupervised', version: health?.model_versions?.ecod ?? '—' },
    { name: 'XGBoost', type: 'supervised', version: health?.model_versions?.xgboost ?? '—' },
    { name: 'Transformer', type: 'sequence', version: health?.model_versions?.transformer ?? '—' },
  ];

  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#43cddd]">System</p>
      <h1 className="mt-2 text-2xl font-bold tracking-tight text-[#201b4b]">Model information</h1>

      <div className="mt-6 grid gap-5 md:grid-cols-3">
        {models.map((m) => (
          <div key={m.name} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-bold text-[#201b4b]">{m.name}</p>
            <p className="text-xs uppercase tracking-[0.14em] text-slate-500">{m.type}</p>
            <p className="mt-2 text-xs text-slate-500">Version</p>
            <p className="font-semibold tabular-nums text-[#201b4b]">{m.version}</p>
          </div>
        ))}
      </div>

      <div className="mt-5 grid gap-5 md:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">Ensemble weighting</h2>
          <div className="mt-3 flex h-3 w-full overflow-hidden rounded-full bg-slate-100">
            <div className="h-full bg-[#32406f]" style={{ width: '30%' }} />
            <div className="h-full bg-[#43cddd]" style={{ width: '70%' }} />
          </div>
          <div className="mt-3 flex justify-between text-sm">
            <span className="font-semibold text-slate-700">30% XGBoost</span>
            <span className="font-semibold text-slate-700">70% Transformer</span>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">Training</h2>
          <dl className="mt-3 space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-slate-500">Last trained</dt>
              <dd className="font-semibold text-[#201b4b]">2026-08-28</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Total feedback collected</dt>
              <dd className="font-semibold tabular-nums text-[#201b4b]">{stats?.total_feedback ?? '—'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Status</dt>
              <dd className="font-semibold text-[#201b4b]">{health?.status ?? 'unknown'}</dd>
            </div>
          </dl>
        </div>
      </div>

      <div className="mt-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-sm font-bold text-[#201b4b]">Retrain models</h2>
        <p className="mt-1 text-sm text-slate-500">
          Re-trains all models using analyst feedback. Held-out metrics must clear the current
          champion before the new version is promoted.
        </p>

        <button
          onClick={openConfirm}
          disabled={retrain.isPending}
          className="mt-4 inline-flex items-center gap-2 rounded-lg bg-[#29265f] px-5 py-2 text-sm font-bold text-white transition hover:bg-[#201b4b] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {retrain.isPending ? (
            <>
              <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
              Retraining…
            </>
          ) : (
            'Retrain Models'
          )}
        </button>

        {retrain.isSuccess && retrain.data && (
          <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 p-4">
            <p className="font-semibold text-emerald-800">
              ✓ {retrain.data.message ?? 'Retraining complete.'}
            </p>
            <dl className="mt-3 grid gap-3 sm:grid-cols-3">
              <Metric label="ROC-AUC" value={retrain.data.metrics.roc_auc} />
              <Metric label="PR-AUC" value={retrain.data.metrics.pr_auc} />
              <Metric label="False positive rate" value={retrain.data.metrics.false_positive_rate} />
            </dl>
            <p className="mt-3 text-xs text-emerald-700">
              New version: machine-28 · {retrain.data.new_version}
            </p>
          </div>
        )}
        {retrain.isError && (
          <p className="mt-3 text-sm font-semibold text-red-600">Retraining failed. Please try again.</p>
        )}
      </div>

      {/* Confirmation dialog */}
      {confirming && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/40 px-4">
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
            <h3 className="text-lg font-bold text-[#201b4b]">Retrain all models?</h3>
            <p className="mt-2 text-sm text-slate-600">
              This will retrain all models using analyst feedback. This may take several minutes.
              Continue?
            </p>
            <div className="mt-5 flex justify-end gap-2">
              <button
                onClick={() => setConfirming(false)}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={runRetrain}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-bold text-white hover:bg-red-700"
              >
                Retrain
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg bg-white px-3 py-2">
      <p className="text-xs text-emerald-700">{label}</p>
      <p className="text-lg font-semibold tabular-nums text-emerald-800">
        {label === 'False positive rate' ? formatPercent(value, 1) : value.toFixed(4)}
      </p>
    </div>
  );
}