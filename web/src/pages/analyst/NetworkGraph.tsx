// Network analysis view for a transaction — the PLAN §12 fourth scoring axis.
// Renders the customer's ego graph (pure SVG, no d3 dependency) plus the
// network risk indicators returned by the graph engine. Includes a full-ring
// community view that renders the entire Louvain-style cluster around a
// flagged customer, with aggregate cluster stats.
import { useState } from 'react';
import type { Community, CommunityStats, NetworkEgo, NetworkFeatures } from '../../types/analyst';

const STATUS_FILL: Record<string, string> = {
  self: '#29265f',
  flagged: '#dc2626',
  review: '#f97316',
  normal: '#94a3b8',
};

const STATUS_LABEL: Record<string, string> = {
  self: 'This customer',
  flagged: 'Confirmed fraud',
  review: 'Flagged for review',
  normal: 'Normal account',
};

const RING_RADIUS_INNER = 90;
const RING_RADIUS_OUTER = 160;
const CENTER = { x: 180, y: 180 };

function placeOnRing(index: number, total: number, radius: number) {
  const step = total > 1 ? (2 * Math.PI) / total : 0;
  const angle = index * step - Math.PI / 2;
  return {
    x: CENTER.x + radius * Math.cos(angle),
    y: CENTER.y + radius * Math.sin(angle),
  };
}

function NetworkFeature({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-slate-100 py-1.5">
      <span className="text-sm text-slate-600">{label}</span>
      <span className="font-semibold tabular-nums text-[#201b4b]">{value}</span>
    </div>
  );
}

