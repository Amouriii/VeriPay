import SwiftUI

@MainActor
final class DemoStore: ObservableObject {
  @Published var route: DemoRoute = .welcome
  @Published var recentTransactions: [DemoTransaction] = []
  @Published private(set) var pendingTransaction: DemoTransaction?
  @Published private(set) var activeAnalysis: FraudAnalysis?
  @Published private(set) var selectedAccount: DemoAccount?
  @Published private(set) var biometricMessage = ""
  /// True when the last analysis came from the live analyst_api instead of mocks.
  @Published private(set) var usingLiveRisk = false

  var account: DemoAccount { selectedAccount ?? MockBankingService.personalAccount }
  private var activeScenario: DemoScenario?
  private var analysisTask: Task<Void, Never>?
  private var pendingWasRecorded = false
  /// True when the biometric prompt is a high-risk review instead of a sign-in.
  private var reviewing = false

  func chooseAccount(_ type: DemoAccountType) {
    selectedAccount = type == .personal ? MockBankingService.personalAccount : MockBankingService.businessAccount
    biometricMessage = ""
    withAnimation(.spring(response: 0.5, dampingFraction: 0.86)) { route = .biometric }
  }

  func authenticateBiometric() {
    biometricMessage = "Biometric match confirmed for demo testing."
    let continueReview = reviewing
    reviewing = false
    withAnimation(.spring(response: 0.5, dampingFraction: 0.86)) {
      recentTransactions = MockBankingService.recentTransactions(for: account)
      route = continueReview ? .verification : .dashboard
    }
  }

  func signIn() { route = .accountSelection }
  func signOut() { resetState(route: .welcome) }

  func start(_ scenario: DemoScenario) {
    analysisTask?.cancel()
    activeScenario = scenario
    pendingTransaction = MockBankingService.transaction(for: scenario, account: account)
    activeAnalysis = nil
    usingLiveRisk = false
    pendingWasRecorded = false
    let transaction = pendingTransaction
    withAnimation(.easeInOut(duration: 0.35)) { route = .analyzing }

    analysisTask = Task { [weak self] in
      guard let transaction else { return }
      // Resolve the live analyst score while the analyzing moment is shown.
      async let fetched: FraudAnalysis? = LiveRiskService.evaluate(
        scenario: scenario, transaction: transaction
      )
      try? await Task.sleep(nanoseconds: 1_800_000_000)
      let liveAnalysis = await fetched
      guard !Task.isCancelled, let self, self.activeScenario == scenario else { return }
      self.completeAnalysis(scenario, liveAnalysis: liveAnalysis)
    }
  }

  func reviewTransaction() { reviewing = true; route = .biometric }
  func approveTransaction() { recordPendingTransaction(as: .approved); route = .approved }
  func denyTransaction() { recordPendingTransaction(as: .blocked); route = .blocked }
  func returnToDashboard() { resetState(route: .dashboard) }
  func resetDemo() { recentTransactions = MockBankingService.recentTransactions(for: account); resetState(route: .dashboard) }

  private func completeAnalysis(_ scenario: DemoScenario, liveAnalysis: FraudAnalysis?) {
    usingLiveRisk = liveAnalysis != nil
    activeAnalysis = liveAnalysis ?? MockBankingService.analysis(for: scenario, account: account)
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
    pendingTransaction = nil; activeAnalysis = nil; pendingWasRecorded = false
    reviewing = false
    usingLiveRisk = false; biometricMessage = ""
    withAnimation(.spring(response: 0.5, dampingFraction: 0.9)) { route = destination }
  }
}
