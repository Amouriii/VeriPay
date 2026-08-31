import { useState } from 'react';
import { Link } from 'react-router-dom';
import { analystPost } from '../api/client';
import type { ScoreResponse } from '../types/analyst';

const steps = [
  {
    id: 'trust',
    eyebrow: '01 / Trust & fraud prevention',
    title: 'Stop the right payment, explain why, recover gracefully.',
    summary: 'A coordinated card-testing pattern is caught before settlement, with human-readable evidence and a customer-safe verification path.',
    metrics: [
      ['96.8%', 'fraud probability'],
      ['94%', 'behavioral anomaly'],
      ['12.4×', 'above 90-day median'],
      ['6', 'transactions in one hour'],
    ],
    bullets: ['Rules, supervised ML, anomaly detection, device and graph signals converge.', 'The decision engine chooses BLOCK and biometric verification using governed cost parameters.', 'The analyst can inspect feature attribution, timeline, network ring, and submit feedback.'],
    links: [['Open the flagged case', '/analyst/tx/tx_9001'], ['View customer context', '/analyst/customer/4716561796955522']],
    tone: 'red',
  },
  {
    id: 'operations',
    eyebrow: '02 / Enterprise operating model',
    title: 'One control plane for risk, disputes, treasury, and oversight.',
    summary: 'VeriPay turns a payment signal into coordinated work across fraud operations, financial-institution controls, and business treasury teams.',
    metrics: [['24/7', 'risk operations'], ['4', 'decision outcomes'], ['5', 'logical data domains'], ['100%', 'auditable actions']],
    bullets: ['FI Ops monitors transactions, disputes, regulatory reports, and immutable audit events.', 'Business teams manage spend policies, merchant controls, webhooks, and dispute transitions.', 'Role boundaries keep institutional and merchant workflows separate while contracts connect them.'],
    links: [['Open FI Ops console', '/fi-ops'], ['Open treasury workspace', '/treasury'], ['Review bank risk analytics', '/bank/analytics']],
    tone: 'indigo',
  },
  {
    id: 'platform',
    eyebrow: '03 / Technology platform',
    title: 'Composable, governed, and designed to keep operating when signals fail.',
    summary: 'The architecture combines streaming features, model ensembles, graph intelligence, explainability, and a closed learning loop behind stable service contracts.',
    metrics: [['26', 'backend services'], ['4', 'risk axes'], ['0', 'LLM authorization paths'], ['0.25', 'PSI drift trigger']],
    bullets: ['Kafka, Redis, PostgreSQL, and Flink support real-time feature and event flows.', 'Unavailable downstream signals degrade safely; fusion redistributes weight instead of silently guessing.', 'Feedback, drift monitoring, champion comparison, and retraining create governed improvement.'],
    links: [['Inspect model status', '/analyst/models'], ['View system performance', '/analyst/performance'], ['Browse alert queue', '/analyst']],
    tone: 'teal',
  },
] as const;

const coverage = [
  ['Ingress & authorization', 'Payment enters through a stable contract and receives an immediate decision.'],
  ['Rules + ML + anomaly', 'Hard rules, XGBoost, Isolation Forest, and sequence-derived features work together.'],
  ['Graph intelligence', 'Shared merchants, communities, flagged exposure, and network risk surface coordinated fraud.'],
  ['Decision & friction', 'BLOCK, stealth review, unusual review, and PASS map to customer-safe actions.'],
  ['Investigation & explainability', 'Evidence, SHAP-style contributions, typologies, and guarded explanations support humans.'],
  ['Feedback & learning', 'Analyst labels adjust live scoring and flow to monitoring/retraining gates.'],
  ['FI + business operations', 'Disputes, compliance, settlement, treasury policy, and audit complete the operating model.'],
  ['Security & privacy', 'Role-based access, redaction boundaries, device integrity, and append-only audit protect trust.'],
];

