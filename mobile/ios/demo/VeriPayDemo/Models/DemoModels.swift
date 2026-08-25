import Foundation

struct DemoAccount {
  let customerName: String
  let firstName: String
  let balance: Decimal
  let availableCredit: Decimal
  let cardLastFour: String
}

struct DemoTransaction: Identifiable, Equatable {
  enum Status: Equatable {
    case completed
    case approved
    case blocked
    case pending
  }

  let id: UUID
  let merchant: String
  let category: String
  let amount: Decimal
  let location: String
  let date: Date
  let symbol: String
  var status: Status

  init(
    id: UUID = UUID(),
    merchant: String,
    category: String,
    amount: Decimal,
    location: String,
    date: Date,
    symbol: String,
    status: Status
  ) {
    self.id = id
    self.merchant = merchant
    self.category = category
    self.amount = amount
    self.location = location
    self.date = date
    self.symbol = symbol
    self.status = status
  }

  var amountText: String {
    amount.formattedCurrency
  }

  var shortDateText: String {
    Self.shortDateFormatter.string(from: date)
  }

  var fullDateText: String {
    Self.fullDateFormatter.string(from: date)
  }

  private static let shortDateFormatter: DateFormatter = {
    let formatter = DateFormatter()
    formatter.dateFormat = "MMM d"
    return formatter
  }()

  private static let fullDateFormatter: DateFormatter = {
    let formatter = DateFormatter()
    formatter.dateFormat = "MMM d, yyyy 'at' h:mm a"
    return formatter
  }()
}

struct RiskReason: Identifiable, Equatable {
  let id = UUID()
  let title: String
  let detail: String
  let symbol: String
}

struct FraudAnalysis: Equatable {
  let score: Int
  let level: RiskLevel
  let headline: String
  let summary: String
  let reasons: [RiskReason]

  enum RiskLevel: Equatable {
    case low
    case high
  }
}

enum DemoScenario: Equatable {
  case lowRisk
  case highRisk
}

enum DemoRoute {
  case welcome
  case dashboard
  case analyzing
  case analysisResult
  case verification
  case approved
  case blocked
}

extension Decimal {
  var formattedCurrency: String {
    let formatter = NumberFormatter()
    formatter.numberStyle = .currency
    formatter.currencyCode = "USD"
    formatter.locale = Locale(identifier: "en_US")
    return formatter.string(from: NSDecimalNumber(decimal: self)) ?? "$0.00"
  }
}
