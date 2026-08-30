// MSW (Mock Service Worker) handlers for the local demo.
// Paths and payloads mirror the web client contract (web/src/api, web/src/types).
import { http, HttpResponse } from "msw";
import { analystHandlers } from "./analystHandlers";

const transactions = [
  {
    transactionId: "tx_mock_001",
    userId: "u_100",
    amountMinor: 4999,
    currency: "USD",
    merchantId: "m_amazon",
  },
  {
    transactionId: "tx_mock_002",
    userId: "u_204",
    amountMinor: 125000,
    currency: "USD",
    merchantId: "m_wire",
  },
  {
    transactionId: "tx_mock_003",
    userId: "u_077",
    amountMinor: 2140,
    currency: "EUR",
    merchantId: "m_insta",
  },
];

export const handlers = [
  ...analystHandlers,

  http.get("/api/transactions", () => HttpResponse.json(transactions)),

  http.get("/api/transactions/:txId/risk", ({ params }) =>
    HttpResponse.json({
      transactionId: params.txId,
      unifiedScore: 42,
      band: "VERIFY",
      components: [
        { component: "supervised", score: 35, weight: 0.3, available: true, reasonCode: "NEW_DEVICE" },
        { component: "anomaly", score: 50, weight: 0.15, available: true },
      ],
    }),
  ),
];
