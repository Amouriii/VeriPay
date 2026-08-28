// Renders a decision action label (PLAN §19).
export function DecisionBadge({ action }: { action: string }) {
  const tone =
    action === 'BLOCK'
      ? 'bg-red-500/10 text-red-600 ring-red-500/25 dark:bg-red-400/15 dark:text-red-300 dark:ring-red-400/30'
      : action === 'VERIFY'
        ? 'bg-amber-400/15 text-amber-700 ring-amber-500/30 dark:bg-amber-400/10 dark:text-amber-300 dark:ring-amber-400/25'
        : action === 'ALLOW'
          ? 'bg-emerald-500/10 text-emerald-700 ring-emerald-500/25 dark:bg-emerald-400/10 dark:text-emerald-300 dark:ring-emerald-400/25'
          : 'bg-ink/[0.06] text-ink-muted ring-ink/10 dark:bg-white/10 dark:text-ink-muted dark:ring-white/15';
  return <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${tone}`}>{action}</span>;
}
