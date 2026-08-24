import type { ShapAttributionDto } from '../types';

export function SHAPReasonList({ attributions }: { attributions: ShapAttributionDto[] }) {
  return (
    <ul className="text-sm">
      {attributions.map((a) => (
        <li key={a.reasonCode}>{a.reasonCode} ({a.direction})</li>
      ))}
    </ul>
  );
}
