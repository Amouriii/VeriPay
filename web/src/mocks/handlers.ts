// MSW (Mock Service Worker) handlers for Day-1 parallel development.
// Dev 2 builds all React UI against these mocks before backend is live.
import { http, HttpResponse } from "msw";

export const handlers = [
  http.get("/api/v1/transactions", () =>
    HttpResponse.json([
      {
        transaction_id: "tx_mock_001",
        user_id: "u_100",
        amount_minor: 4999,
        currency: "USD",
        merchant_id: "m_amazon",
        mti: "0100",
        channel: "CARD_NOT_PRESENT",
      },
    ]),
  ),

  http.get("/api/v1/transactions/:txId/risk", () =>
    HttpResponse.json({
      transaction_id: "tx_mock_001",
      unified_score: 42,
      band: "VERIFY",
      components: [
        { component: "supervised", score: 35, weight: 0.3, available: true, reason_code: "NEW_DEVICE" },
        { component: "anomaly", score: 50, weight: 0.15, available: true },
      ],
    }),
  ),

  http.post("/api/v1/investigate/:txId", () =>
    HttpResponse.json({
      transaction_id: "tx_mock_001",
      analyst_summary:
        "Transaction flagged for elevated risk. Primary driver: NEW_DEVICE with z-score 2.8 on amount.",
      guardrail_violation: false,
    }),
  ),
];
