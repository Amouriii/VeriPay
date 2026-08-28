import SwiftUI

struct DecisionConfirmationView: View {
  enum Decision: Equatable {
    case approved
    case blocked
  }

  let decision: Decision

  @EnvironmentObject private var store: DemoStore
  @State private var iconScale: CGFloat = 0.65
  @State private var contentVisible = false

  var body: some View {
    ScrollView(showsIndicators: false) {
      VStack(spacing: 26) {
        HStack {
          PrototypePill()
          Spacer()
        }

        Spacer(minLength: 25)

        ZStack {
          Circle()
            .fill(tint.opacity(0.1))
            .frame(width: 150, height: 150)
          Circle()
            .fill(tint)
            .frame(width: 112, height: 112)
            .shadow(color: tint.opacity(0.3), radius: 20, y: 10)
          Image(systemName: decision == .approved ? "checkmark" : "lock.shield.fill")
            .font(.system(size: 46, weight: .bold))
            .foregroundColor(.white)
        }
        .scaleEffect(iconScale)

        VStack(spacing: 9) {
          Text(decision == .approved ? "Transaction Approved" : "Transaction Blocked")
            .font(.system(size: 29, weight: .bold, design: .rounded))
            .multilineTextAlignment(.center)
            .foregroundColor(VeriPayTheme.primaryText)
          Text(message)
            .font(.system(size: 15, weight: .regular))
            .multilineTextAlignment(.center)
            .foregroundColor(VeriPayTheme.secondaryText)
            .fixedSize(horizontal: false, vertical: true)
        }

        if let transaction = store.pendingTransaction {
          VStack(spacing: 15) {
            HStack {
              VStack(alignment: .leading, spacing: 5) {
                Text(transaction.merchant)
                  .font(.system(size: 16, weight: .semibold))
                  .foregroundColor(VeriPayTheme.primaryText)
                Text(transaction.fullDateText)
                  .font(.system(size: 12, weight: .medium))
                  .foregroundColor(VeriPayTheme.secondaryText)
              }
              Spacer()
              Text(transaction.amountText)
                .font(.system(size: 20, weight: .bold, design: .rounded))
                .foregroundColor(VeriPayTheme.primaryText)
            }

            Divider()

            HStack(spacing: 10) {
              Image(systemName: decision == .approved ? "checkmark.seal.fill" : "bell.badge.fill")
                .foregroundColor(tint)
              Text(securityNote)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(VeriPayTheme.secondaryText)
              Spacer()
            }
          }
          .veriPayCard()
        }

        if decision == .blocked {
          HStack(alignment: .top, spacing: 12) {
            Image(systemName: "shield.lefthalf.filled")
              .font(.system(size: 18, weight: .semibold))
              .foregroundColor(VeriPayTheme.indigo)
            VStack(alignment: .leading, spacing: 4) {
              Text("Security confirmation")
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(VeriPayTheme.primaryText)
              Text(
                "The mock card has been marked secure and the simulated merchant cannot retry this payment."
              )
              .font(.system(size: 13))
              .foregroundColor(VeriPayTheme.secondaryText)
              .fixedSize(horizontal: false, vertical: true)
            }
          }
          .veriPayCard(padding: 17)
        }

        Spacer(minLength: 8)

        PrimaryActionButton("Reset Demo", symbol: "arrow.counterclockwise") {
          store.resetDemo()
        }

        Text("This confirmation is entirely simulated")
          .font(.system(size: 11, weight: .medium))
          .foregroundColor(VeriPayTheme.secondaryText)
          .padding(.bottom, 24)
      }
      .padding(.horizontal, 20)
      .padding(.top, 12)
      .frame(maxWidth: .infinity)
      .opacity(contentVisible ? 1 : 0)
      .offset(y: contentVisible ? 0 : 12)
    }
    .background(VeriPayTheme.background.ignoresSafeArea())
    .onAppear {
      withAnimation(.spring(response: 0.58, dampingFraction: 0.68)) {
        iconScale = 1
      }
      withAnimation(.easeOut(duration: 0.48)) {
        contentVisible = true
      }
    }
  }

  private var tint: Color {
    decision == .approved ? VeriPayTheme.success : VeriPayTheme.danger
  }

  private var message: String {
    switch decision {
    case .approved:
      return
        "Thanks for confirming. The simulated purchase has been approved and added to recent activity."
    case .blocked:
      return
        "The simulated purchase was stopped. No funds were moved and the demo account remains protected."
    }
  }

  private var securityNote: String {
    switch decision {
    case .approved: return "Identity confirmed • Mock approval complete"
    case .blocked: return "Mock security alert created • Card protected"
    }
  }
}
