import SwiftUI

struct AnalysisResultView: View {
  @EnvironmentObject private var store: DemoStore
  @State private var appeared = false

  var body: some View {
    Group {
      if let analysis = store.activeAnalysis, let transaction = store.pendingTransaction {
        content(analysis: analysis, transaction: transaction)
      } else {
        ProgressView()
      }
    }
    .background(VeriPayTheme.background.ignoresSafeArea())
    .onAppear {
      withAnimation(.easeOut(duration: 0.5)) {
        appeared = true
      }
    }
  }

  private func content(analysis: FraudAnalysis, transaction: DemoTransaction) -> some View {
    let isLowRisk = analysis.level == .low
    let tint = isLowRisk ? VeriPayTheme.success : VeriPayTheme.danger

    return ScrollView(showsIndicators: false) {
      VStack(spacing: 22) {
        DemoTopBar(title: "Fraud analysis", onReset: store.resetDemo)

        VStack(spacing: 18) {
          RiskGauge(score: analysis.score, level: analysis.level)

          VStack(spacing: 7) {
            Label(
              isLowRisk ? "LOW RISK" : "HIGH RISK",
              systemImage: isLowRisk ? "checkmark.seal.fill" : "exclamationmark.shield.fill"
            )
            .font(.system(size: 11, weight: .bold, design: .rounded))
            .tracking(1)
            .foregroundColor(tint)

            Text(analysis.headline)
              .font(.system(size: 28, weight: .bold, design: .rounded))
              .multilineTextAlignment(.center)
              .foregroundColor(VeriPayTheme.primaryText)

            Text(analysis.summary)
              .font(.system(size: 15, weight: .regular))
              .multilineTextAlignment(.center)
              .foregroundColor(VeriPayTheme.secondaryText)
              .fixedSize(horizontal: false, vertical: true)
          }
        }
        .padding(.top, 8)

        transactionSummary(transaction, tint: tint)

        VStack(alignment: .leading, spacing: 17) {
          Text(isLowRisk ? "Why it looks safe" : "Why it was flagged")
            .font(.system(size: 18, weight: .bold, design: .rounded))
            .foregroundColor(VeriPayTheme.primaryText)

          ForEach(analysis.reasons) { reason in
            RiskReasonRow(reason: reason, tint: tint)
          }
        }
        .veriPayCard()

        if isLowRisk {
          PrimaryActionButton("Return to Dashboard", symbol: "arrow.right") {
            store.returnToDashboard()
          }
        } else {
          PrimaryActionButton("Review Transaction", symbol: "arrow.right") {
            store.reviewTransaction()
          }
          SecondaryActionButton("Reset Demo", symbol: "arrow.counterclockwise") {
            store.resetDemo()
          }
        }

        Text("Simulated analysis • No payment was processed")
          .font(.system(size: 11, weight: .medium))
          .foregroundColor(VeriPayTheme.secondaryText)
          .padding(.bottom, 22)
      }
      .padding(.horizontal, 20)
      .padding(.top, 12)
      .opacity(appeared ? 1 : 0)
      .offset(y: appeared ? 0 : 10)
    }
  }

  private func transactionSummary(_ transaction: DemoTransaction, tint: Color) -> some View {
    HStack(spacing: 14) {
      ZStack {
        RoundedRectangle(cornerRadius: 16, style: .continuous)
          .fill(tint.opacity(0.11))
        Image(systemName: transaction.symbol)
          .font(.system(size: 21, weight: .semibold))
          .foregroundColor(tint)
      }
      .frame(width: 54, height: 54)

      VStack(alignment: .leading, spacing: 5) {
        Text(transaction.merchant)
          .font(.system(size: 15, weight: .semibold))
          .foregroundColor(VeriPayTheme.primaryText)
          .lineLimit(1)
        Text(transaction.location)
          .font(.system(size: 12, weight: .medium))
          .foregroundColor(VeriPayTheme.secondaryText)
      }
      Spacer(minLength: 6)
      Text(transaction.amountText)
        .font(.system(size: 19, weight: .bold, design: .rounded))
        .foregroundColor(VeriPayTheme.primaryText)
    }
    .veriPayCard(padding: 16)
  }
}
