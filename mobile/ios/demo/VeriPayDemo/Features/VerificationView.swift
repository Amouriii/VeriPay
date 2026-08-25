import SwiftUI

struct VerificationView: View {
  @EnvironmentObject private var store: DemoStore
  @State private var appeared = false

  var body: some View {
    Group {
      if let transaction = store.pendingTransaction, let analysis = store.activeAnalysis {
        verificationContent(transaction: transaction, analysis: analysis)
      } else {
        ProgressView()
      }
    }
    .background(VeriPayTheme.background.ignoresSafeArea())
    .onAppear {
      withAnimation(.easeOut(duration: 0.45)) {
        appeared = true
      }
    }
  }

  private func verificationContent(transaction: DemoTransaction, analysis: FraudAnalysis)
    -> some View
  {
    ScrollView(showsIndicators: false) {
      VStack(spacing: 22) {
        DemoTopBar(
          title: "Verify transaction",
          onBack: { store.route = .analysisResult },
          onReset: store.resetDemo
        )

        VStack(spacing: 12) {
          ZStack {
            Circle().fill(VeriPayTheme.danger.opacity(0.11))
            Image(systemName: "exclamationmark.shield.fill")
              .font(.system(size: 34, weight: .semibold))
              .foregroundColor(VeriPayTheme.danger)
          }
          .frame(width: 76, height: 76)

          Text("Do you recognize this purchase?")
            .font(.system(size: 25, weight: .bold, design: .rounded))
            .multilineTextAlignment(.center)
            .foregroundColor(VeriPayTheme.primaryText)
          Text("Your response protects the account and resolves this transaction immediately.")
            .font(.system(size: 14, weight: .regular))
            .multilineTextAlignment(.center)
            .foregroundColor(VeriPayTheme.secondaryText)
            .fixedSize(horizontal: false, vertical: true)
        }
        .padding(.horizontal, 12)

        VStack(spacing: 0) {
          detailRow("Merchant", value: transaction.merchant, symbol: "storefront.fill")
          Divider().padding(.leading, 45)
          detailRow("Amount", value: transaction.amountText, symbol: "dollarsign.circle.fill")
          Divider().padding(.leading, 45)
          detailRow("Location", value: transaction.location, symbol: "location.fill")
          Divider().padding(.leading, 45)
          detailRow("Date & time", value: transaction.fullDateText, symbol: "calendar")
          Divider().padding(.leading, 45)
          detailRow(
            "Risk score", value: "\(analysis.score)% · High", symbol: "gauge.high",
            valueTint: VeriPayTheme.danger)
        }
        .veriPayCard(padding: 16)

        VStack(alignment: .leading, spacing: 16) {
          HStack {
            Text("Why VeriPay flagged it")
              .font(.system(size: 18, weight: .bold, design: .rounded))
              .foregroundColor(VeriPayTheme.primaryText)
            Spacer()
            Text("\(analysis.reasons.count) SIGNALS")
              .font(.system(size: 10, weight: .bold, design: .rounded))
              .tracking(0.7)
              .foregroundColor(VeriPayTheme.danger)
          }

          ForEach(analysis.reasons) { reason in
            RiskReasonRow(reason: reason, tint: VeriPayTheme.danger)
          }
        }
        .veriPayCard()

        VStack(spacing: 12) {
          Button(action: store.approveTransaction) {
            Label("Approve Transaction", systemImage: "checkmark.circle.fill")
              .font(.system(size: 18, weight: .bold, design: .rounded))
              .foregroundColor(.white)
              .frame(maxWidth: .infinity)
              .frame(height: 60)
              .background(VeriPayTheme.success)
              .clipShape(RoundedRectangle(cornerRadius: 19, style: .continuous))
              .shadow(color: VeriPayTheme.success.opacity(0.24), radius: 14, y: 8)
          }
          .buttonStyle(ScaleButtonStyle())

          Button(action: store.denyTransaction) {
            Label("Deny Transaction", systemImage: "xmark.octagon.fill")
              .font(.system(size: 18, weight: .bold, design: .rounded))
              .foregroundColor(VeriPayTheme.danger)
              .frame(maxWidth: .infinity)
              .frame(height: 60)
              .background(VeriPayTheme.danger.opacity(0.1))
              .overlay(
                RoundedRectangle(cornerRadius: 19, style: .continuous)
                  .stroke(VeriPayTheme.danger.opacity(0.22), lineWidth: 1)
              )
              .clipShape(RoundedRectangle(cornerRadius: 19, style: .continuous))
          }
          .buttonStyle(ScaleButtonStyle())

          Text("Presentation only • No real account action occurs")
            .font(.system(size: 11, weight: .medium))
            .foregroundColor(VeriPayTheme.secondaryText)
            .padding(.top, 4)
        }
        .padding(.bottom, 24)
      }
      .padding(.horizontal, 20)
      .padding(.top, 12)
      .opacity(appeared ? 1 : 0)
      .offset(y: appeared ? 0 : 10)
    }
  }

  private func detailRow(
    _ label: String,
    value: String,
    symbol: String,
    valueTint: Color = VeriPayTheme.primaryText
  ) -> some View {
    HStack(spacing: 12) {
      Image(systemName: symbol)
        .font(.system(size: 15, weight: .semibold))
        .foregroundColor(VeriPayTheme.indigo)
        .frame(width: 32, height: 32)
        .background(VeriPayTheme.indigo.opacity(0.09))
        .clipShape(Circle())

      Text(label)
        .font(.system(size: 13, weight: .medium))
        .foregroundColor(VeriPayTheme.secondaryText)
      Spacer(minLength: 12)
      Text(value)
        .font(.system(size: 14, weight: .semibold, design: .rounded))
        .foregroundColor(valueTint)
        .multilineTextAlignment(.trailing)
        .lineLimit(2)
    }
    .padding(.vertical, 10)
    .accessibilityElement(children: .combine)
  }
}
