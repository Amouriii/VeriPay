#!/usr/bin/env bash
# Raise an account-free public HTTPS URL to a local VeriPay service.
#
# Uses a Cloudflare quick tunnel (trycloudflare.com) - no Cloudflare account,
# no API token, no cost. The URL is live for as long as this process runs.
#
# Usage:
#   scripts/live-demo-tunnel.sh [port]     (default 5173 = web dashboard)
#   scripts/live-demo-tunnel.sh 8001       (ingress API)
#
# Requires cloudflared (https://developers.cloudflare.com/cloudflare-one/):
#   brew install cloudflared        # macOS
#   winget install Cloudflare.cloudflared   # Windows
set -euo pipefail

PORT="${1:-5173}"

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared is not installed. Install it (no account needed), then retry:"
  echo "  brew install cloudflared"
  echo "  https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
  exit 1
fi

echo "Exposing http://localhost:${PORT} through a public HTTPS tunnel..."
echo "Copy the https://<random>.trycloudflare.com URL from the output below."
echo "Press Ctrl+C to stop the tunnel."
exec cloudflared tunnel --url "http://localhost:${PORT}"
