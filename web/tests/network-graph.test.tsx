// @vitest-environment jsdom
//
// Component tests for the NetworkGraph view (PLAN §12 fourth scoring axis).
// It renders the customer ego graph plus the full fraud-ring community view.
// Uses plain react-dom rendering into jsdom so no extra test libraries are
// required beyond what the repo already ships.
import { describe, it, expect, beforeAll, beforeEach } from 'vitest';

// Enable React 18's act() assertion support so we don't emit act warnings.
beforeAll(() => {
  (globalThis as Record<string, unknown>).IS_REACT_ACT_ENVIRONMENT = true;
});
import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import type { Community, NetworkEgo, NetworkFeatures } from '../src/types/analyst';
import { NetworkGraph } from '../src/pages/analyst/NetworkGraph';

const ego: NetworkEgo = {
  nodes: [
    { id: 'self', kind: 'customer', label: 'Avery Morgan', status: 'self' },
    { id: 'm1', kind: 'merchant', label: 'Alice Retail', status: 'normal' },
    { id: 'c2', kind: 'customer', label: 'Bob Ames', status: 'flagged' },
  ],
  edges: [
    { from: 'self', to: 'm1', weight: 3 },
    { from: 'm1', to: 'c2', weight: 2 },
  ],
};

const features: NetworkFeatures = {
  merchant_degree: 2,
  merchant_fan_in: 1,
  shared_counterparty_count: 1,
  co_occurrence_count: 0,
  flagged_neighbor_count: 1,
  flagged_exposure: 0.5,
  cluster_size: 4,
  cluster_flagged_ratio: 0.25,
};

const COMMUNITY_STATS: Community = {
  graph: ego,
  members: [
    { cc_num: 4000000000000001, status: 'self' },
    { cc_num: 4000000000000002, status: 'flagged' },
    { cc_num: 4000000000000003, status: 'flagged' },
  ],
  stats: {
    cluster_size: 5,
    flagged_count: 2,
    flagged_ratio: 0.4,
    distinct_shared_merchants: 3,
    total_volume: 85000,
    dominant_pattern: 'fraud_ring',
  },
};

let container: HTMLElement;

function renderFixture(props?: { available?: boolean }) {
  const available = props?.available ?? true;
  const root = createRoot(container);
  act(() => {
    root.render(
      <NetworkGraph
        risk={0.73}
        available={available}
        findings={
          available
            ? ['Shares merchant(s) with confirmed-fraud account(s).', 'Temporal co-occurrence with flagged peers.']
            : []
        }
        features={available ? features : undefined}
        ego={available ? ego : undefined}
        community={available ? COMMUNITY_STATS : undefined}
      />,
    );
  });
  return root;
}

beforeEach(() => {
  container = document.createElement('div');
  document.body.appendChild(container);
});

describe('NetworkGraph', () => {
  it('shows the isolated fallback when no network signal is available', () => {
    renderFixture({ available: false });
    expect(container.textContent).toContain(
      'No network signal for this transaction',
    );
  });

  it('renders the risk score and findings in the ego view by default', () => {
    renderFixture();
    const text = container.textContent ?? '';
    expect(text).toContain('Network risk score');
    expect(text).toContain('0.73');
    expect(text).toContain('Shares merchant(s) with confirmed-fraud account(s)');
    expect(container.querySelector('svg')).not.toBeNull();
    // ego legend includes the self/flagged/normal labels
    expect(text).toContain('This customer');
    expect(text).toContain('Confirmed fraud');
  });

  it('renders the node-feature panel with formatted percentages', () => {
    renderFixture();
    const text = container.textContent ?? '';
    expect(text).toContain('Node features');
    expect(text).toContain('Distinct merchants');
    expect(text).toContain('Flagged exposure');
    expect(text).toContain('50%'); // flagged_exposure 0.5
    expect(text).toContain('25%'); // cluster_flagged_ratio 0.25
  });

  it('switches to the community (full ring) view on toggle and shows cluster stats', () => {
    const root = renderFixture();
    const toggle = Array.from(container.querySelectorAll('button')).find((b) =>
      b.textContent?.includes('Community (full ring)'),
    );
    expect(toggle).toBeTruthy();

    act(() => {
      toggle!.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });

    const text = container.textContent ?? '';
    expect(text).toContain('Community / fraud ring');
    expect(text).toContain('Fraud ring'); // dominant_pattern badge label
    expect(text).toContain('Cluster size');
    expect(text).toContain('Confirmed fraud');
    expect(text).toContain(COMMUNITY_STATS.stats.flagged_count.toString());
    expect(text).toContain('Total volume across cluster');
    root.unmount();
  });

  it('renders an SVG ego graph with an edge for each connection', () => {
    renderFixture();
    const svg = container.querySelector('svg');
    expect(svg).not.toBeNull();
    // self + merchant + peer = 3 nodes; 2 edges
    expect(container.querySelectorAll('circle').length).toBe(3);
    expect(container.querySelectorAll('line').length).toBe(2);
  });
});