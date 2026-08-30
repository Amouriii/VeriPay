import SwiftUI

struct DashboardView: View {
  @EnvironmentObject private var store: DemoStore
  @State private var showScenarioPicker = false
  @State private var appeared = false

  var body: some View {
    ZStack {
      VeriPayTheme.background.ignoresSafeArea()

      ScrollView(showsIndicators: false) {
        VStack(spacing: 24) {
          header
          balanceCard
          paymentCard
          activitySection
          Color.clear.frame(height: 92)
        }
        .padding(.horizontal, 20)
        .padding(.top, 12)
        .opacity(appeared ? 1 : 0)
        .offset(y: appeared ? 0 : 10)
      }
    }
    .safeAreaInset(edge: .bottom) {
      PrimaryActionButton("Simulate New Transaction", symbol: "wave.3.right.circle.fill") {
        showScenarioPicker = true
      }
      .padding(.horizontal, 20)
      .padding(.top, 12)
      .padding(.bottom, 8)
      .background(.ultraThinMaterial)
    }
    .confirmationDialog(
      "Choose a transaction scenario",
      isPresented: $showScenarioPicker,
      titleVisibility: .visible
    ) {
      Button("Everyday purchase — Low risk") {
        store.start(.lowRisk)
      }
      Button("Unusual purchase — High risk") {
        store.start(.highRisk)
      }
      Button("Cancel", role: .cancel) {}
    } message: {
      Text("Fictional transaction data; risk analysis is scored live by the VeriPay analyst service when reachable, otherwise local mocks.")
    }
    .onAppear {
      withAnimation(.easeOut(duration: 0.45)) {
        appeared = true
      }
    }
  }

  private var header: some View {
    HStack(alignment: .center) {
      VStack(alignment: .leading, spacing: 4) {
        Text("Good morning,")
          .font(.system(size: 14, weight: .medium))
          .foregroundColor(VeriPayTheme.secondaryText)
        Text(store.account.firstName)
          .font(.system(size: 27, weight: .bold, design: .rounded))
          .foregroundColor(VeriPayTheme.primaryText)
      }

      Spacer()

      Button(action: store.resetDemo) {
        ZStack {
          Circle().fill(VeriPayTheme.surface)
          Image(systemName: "arrow.counterclockwise")
            .font(.system(size: 16, weight: .semibold))
            .foregroundColor(VeriPayTheme.indigo)
        }
        .frame(width: 44, height: 44)
        .shadow(color: Color.black.opacity(0.05), radius: 8, y: 4)
      }
      .buttonStyle(ScaleButtonStyle())
      .accessibilityLabel("Reset demo")

      ZStack {
        Circle().fill(VeriPayTheme.brandGradient)
        Text("MB")
          .font(.system(size: 14, weight: .bold, design: .rounded))
          .foregroundColor(.white)
      }
      .frame(width: 44, height: 44)
      .padding(.leading, 8)
      .accessibilityLabel("Profile for \(store.account.customerName)")
    }
  }

  private var balanceCard: some View {
    VStack(alignment: .leading, spacing: 16) {
      HStack {
        VStack(alignment: .leading, spacing: 7) {
          Text("TOTAL BALANCE")
            .font(.system(size: 11, weight: .bold, design: .rounded))
            .tracking(1.2)
            .foregroundColor(VeriPayTheme.secondaryText)
          Text(store.account.balance.formattedCurrency)
            .font(.system(size: 35, weight: .bold, design: .rounded))
            .foregroundColor(VeriPayTheme.primaryText)
        }
        Spacer()
        ZStack {
          Circle().fill(VeriPayTheme.success.opacity(0.12))
          Image(systemName: "chart.line.uptrend.xyaxis")
            .font(.system(size: 18, weight: .semibold))
            .foregroundColor(VeriPayTheme.success)
        }
        .frame(width: 48, height: 48)
      }

      HStack(spacing: 6) {
        Image(systemName: "checkmark.shield.fill")
          .foregroundColor(VeriPayTheme.success)
        Text("Accounts protected")
          .font(.system(size: 13, weight: .semibold))
          .foregroundColor(VeriPayTheme.secondaryText)
      }
    }
    .veriPayCard()
  }

  private var paymentCard: some View {
    ZStack {
      RoundedRectangle(cornerRadius: 26, style: .continuous)
        .fill(VeriPayTheme.cardGradient)
        .shadow(color: VeriPayTheme.indigo.opacity(0.28), radius: 20, x: 0, y: 12)

      Circle()
        .fill(Color.white.opacity(0.08))
        .frame(width: 190, height: 190)
        .offset(x: 135, y: -72)

      Circle()
        .stroke(Color.white.opacity(0.08), lineWidth: 28)
        .frame(width: 150, height: 150)
        .offset(x: -150, y: 95)

      VStack(alignment: .leading) {
        HStack {
          Text("VERIPAY")
            .font(.system(size: 14, weight: .bold, design: .rounded))
            .tracking(1.5)
          Spacer()
          Image(systemName: "wave.3.right")
            .font(.system(size: 22, weight: .medium))
        }
        Spacer()
        Image(systemName: "simcard.fill")
          .font(.system(size: 30))
          .foregroundColor(Color(red: 0.92, green: 0.78, blue: 0.38))
        Spacer()
        Text("••••  ••••  ••••  \(store.account.cardLastFour)")
          .font(.system(size: 20, weight: .semibold, design: .monospaced))
          .tracking(1.2)
        HStack {
          VStack(alignment: .leading, spacing: 3) {
            Text("CARDHOLDER")
              .font(.system(size: 8, weight: .bold))
              .opacity(0.65)
            Text(store.account.customerName.uppercased())
              .font(.system(size: 12, weight: .semibold))
          }
          Spacer()
          Text("VISA")
            .font(.system(size: 18, weight: .black, design: .rounded))
            .italic()
        }
      }
      .foregroundColor(.white)
      .padding(22)
    }
    .frame(height: 220)
    .clipped()
    .clipShape(RoundedRectangle(cornerRadius: 26, style: .continuous))
    .accessibilityElement(children: .combine)
    .accessibilityLabel("VeriPay card ending in \(store.account.cardLastFour)")
  }

  private var activitySection: some View {
    VStack(spacing: 14) {
      HStack {
        Text("Recent activity")
          .font(.system(size: 20, weight: .bold, design: .rounded))
          .foregroundColor(VeriPayTheme.primaryText)
        Spacer()
        Text("Fictional data")
          .font(.system(size: 11, weight: .semibold))
          .foregroundColor(VeriPayTheme.secondaryText)
      }

      VStack(spacing: 4) {
        ForEach(displayedTransactions.indices, id: \.self) { index in
          TransactionRow(transaction: displayedTransactions[index])
          if index < displayedTransactions.count - 1 {
            Divider().padding(.leading, 62)
          }
        }
      }
      .veriPayCard(padding: 16)
    }
  }

  private var displayedTransactions: [DemoTransaction] {
    Array(store.recentTransactions.prefix(5))
  }
}