const toneClasses = {
  red: { accent: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200', bar: 'bg-red-500' },
  indigo: { accent: 'text-indigo-700', bg: 'bg-indigo-50', border: 'border-indigo-200', bar: 'bg-indigo-600' },
  teal: { accent: 'text-teal-700', bg: 'bg-teal-50', border: 'border-teal-200', bar: 'bg-teal-600' },
};

export function ExecutiveDemo() {
  const [active, setActive] = useState(0);
  const [testResult, setTestResult] = useState<ScoreResponse | null>(null);
  const [testError, setTestError] = useState<string | null>(null);
  const [testRunning, setTestRunning] = useState(false);
  const step = steps[active];

  const runLiveTest = async () => {
    setTestRunning(true);
    setTestError(null);
    try {
      const result = await analystPost<ScoreResponse>('/score', { transaction_id: 'tx_9001' });
      setTestResult(result);
    } catch {
      setTestError('The live test could not reach the scoring service.');
    } finally {
      setTestRunning(false);
    }
  };
  const tone = toneClasses[step.tone];

  return (
    <div className="min-h-screen bg-[#f7f9fc] text-slate-900">
      <header className="border-b border-slate-200 bg-[#201b4b] text-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div><p className="text-[10px] font-black uppercase tracking-[0.22em] text-[#43cddd]">VeriPay / Executive briefing</p><h1 className="mt-1 text-xl font-bold">Trust infrastructure for every payment</h1></div>
          <div className="hidden items-center gap-3 text-xs md:flex"><span className="rounded-full bg-white/10 px-3 py-1.5">Board demo mode</span><Link className="text-[#43cddd] hover:text-white" to="/fi-ops">Exit briefing →</Link></div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8 md:py-12">
        <section className="grid gap-8 lg:grid-cols-[0.9fr_1.5fr] lg:items-end">
          <div><p className="text-xs font-black uppercase tracking-[0.22em] text-[#087f7a]">The board story</p><h2 className="mt-3 max-w-xl text-4xl font-black tracking-tight text-[#201b4b] md:text-5xl">Make risk decisions that earn trust.</h2><p className="mt-5 max-w-xl text-base leading-7 text-slate-600">A concise view of how VeriPay protects customers, scales institutional operations, and turns governed intelligence into measurable outcomes.</p><div className="mt-7 flex flex-wrap gap-3">
              <button type="button" onClick={runLiveTest} disabled={testRunning} className="rounded-lg bg-[#087f7a] px-4 py-2.5 text-sm font-bold text-white shadow-sm hover:bg-[#06645f] disabled:cursor-wait disabled:opacity-60">
                {testRunning ? 'Running live test…' : '▶ Run live test'}
              </button>
              <Link to="/analyst/tx/tx_9001" className="rounded-lg bg-[#29265f] px-4 py-2.5 text-sm font-bold text-white shadow-sm hover:bg-[#201b4b]">Open live case</Link>
              <a href="#coverage" className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 hover:border-[#43cddd]">See capability coverage</a>
            </div>
            {(testResult || testError) && (
              <div className={`mt-5 rounded-xl border p-4 ${testError ? 'border-red-200 bg-red-50' : 'border-teal-200 bg-teal-50'}`} aria-live="polite">
                {testError ? <p className="text-sm font-semibold text-red-700">{testError}</p> : testResult && (
                  <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
                    <div><p className="text-[10px] font-black uppercase tracking-widest text-slate-500">Live decision</p><p className="mt-1 text-lg font-black text-red-700">{testResult.decision}</p></div>
                    <div><p className="text-[10px] font-black uppercase tracking-widest text-slate-500">Fraud probability</p><p className="mt-1 text-lg font-black text-[#201b4b]">{(testResult.fraud_probability * 100).toFixed(1)}%</p></div>
                    <div><p className="text-[10px] font-black uppercase tracking-widest text-slate-500">Anomaly</p><p className="mt-1 text-lg font-black text-[#201b4b]">{(testResult.anomaly_score * 100).toFixed(1)}%</p></div>
                    <div className="min-w-[220px] flex-1"><p className="text-[10px] font-black uppercase tracking-widest text-slate-500">Action</p><p className="mt-1 text-sm font-bold text-slate-700">{testResult.verification_action}</p></div>
                  </div>
                )}
              </div>
            )}</div>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">{[['$2.4B', 'protected volume'], ['99.97%', 'decision uptime'], ['33%', 'fewer false positives'], ['<80ms', 'target latency']].map(([value, label]) => <div key={label} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"><p className="text-2xl font-black text-[#201b4b]">{value}</p><p className="mt-1 text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p></div>)}</div>
        </section>

        <section className="mt-12 grid gap-6 lg:grid-cols-[250px_1fr]" aria-label="Executive demo chapters">
          <nav className="space-y-2">{steps.map((item, index) => <button key={item.id} onClick={() => setActive(index)} className={`w-full rounded-xl border px-4 py-4 text-left transition ${active === index ? 'border-[#43cddd] bg-white shadow-md' : 'border-transparent bg-white/60 hover:border-slate-200'}`}><span className="text-[10px] font-black uppercase tracking-widest text-slate-400">{item.eyebrow}</span><span className={`mt-1 block text-sm font-bold ${active === index ? 'text-[#201b4b]' : 'text-slate-600'}`}>{item.title}</span></button>)}</nav>
          <article className={`rounded-2xl border ${tone.border} ${tone.bg} p-6 md:p-8`}><p className={`text-xs font-black uppercase tracking-[0.2em] ${tone.accent}`}>{step.eyebrow}</p><h3 className="mt-3 max-w-3xl text-3xl font-black tracking-tight text-[#201b4b]">{step.title}</h3><p className="mt-4 max-w-3xl text-base leading-7 text-slate-700">{step.summary}</p><div className="mt-7 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{step.metrics.map(([value, label]) => <div key={label} className="rounded-xl border border-white/80 bg-white/75 p-4"><p className={`text-2xl font-black ${tone.accent}`}>{value}</p><p className="mt-1 text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p></div>)}</div><div className="mt-7 grid gap-6 lg:grid-cols-[1fr_0.8fr]"><div><p className="text-xs font-black uppercase tracking-widest text-slate-500">What to say</p><ul className="mt-3 space-y-3">{step.bullets.map((bullet) => <li key={bullet} className="flex gap-3 text-sm leading-6 text-slate-700"><span className={`mt-2 h-2 w-2 shrink-0 rounded-full ${tone.bar}`} />{bullet}</li>)}</ul></div><div><p className="text-xs font-black uppercase tracking-widest text-slate-500">Jump to evidence</p><div className="mt-3 space-y-2">{step.links.map(([label, href]) => <Link key={href} to={href} className="block rounded-lg border border-white bg-white/80 px-4 py-3 text-sm font-bold text-[#29265f] hover:bg-white">{label} <span className="float-right">→</span></Link>)}</div></div></div></article>
        </section>

        <section id="coverage" className="mt-14"><div className="flex flex-col justify-between gap-3 md:flex-row md:items-end"><div><p className="text-xs font-black uppercase tracking-[0.2em] text-[#087f7a]">Capability map</p><h3 className="mt-2 text-2xl font-black text-[#201b4b]">Coverage across the platform</h3></div><p className="max-w-md text-sm leading-6 text-slate-500">Every point in the board narrative maps to a navigable product surface or an exercised backend contract.</p></div><div className="mt-5 grid gap-3 md:grid-cols-2">{coverage.map(([title, detail], index) => <div key={title} className="flex gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm"><span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-[#e7f7f5] text-sm font-black text-[#087f7a]">{String(index + 1).padStart(2, '0')}</span><div><p className="font-bold text-[#201b4b]">{title}</p><p className="mt-1 text-sm leading-6 text-slate-500">{detail}</p></div></div>)}</div></section>

        <section className="mt-12 rounded-2xl bg-[#201b4b] p-6 text-white md:p-8"><div className="grid gap-6 md:grid-cols-[1fr_auto] md:items-center"><div><p className="text-xs font-black uppercase tracking-[0.2em] text-[#43cddd]">Recommended close</p><h3 className="mt-2 text-2xl font-black">From signal to confidence, without surrendering control.</h3><p className="mt-3 max-w-2xl text-sm leading-6 text-indigo-100">Run the alert queue, inspect the card-testing case, submit an analyst verdict, then show model performance and retraining governance.</p></div><Link to="/analyst" className="rounded-lg bg-[#43cddd] px-5 py-3 text-center text-sm font-black text-[#201b4b] hover:bg-white">Open analyst console →</Link></div></section>
      </main>
    </div>
  );
}
