import SwiftUI

struct ContentView: View {
  @EnvironmentObject private var store: DemoStore

  var body: some View {
    ZStack {
      VeriPayTheme.background.ignoresSafeArea()

      Group {
        switch store.route {
        case .welcome:
          WelcomeView()
        case .accountSelection:
          AccountSelectionView()
        case .biometric:
          BiometricView()
        case .dashboard:
          DashboardView()
        case .analyzing:
          AnalyzingView()
        case .analysisResult:
          AnalysisResultView()
        case .verification:
          VerificationView()
        case .approved:
          DecisionConfirmationView(decision: .approved)
        case .blocked:
          DecisionConfirmationView(decision: .blocked)
        }
      }
      .id(routeIdentifier)
      .transition(
        .asymmetric(
          insertion: .opacity.combined(with: .move(edge: .trailing)),
          removal: .opacity.combined(with: .scale(scale: 0.985))
        )
      )
    }
    .preferredColorScheme(nil)
  }

  private var routeIdentifier: String {
    switch store.route {
    case .welcome: return "welcome"
    case .accountSelection: return "accountSelection"
    case .biometric: return "biometric"
    case .dashboard: return "dashboard"
    case .analyzing: return "analyzing"
    case .analysisResult: return "analysisResult"
    case .verification: return "verification"
    case .approved: return "approved"
    case .blocked: return "blocked"
    }
  }
}
