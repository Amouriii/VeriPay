import Foundation

enum MockBankingService {
  static let personalAccount = DemoAccount(
    customerName: "Maya Bennett", firstName: "Maya", balance: 12_846.72,
    availableCredit: 8_420.00, cardLastFour: "4821", type: .personal,
    biometricMethod: .faceID, businessName: nil
  )
  static let businessAccount = DemoAccount(
    customerName: "Jordan Lee", firstName: "Jordan", balance: 84_210.45,
    availableCredit: 35_000.00, cardLastFour: "7306", type: .business,
    biometricMethod: .touchID, businessName: "Northstar Studio LLC"
  )

  static func recentTransactions(for account: DemoAccount, referenceDate: Date = Date()) -> [DemoTransaction] {
    let business = account.type == .business
    return [
      DemoTransaction(merchant: business ? "Harbor Office Supply" : "Lumen Coffee Roasters", category: business ? "Operations" : "Dining", amount: business ? 284.50 : 8.75, location: business ? "New York, NY" : "Brooklyn, NY", date: referenceDate.addingTimeInterval(-3_600), symbol: business ? "shippingbox.fill" : "cup.and.saucer.fill", status: .completed),
      DemoTransaction(merchant: business ? "Cloudline Hosting" : "Northstar Market", category: business ? "Software" : "Groceries", amount: business ? 149.00 : 64.28, location: "New York, NY", date: referenceDate.addingTimeInterval(-86_400), symbol: business ? "cloud.fill" : "basket.fill", status: .completed),
      DemoTransaction(merchant: business ? "Metro Payroll" : "Metro Transit", category: business ? "Payroll" : "Transportation", amount: business ? 2_450.00 : 33.00, location: "New York, NY", date: referenceDate.addingTimeInterval(-172_800), symbol: business ? "person.3.fill" : "tram.fill", status: .completed),
    ]
  }

  static func transaction(for scenario: DemoScenario, account: DemoAccount, date: Date = Date()) -> DemoTransaction {
    switch scenario {
    case .lowRisk:
      return DemoTransaction(merchant: account.type == .business ? "Cloudline Hosting" : "Northstar Market", category: account.type == .business ? "Software" : "Groceries", amount: account.type == .business ? 249.00 : 42.18, location: "New York, NY", date: date, symbol: account.type == .business ? "cloud.fill" : "basket.fill", status: .pending)
    case .highRisk:
      return DemoTransaction(merchant: "Orion Digital Exchange", category: "Electronics", amount: 1_849.00, location: "Lisbon, Portugal", date: date, symbol: "laptopcomputer", status: .pending)
    }
  }

  static func analysis(for scenario: DemoScenario, account: DemoAccount) -> FraudAnalysis {
    switch scenario {
    case .lowRisk:
      return FraudAnalysis(score: 9, level: .low, headline: "Transaction approved", summary: "This purchase matches the usual spending behavior for this demo account and was approved automatically.", reasons: [RiskReason(title: "Recognized merchant", detail: "Purchase history shows regular activity with this merchant.", symbol: "checkmark.seal.fill"), RiskReason(title: "Familiar location", detail: "The purchase matches the account's typical activity area.", symbol: "location.fill")])
    case .highRisk:
      return FraudAnalysis(score: 87, level: .high, headline: "Verification required", summary: "This transaction differs significantly from the normal purchase patterns for this demo account.", reasons: [RiskReason(title: "Unusual location", detail: "The purchase is far from recent account activity.", symbol: "location.slash.fill"), RiskReason(title: "High purchase amount", detail: "The amount is substantially above typical spending.", symbol: "arrow.up.right.circle.fill"), RiskReason(title: "New merchant", detail: "There is no prior account history with this merchant.", symbol: "building.2.crop.circle.fill")])
    }
  }
}
