export function VeriPayMark({
  compact = false,
  variant = 'teal',
}: {
  compact?: boolean;
  /** Visual identity: 'teal' for customers, 'indigo' for bank operations. */
  variant?: 'teal' | 'indigo';
}) {
  const isIndigo = variant === 'indigo';

  const markBg = isIndigo ? 'bg-[#8b8ff2]' : 'bg-[#43cddd]';

  const markRing = isIndigo
    ? 'border-white'
    : 'border-[#29265f]';

  // IMPORTANT:
  // Bank login has a dark background, so the indigo wordmark must be white.
  const wordmarkColor = isIndigo
    ? 'text-white'
    : 'text-[#102a43]';

  const subtitleColor = isIndigo
    ? 'text-[#8b8ff2]'
    : 'text-[#2e2c83]';

  const subtitleText = isIndigo
    ? 'Operations console'
    : 'Secure payments';

  return (
    <div className="flex items-center gap-2.5">
      {/* VeriPay shield */}
      <span
        className={`relative grid shrink-0 place-items-center ${markBg} text-[#29265f] shadow-[0_7px_20px_rgba(46,44,131,0.22)] [clip-path:polygon(50%_0%,91%_17%,86%_67%,50%_100%,14%_67%,9%_17%)] ${
          compact ? 'h-10 w-10' : 'h-12 w-12'
        }`}
        aria-hidden="true"
      >
        <span
          className={`grid place-items-center rounded-full border-2 ${markRing} font-black ${
            compact
              ? 'h-6 w-6 text-xs'
              : 'h-7 w-7 text-sm'
          }`}
        >
          V
        </span>

        <span
          className={`absolute rotate-45 border-b-2 border-r-2 ${markRing} ${
            compact
              ? 'bottom-2 right-1 h-2 w-1.5'
              : 'bottom-2.5 right-1.5 h-2.5 w-2'
          }`}
        />
      </span>

      {/* Wordmark */}
      <span>
        <span
          className={`block font-bold tracking-tight ${wordmarkColor} ${
            compact ? 'text-lg' : 'text-xl'
          }`}
        >
          VeriPay
        </span>

        {!compact && (
          <span
            className={`block text-[9px] font-black uppercase tracking-[0.18em] ${subtitleColor}`}
          >
            {subtitleText}
          </span>
        )}
      </span>
    </div>
  );
}