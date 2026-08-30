import Foundation

/// Live analyst integration for the demo app.
///
/// POSTs the fictional demo transaction to the local ``analyst_api`` composite
/// (`/explain`) and maps the response — fused risk score, decision, governed
/// case report, and the new network/graph scoring axis — onto the demo's
/// ``FraudAnalysis`` model. Any failure (backend down, bad payload, ATS block)
/// returns ``nil`` so ``DemoStore`` transparently falls back to the local mock.
enum LiveRiskService {
  /// The analyst_api composite (see README Service table: analyst_api = 8026).
  /// The iOS Simulator shares the host loopback, so 127.0.0.1 reaches the Mac.
  static let analystAPIBase = URL(string: "http://127.0.0.1:8026")!

  static func evaluate(scenario: DemoScenario, transaction: DemoTransaction) async -> FraudAnalysis? {
    let suspicious = scenario == .highRisk
    let amount = NSDecimalNumber(decimal: transaction.amount).doubleValue

    let payload = TransactionPayload(
      transaction_id: "demo-\(Int(Date().timeIntervalSince1970))-\(transaction.id.uuidString.prefix(4))",
      cc_num: 453201, // single demo customer so the graph engine builds real history
      amount: amount,
      merchant: transaction.merchant,
      category: transaction.category,
      timestamp: Self.iso8601.string(from: transaction.date) ?? "",
      location: Self.location(for: scenario),
      mcc_risk: suspicious ? 0.85 : 0.2,
      new_device: suspicious ? 0.6 : 0.0
    )

    guard let body = try? JSONEncoder().encode(RequestBody(transaction: payload)) else { return nil }
    var request = URLRequest(url: analystAPIBase.appendingPathComponent("explain"))
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    request.httpBody = body
    request.timeoutInterval = 6

    do {
      let (data, response) = try await URLSession.shared.data(for: request)
      guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else { return nil }
      let decoder = JSONDecoder()
      decoder.keyDecodingStrategy = .convertFromSnakeCase
      let decoded = try decoder.decode(ExplainResponse.self, from: data)
      return Self.map(decoded, suspicious: suspicious)
    } catch {
      return nil
    }
  }

  /// Approximate coordinates for the demo's fictional locations.
  private static func location(for scenario: DemoScenario) -> LocationPayload? {
    switch scenario {
    case .lowRisk: return LocationPayload(lat: 40.7128, lon: -74.0060) // New York, NY
    case .highRisk: return LocationPayload(lat: 38.7223, lon: -9.1393) // Lisbon, Portugal
    }
  }

  // MARK: - Mapping

  private static func map(_ response: ExplainResponse, suspicious: Bool) -> FraudAnalysis {
    let high = response.score.decision != "PASS"
    let level: FraudAnalysis.RiskLevel = high ? .high : .low
    let score = min(100, max(0, response.score.fusedRiskScore))
    let headline: String
    switch response.score.decision {
    case "PASS": headline = "Transaction approved"
    case "BLOCK": headline = "Transaction blocked"
    default: headline = "Verification required"
    }
    let symbol = high ? "exclamationmark.triangle.fill" : "checkmark.seal.fill"

    var reasons: [RiskReason] = []
    for evidence in response.caseReport.evidence {
      let trimmed = evidence.trimmingCharacters(in: .whitespacesAndNewlines)
      guard !trimmed.isEmpty else { continue }
      reasons.append(RiskReason(title: String(trimmed.prefix(64)), detail: "", symbol: symbol))
      if reasons.count >= 3 { break }
    }

    // Surface the network/graph axis (PLAN §12) explicitly.
    if response.score.networkAvailable {
      let detail: String
      if response.score.networkFindings.isEmpty {
        detail = suspicious
          ? "Connected to a suspicious merchant network."
          : "No abnormal network connections found."
      } else {
        detail = response.score.networkFindings.joined(separator: ". ")
      }
      reasons.append(
        RiskReason(title: "Network graph analysis", detail: detail, symbol: "point.3.connected.trianglepath.dotted")
      )
    }

    if reasons.isEmpty {
      reasons.append(
        RiskReason(
          title: high ? "Transaction flagged" : "Transaction looks normal",
          detail: response.caseReport.patternMatch,
          symbol: symbol
        )
      )
    }

    let summary = response.caseReport.verdict.isEmpty
      ? (high ? "This transaction differs from typical account behavior and needs review." : "This purchase matched expected behavior and was approved.")
      : response.caseReport.verdict

    return FraudAnalysis(score: score, level: level, headline: headline, summary: summary, reasons: reasons)
  }

  // MARK: - Wire models

  private struct TransactionPayload: Encodable {
    let transaction_id: String
    let cc_num: Int
    let amount: Double
    let merchant: String
    let category: String
    let timestamp: String
    let location: LocationPayload?
    let mcc_risk: Double
    let new_device: Double
  }

  private struct LocationPayload: Encodable {
    let lat: Double
    let lon: Double
  }

  private struct RequestBody: Encodable {
    let transaction: TransactionPayload
  }

  private struct ExplainResponse: Decodable {
    let caseReport: CaseReportPayload
    let score: ScorePayload
  }

  private struct CaseReportPayload: Decodable {
    let verdict: String
    let evidence: [String]
    let patternMatch: String
  }

  private struct ScorePayload: Decodable {
    let decision: String
    let riskLevel: String
    let fusedRiskScore: Int
    let networkAvailable: Bool
    let networkFindings: [String]
  }

  private static let iso8601: ISO8601DateFormatter = {
    let formatter = ISO8601DateFormatter()
    formatter.formatOptions = [.withInternetDateTime]
    return formatter
  }()
}
