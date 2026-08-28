import Foundation

enum MockBankingService {
  static let account = DemoAccount(
    customerName: "Maya Bennett",
    firstName: "Maya",
    balance: 12_846.72,
    availableCredit: 8_420.00,
    cardLastFour: "4821"
  )

  static func recentTransactions(referenceDate: Date = Date()) -> [DemoTransaction] {
    [
      DemoTransaction(
        merchant: "Lumen Coffee Roasters",
        category: "Dining",
        amount: 8.75,
        location: "Brooklyn, NY",
        date: referenceDate.addingTimeInterval(-3_600),
        symbol: "cup.and.saucer.fill",
        status: .completed
      ),
      DemoTransaction(
        merchant: "Northstar Market",
        category: "Groceries",
        amount: 64.28,
        location: "New York, NY",
        date: referenceDate.addingTimeInterval(-86_400),
        symbol: "basket.fill",
        status: .completed
      ),
      DemoTransaction(
        merchant: "Metro Transit",
        category: "Transportation",
        amount: 33.00,
        location: "New York, NY",
        date: referenceDate.addingTimeInterval(-172_800),
        symbol: "tram.fill",
        status: .completed
      ),
      DemoTransaction(
        merchant: "Arc & Alder",
        category: "Home",
        amount: 126.40,
        location: "Brooklyn, NY",
        date: referenceDate.addingTimeInterval(-259_200),
        symbol: "house.fill",
        status: .completed
      ),
    ]
  }

  static func transaction(for scenario: DemoScenario, date: Date = Date()) -> DemoTransaction {
    switch scenario {
    case .lowRisk:
      return DemoTransaction(
        merchant: "Northstar Market",
        category: "Groceries",
        amount: 42.18,
        location: "Brooklyn, NY",
        date: date,
        symbol: "basket.fill",
        status: .pending
      )
    case .highRisk:
      return DemoTransaction(
        merchant: "Orion Digital Exchange",
        category: "Electronics",
        amount: 1_849.00,
        location: "Lisbon, Portugal",
        date: date,
        symbol: "laptopcomputer",
        status: .pending
      )
    }
  }

  static func analysis(for scenario: DemoScenario) -> FraudAnalysis {
    switch scenario {
    case .lowRisk:
      return FraudAnalysis(
        score: 9,
        level: .low,
        headline: "Transaction approved",
        summary:
          "This purchase matches Maya's usual spending behavior and was approved automatically.",
        reasons: [
          RiskReason(
            title: "Recognized merchant",
            detail: "Purchase history shows regular visits to this merchant.",
            symbol: "checkmark.seal.fill"
          ),
          RiskReason(
            title: "Familiar location",
            detail: "The purchase is near Maya's typical activity area.",
            symbol: "location.fill"
          ),
        ]
      )
    case .highRisk:
      return FraudAnalysis(
        score: 87,
        level: .high,
        headline: "Verification required",
        summary: "This transaction differs significantly from Maya's normal purchase patterns.",
        reasons: [
          RiskReason(
            title: "Unusual location",
            detail: "The purchase is far from recent account activity.",
            symbol: "location.slash.fill"
          ),
          RiskReason(
            title: "High purchase amount",
            detail: "The amount is substantially above typical card spending.",
            symbol: "arrow.up.right.circle.fill"
          ),
          RiskReason(
            title: "New merchant",
            detail: "There is no prior account history with this merchant.",
            symbol: "building.2.crop.circle.fill"
          ),
        ]
      )
    }
  }
}
