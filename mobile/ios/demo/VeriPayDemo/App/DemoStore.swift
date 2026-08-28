import SwiftUI

@MainActor
final class DemoStore: ObservableObject {
  @Published var route: DemoRoute = .welcome
  @Published var recentTransactions = MockBankingService.recentTransactions()
  @Published private(set) var pendingTransaction: DemoTransaction?
  @Published private(set) var activeAnalysis: FraudAnalysis?

  let account = MockBankingService.account

  private var activeScenario: DemoScenario?
  private var analysisTask: Task<Void, Never>?
  private var pendingWasRecorded = false

  func signIn() {
    withAnimation(.spring(response: 0.55, dampingFraction: 0.86)) {
      route = .dashboard
    }
  }

  func signOut() {
    resetState(route: .welcome)
  }

  func start(_ scenario: DemoScenario) {
    analysisTask?.cancel()
    activeScenario = scenario
    pendingTransaction = MockBankingService.transaction(for: scenario)
    activeAnalysis = nil
    pendingWasRecorded = false

    withAnimation(.easeInOut(duration: 0.35)) {
      route = .analyzing
    }

    analysisTask = Task { [weak self] in
      try? await Task.sleep(nanoseconds: 2_350_000_000)
      guard !Task.isCancelled, let self, let scenario = self.activeScenario else { return }
      self.completeAnalysis(scenario)
    }
  }

  func reviewTransaction() {
    withAnimation(.spring(response: 0.5, dampingFraction: 0.88)) {
      route = .verification
    }
  }

  func approveTransaction() {
    recordPendingTransaction(as: .approved)
    withAnimation(.spring(response: 0.5, dampingFraction: 0.86)) {
      route = .approved
    }
  }

  func denyTransaction() {
    recordPendingTransaction(as: .blocked)
    withAnimation(.spring(response: 0.5, dampingFraction: 0.86)) {
      route = .blocked
    }
  }

  func returnToDashboard() {
    analysisTask?.cancel()
    pendingTransaction = nil
    activeAnalysis = nil
    activeScenario = nil
    pendingWasRecorded = false
    withAnimation(.spring(response: 0.5, dampingFraction: 0.9)) {
      route = .dashboard
    }
  }

  func resetDemo() {
    recentTransactions = MockBankingService.recentTransactions()
    resetState(route: .dashboard)
  }

  private func completeAnalysis(_ scenario: DemoScenario) {
    activeAnalysis = MockBankingService.analysis(for: scenario)
    if scenario == .lowRisk {
      recordPendingTransaction(as: .approved)
    }
    withAnimation(.spring(response: 0.55, dampingFraction: 0.9)) {
      route = .analysisResult
    }
  }

  private func recordPendingTransaction(as status: DemoTransaction.Status) {
    guard !pendingWasRecorded, var transaction = pendingTransaction else { return }
    transaction.status = status
    recentTransactions.insert(transaction, at: 0)
    pendingTransaction = transaction
    pendingWasRecorded = true
  }

  private func resetState(route destination: DemoRoute) {
    analysisTask?.cancel()
    analysisTask = nil
    activeScenario = nil
    pendingTransaction = nil
    activeAnalysis = nil
    pendingWasRecorded = false
    withAnimation(.spring(response: 0.5, dampingFraction: 0.9)) {
      route = destination
    }
  }
}
