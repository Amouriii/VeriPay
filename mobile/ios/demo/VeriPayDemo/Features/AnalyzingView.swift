import SwiftUI

struct AnalyzingView: View {
  @EnvironmentObject private var store: DemoStore
  @State private var isScanning = false
  @State private var pulse = false

  var body: some View {
    VStack(spacing: 0) {
      DemoTopBar(title: "Transaction analysis", onReset: store.resetDemo)
        .padding(.horizontal, 20)
        .padding(.top, 12)

      Spacer()

      VStack(spacing: 28) {
        scanner

        VStack(spacing: 9) {
          Text("Analyzing transaction…")
            .font(.system(size: 27, weight: .bold, design: .rounded))
            .foregroundColor(VeriPayTheme.primaryText)
          Text("VeriPay is evaluating payment signals in real time.")
            .font(.system(size: 15, weight: .regular))
            .multilineTextAlignment(.center)
            .foregroundColor(VeriPayTheme.secondaryText)
            .padding(.horizontal, 28)
        }

        if let transaction = store.pendingTransaction {
          VStack(spacing: 14) {
            HStack {
              VStack(alignment: .leading, spacing: 4) {
                Text(transaction.merchant)
                  .font(.system(size: 16, weight: .semibold))
                  .foregroundColor(VeriPayTheme.primaryText)
                Text(transaction.location)
                  .font(.system(size: 13, weight: .medium))
                  .foregroundColor(VeriPayTheme.secondaryText)
              }
              Spacer()
              Text(transaction.amountText)
                .font(.system(size: 20, weight: .bold, design: .rounded))
                .foregroundColor(VeriPayTheme.primaryText)
            }

            Divider()

            VStack(spacing: 12) {
              analysisStep("Payment context", symbol: "creditcard.fill", delay: 0)
              analysisStep("Spending behavior", symbol: "waveform.path.ecg", delay: 0.15)
              analysisStep("Location signals", symbol: "location.fill", delay: 0.3)
            }
          }
          .veriPayCard()
          .padding(.horizontal, 20)
        }
      }

      Spacer()

      HStack(spacing: 7) {
        Image(systemName: "lock.shield.fill")
        Text("Local presentation simulation")
      }
      .font(.system(size: 12, weight: .semibold))
      .foregroundColor(VeriPayTheme.secondaryText)
      .padding(.bottom, 24)
    }
    .background(VeriPayTheme.background.ignoresSafeArea())
    .onAppear {
      isScanning = true
      pulse = true
    }
  }

  private var scanner: some View {
    ZStack {
      Circle()
        .fill(VeriPayTheme.indigo.opacity(pulse ? 0.05 : 0.13))
        .frame(width: pulse ? 210 : 175, height: pulse ? 210 : 175)
        .animation(.easeInOut(duration: 1.15).repeatForever(autoreverses: true), value: pulse)

      Circle()
        .stroke(VeriPayTheme.indigo.opacity(0.12), lineWidth: 12)
        .frame(width: 142, height: 142)

      Circle()
        .trim(from: 0.03, to: 0.66)
        .stroke(
          VeriPayTheme.brandGradient,
          style: StrokeStyle(lineWidth: 12, lineCap: .round)
        )
        .frame(width: 142, height: 142)
        .rotationEffect(.degrees(isScanning ? 360 : 0))
        .animation(.linear(duration: 1.15).repeatForever(autoreverses: false), value: isScanning)

      ZStack {
        Circle().fill(VeriPayTheme.surface)
        Image(systemName: "checkmark.shield.fill")
          .font(.system(size: 40, weight: .semibold))
          .foregroundStyle(VeriPayTheme.brandGradient)
      }
      .frame(width: 94, height: 94)
      .shadow(color: VeriPayTheme.indigo.opacity(0.14), radius: 18, y: 8)
    }
    .frame(height: 210)
    .accessibilityLabel("Analyzing transaction")
  }

  private func analysisStep(_ title: String, symbol: String, delay: Double) -> some View {
    HStack(spacing: 12) {
      Image(systemName: symbol)
        .font(.system(size: 14, weight: .semibold))
        .foregroundColor(VeriPayTheme.indigo)
        .frame(width: 28, height: 28)
        .background(VeriPayTheme.indigo.opacity(0.1))
        .clipShape(Circle())
      Text(title)
        .font(.system(size: 14, weight: .medium))
        .foregroundColor(VeriPayTheme.primaryText)
      Spacer()
      ProgressView()
        .progressViewStyle(CircularProgressViewStyle(tint: VeriPayTheme.indigo))
        .scaleEffect(0.75)
    }
    .opacity(isScanning ? 1 : 0)
    .animation(.easeOut(duration: 0.35).delay(delay), value: isScanning)
  }
}
