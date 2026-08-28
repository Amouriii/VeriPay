export function VeriPayMark({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <span className={`relative grid shrink-0 place-items-center bg-[#43cddd] text-[#29265f] shadow-[0_6px_18px_rgba(46,44,131,0.24)] [clip-path:polygon(50%_0%,91%_17%,86%_67%,50%_100%,14%_67%,9%_17%)] ${compact ? 'h-10 w-10' : 'h-14 w-14'}`} aria-hidden="true">
        <span className={`grid place-items-center rounded-full border-2 border-[#29265f] font-black ${compact ? 'h-6 w-6 text-xs' : 'h-8 w-8 text-sm'}`}>V</span>
        <span className={`absolute rotate-45 border-b-2 border-r-2 border-[#29265f] ${compact ? 'bottom-2 right-1 h-2 w-1.5' : 'bottom-3 right-2 h-3 w-2'}`} />
      </span>
      <span>
        <span className={`block font-semibold tracking-tight ${compact ? 'text-lg' : 'text-2xl'}`}>VeriPay</span>
        {!compact && <span className="block text-[10px] font-bold uppercase tracking-[0.2em] text-[#2e2c83]">Secure payments</span>}
      </span>
    </div>
  );
}
