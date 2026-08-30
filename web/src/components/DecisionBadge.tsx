// Renders a decision action label (PLAN §19).
export function DecisionBadge({ action }: { action: string }) {
  return <span className="rounded px-2 py-1 bg-slate-200 text-sm">{action}</span>;
}
