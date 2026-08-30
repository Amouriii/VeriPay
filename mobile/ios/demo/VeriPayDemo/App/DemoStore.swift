import SwiftUI

@MainActor
final class DemoStore: ObservableObject {
  @Published var route: DemoRoute = .welcome
  @Published var recentTransactions: [DemoTransaction] = []
  @Published private(set) var pendingTransaction: DemoTransaction?
  @Published private(set) var activeAnalysis: FraudAnalysis?
  @Published private(set) var selectedAccount: DemoAccount?
  @Published private(set) var biometricMessage = ""

  var account: DemoAccount { selectedAccount ?? MockBankingService.personalAccount }
  private var activeScenario: DemoScenario?
  private var analysisTask: Task<Void, Never>?
  private var pendingWasRecorded = false

  func chooseAccount(_ type: DemoAccountType) {
    selectedAccount = type == .personal ? MockBankingService.personalAccount : MockBankingService.businessAccount
    biometricMessage = ""
    withAnimation(.spring(response: 0.5, dampingFraction: 0.86)) { route = .biometric }
  }

  func authenticateBiometric() {
    biometricMessage = "Biometric match confirmed for demo testing."
    withAnimation(.spring(response: 0.5, dampingFraction: 0.86)) {
      recentTransactions = MockBankingService.recentTransactions(for: account)
      route = .dashboard
    }
  }

  func signIn() { route = .accountSelection }
  func signOut() { resetState(route: .welcome) }

  func start(_ scenario: DemoScenario) {
    analysisTask?.cancel(); activeScenario = scenario
    pendingTransaction = MockBankingService.transaction(for: scenario, account: account)
    activeAnalysis = nil; pendingWasRecorded = false
    withAnimation(.easeInOut(duration: 0.35)) { route = .analyzing }
    analysisTask = Task { [weak self] in
      try? await Task.sleep(nanoseconds: 2_350_000_000)
      guard !Task.isCancelled, let self, let scenario = self.activeScenario else { return }
      self.completeAnalysis(scenario)
    }
  }

  func reviewTransaction() { route = .biometric }
  func approveTransaction() { recordPendingTransaction(as: .approved); route = .approved }
  func denyTransaction() { recordPendingTransaction(as: .blocked); route = .blocked }
  func returnToDashboard() { resetState(route: .dashboard) }
  func resetDemo() { recentTransactions = MockBankingService.recentTransactions(for: account); resetState(route: .dashboard) }

  private func completeAnalysis(_ scenario: DemoScenario) {
    activeAnalysis = MockBankingService.analysis(for: scenario, account: account)
    if scenario == .lowRisk { recordPendingTransaction(as: .approved) }
    withAnimation(.spring(response: 0.55, dampingFraction: 0.9)) { route = .analysisResult }
  }

  private func recordPendingTransaction(as status: DemoTransaction.Status) {
    guard !pendingWasRecorded, var transaction = pendingTransaction else { return }
    transaction.status = status; recentTransactions.insert(transaction, at: 0)
    pendingTransaction = transaction; pendingWasRecorded = true
  }

  private func resetState(route destination: DemoRoute) {
    analysisTask?.cancel(); analysisTask = nil; activeScenario = nil
    pendingTransaction = nil; activeAnalysis = nil; pendingWasRecorded = false; biometricMessage = ""
    withAnimation(.spring(response: 0.5, dampingFraction: 0.9)) { route = destination }
  }
}