export function EgoGraph({ ego }: { ego: NetworkEgo }) {
  const customers = ego.nodes.filter((n) => n.kind === 'customer' && n.status !== 'self');
  const merchants = ego.nodes.filter((n) => n.kind === 'merchant');

  const positions: Record<string, { x: number; y: number }> = {};
  const selfNode = ego.nodes.find((n) => n.status === 'self');
  if (selfNode) positions[selfNode.id] = CENTER;
  merchants.forEach((m, i) => {
    positions[m.id] = placeOnRing(i, merchants.length || 1, RING_RADIUS_INNER);
  });
  customers.forEach((c, i) => {
    positions[c.id] = placeOnRing(i, customers.length || 1, RING_RADIUS_OUTER);
  });

  const maxWeight = Math.max(1, ...ego.edges.map((e) => e.weight));

  return (
    <svg viewBox="0 0 360 360" className="w-full max-w-md" role="img" aria-label="Customer ego graph">
      {/* edges */}
      {ego.edges.map((e) => {
        const a = positions[e.from];
        const b = positions[e.to];
        if (!a || !b) return null;
        const w = Math.max(1, (e.weight / maxWeight) * 6);
        return (
          <line
            key={`${e.from}-${e.to}`}
            x1={a.x}
            y1={a.y}
            x2={b.x}
            y2={b.y}
            stroke="#cbd5e1"
            strokeWidth={w}
            strokeOpacity={0.7}
          />
        );
      })}
      {/* nodes */}
      {ego.nodes.map((n) => {
        const p = positions[n.id];
        if (!p) return null;
        const fill = STATUS_FILL[n.status] ?? STATUS_FILL.normal;
        const r = n.status === 'self' ? 12 : n.kind === 'merchant' ? 9 : 7;
        return (
          <g key={n.id}>
            <circle cx={p.x} cy={p.y} r={r} fill={fill} stroke="#fff" strokeWidth={1.5} />
            <text
              x={p.x}
              y={p.y + r + 11}
              textAnchor="middle"
              className="fill-slate-500 text-[8px] font-medium"
            >
              {n.label.length > 14 ? `${n.label.slice(0, 12)}…` : n.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

const PATTERN_LABEL: Record<string, string> = {
  fraud_ring: 'Fraud ring',
  mixed_cluster: 'Mixed cluster',
  shared_merchant_collapse: 'Shared-merchant collapse',
  normal_cluster: 'Normal cluster',
  isolated: 'Isolated',
};

function PatternBadge({ pattern }: { pattern: CommunityStats['dominant_pattern'] }) {
  const label = PATTERN_LABEL[pattern] ?? pattern;
  const tone =
    pattern === 'fraud_ring'
      ? 'border-red-300 bg-red-50 text-red-700'
      : pattern === 'mixed_cluster'
        ? 'border-orange-300 bg-orange-50 text-orange-700'
        : 'border-slate-200 bg-slate-50 text-slate-600';
  return (
    <span className={`inline-block rounded-full border px-2.5 py-0.5 text-xs font-semibold ${tone}`}>
      {label}
    </span>
  );
}

function CommunityView({ community }: { community: Community }) {
  const { stats, graph } = community;
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">
          Community / fraud ring
        </h3>
        <PatternBadge pattern={stats.dominant_pattern} />
      </div>
      <p className="text-sm text-slate-500">
        The full connected component around this customer via shared merchants —
        the Louvain-style community, not just 1-hop peers.
      </p>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-3 text-center">
          <p className="text-xs text-slate-500">Cluster size</p>
          <p className="mt-1 text-2xl font-semibold text-[#201b4b]">{stats.cluster_size}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-3 text-center">
          <p className="text-xs text-slate-500">Confirmed fraud</p>
          <p className="mt-1 text-2xl font-semibold text-red-600">
            {stats.flagged_count}
            <span className="ml-1 text-sm text-slate-400">
              ({(stats.flagged_ratio * 100).toFixed(0)}%)
            </span>
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-3 text-center">
          <p className="text-xs text-slate-500">Shared merchants</p>
          <p className="mt-1 text-2xl font-semibold text-[#201b4b]">
            {stats.distinct_shared_merchants}
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <p className="text-xs text-slate-500">
          Total volume across cluster
          <span className="ml-1 font-semibold text-[#201b4b]">
            ${stats.total_volume.toLocaleString()}
          </span>
        </p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5">
        <EgoGraph ego={graph} />
        <div className="mt-4 flex flex-wrap gap-3 text-xs text-slate-600">
          {Object.entries(STATUS_LABEL).map(([key, label]) => (
            <span key={key} className="inline-flex items-center gap-1.5">
              <span
                className="inline-block h-3 w-3 rounded-full"
                style={{ backgroundColor: STATUS_FILL[key] }}
              />
              {label}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

export function NetworkGraph({
  risk,
  available,
  findings,
  features,
  ego,
  community,
}: {
  risk: number;
  available: boolean;
  findings: string[];
  features?: NetworkFeatures;
  ego?: NetworkEgo;
  community?: Community;
}) {
  const [view, setView] = useState<'ego' | 'community'>('ego');

  if (!available) {
    return (
      <div className="rounded-lg border border-slate-200 bg-slate-50 p-6 text-center text-sm text-slate-500">
        No network signal for this transaction. The customer is not connected to
        any other observed account via shared merchants.
      </div>
    );
  }

  const showCommunityToggle = !!community && community.stats.cluster_size > 1;

  return (
    <div className="space-y-6">
      {/* risk score */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">
            Network risk score
          </p>
          <p className="mt-1 text-3xl font-semibold text-[#201b4b]">
            {risk.toFixed(2)}
            <span className="ml-1 text-sm text-slate-500">/ 1.00</span>
          </p>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-gradient-to-r from-emerald-500 via-orange-400 to-red-500"
              style={{ width: `${risk * 100}%` }}
            />
          </div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">
            Network risk indicators
          </p>
          <ul className="mt-2 space-y-2">
            {findings.length === 0 ? (
              <li className="text-sm text-slate-500">No indicators above threshold.</li>
            ) : (
              findings.map((f) => (
                <li key={f} className="flex gap-2 text-sm text-slate-700">
                  <span className="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-[#43cddd]" />
                  <span>{f}</span>
                </li>
              ))
            )}
          </ul>
        </div>
      </div>

      {/* view toggle: ego (1-hop) vs community (full ring) */}
      {showCommunityToggle && (
        <div className="flex gap-1 rounded-lg border border-slate-200 bg-slate-50 p-1">
          {([
            ['ego', 'Ego (1-hop)'],
            ['community', 'Community (full ring)'],
          ] as ['ego' | 'community', string][]).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setView(key)}
              className={`rounded-md px-3 py-1.5 text-sm font-semibold transition ${
                view === key
                  ? 'bg-[#29265f] text-white shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      )}

      {view === 'community' && community ? (
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <CommunityView community={community} />
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
          {/* ego graph */}
          <div className="rounded-xl border border-slate-200 bg-white p-5">
            <h3 className="mb-1 text-xs font-bold uppercase tracking-[0.16em] text-slate-500">
              Customer ego graph
            </h3>
            <p className="mb-4 text-sm text-slate-500">
              The customer at center, direct connections radiating outward.
            </p>
            {ego && <EgoGraph ego={ego} />}
            {/* legend */}
            <div className="mt-4 flex flex-wrap gap-3 text-xs text-slate-600">
              {Object.entries(STATUS_LABEL).map(([key, label]) => (
                <span key={key} className="inline-flex items-center gap-1.5">
                  <span
                    className="inline-block h-3 w-3 rounded-full"
                    style={{ backgroundColor: STATUS_FILL[key] }}
                  />
                  {label}
                </span>
              ))}
            </div>
          </div>

        {/* node features */}
        {features && (
          <aside className="rounded-xl border border-slate-100 bg-slate-50 p-4">
            <h3 className="mb-2 font-semibold text-[#201b4b]">Node features</h3>
            <NetworkFeature label="Distinct merchants" value={features.merchant_degree} />
            <NetworkFeature label="Merchant fan-in" value={features.merchant_fan_in} />
            <NetworkFeature label="Shared counterparties" value={features.shared_counterparty_count} />
            <NetworkFeature label="Temporal co-occurrences" value={features.co_occurrence_count} />
            <NetworkFeature label="Flagged neighbors" value={features.flagged_neighbor_count} />
            <NetworkFeature
              label="Flagged exposure"
              value={`${(features.flagged_exposure * 100).toFixed(0)}%`}
            />
            <NetworkFeature label="Cluster size" value={features.cluster_size} />
            <NetworkFeature
              label="Cluster flagged ratio"
              value={`${(features.cluster_flagged_ratio * 100).toFixed(0)}%`}
            />
            <p className="mt-3 text-xs leading-4 text-slate-500">
              The graph axis exposes relationships no per-customer model can see:
              shared merchants, temporal co-occurrence, and propagation from
              confirmed-fraud peers.
            </p>
          </aside>
        )}
        </div>
      )}
    </div>
  );
}
