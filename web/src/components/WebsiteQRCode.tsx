import { useEffect, useState } from 'react';
import QRCode from 'qrcode';

type Props = {
  url: string;
  size?: number;
};

const SCAN_LABEL = 'Scan to open the demo on your phone';

/**
 * A QR code that opens `url` when scanned by a phone camera.
 * Mirrors the `WebsiteQRCode` view used in the iOS demo app.
 */
export function WebsiteQRCode({ url, size = 128 }: Props) {
  const [dataUrl, setDataUrl] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    QRCode.toDataURL(url, { margin: 1, width: size * 3 })
      .then((src) => {
        if (!cancelled) setDataUrl(src);
      })
      .catch(() => {
        /* Leave the placeholder visible if generation fails. */
      });
    return () => {
      cancelled = true;
    };
  }, [url, size]);

  return (
    <a
      href={url}
      target="_blank"
      rel="noreferrer"
      className="group inline-flex flex-col items-center gap-3"
      aria-label={`${SCAN_LABEL}. Opens ${url}`}
    >
      <span className="relative rounded-2xl border border-[#BFD0EA] bg-white p-3 shadow-[0_12px_30px_rgba(82,104,216,0.12)] transition group-hover:-translate-y-0.5 group-hover:shadow-[0_16px_40px_rgba(82,104,216,0.18)]">
        {dataUrl ? (
          <img
            src={dataUrl}
            alt="QR code"
            width={size}
            height={size}
            className="block [image-rendering:pixelated]"
          />
        ) : (
          <span
            className="grid place-items-center bg-[#EFF4FF] text-[#8192AA]"
            style={{ width: size, height: size }}
            aria-hidden="true"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className="h-16 w-16"
            >
              <rect x="3" y="3" width="7" height="7" rx="1" />
              <rect x="14" y="3" width="7" height="7" rx="1" />
              <rect x="3" y="14" width="7" height="7" rx="1" />
              <path d="M14 14h3v3h-3zM20 14h1M14 20h4M20 20h0.6" />
            </svg>
          </span>
        )}
        <span
          className="absolute -right-2 -top-2 grid h-8 w-8 place-items-center rounded-lg bg-[#5268D8] text-white shadow-md"
          aria-hidden="true"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-4 w-4"
          >
            <path d="M7 17L17 7M9 7h8v8" />
          </svg>
        </span>
      </span>

      <span className="flex flex-col items-center gap-1">
        <span className="text-xs font-bold text-[#5268D8]">{SCAN_LABEL}</span>
        <span className="text-[11px] text-[#8192AA]">
          {url.replace(/^https?:\/\//, '')}
        </span>
      </span>
    </a>
  );
}

/** The public URL of the deployed demo site, used as the QR target. */
export const DEMO_SITE_URL = 'https://veripay-services.vercel.app/';