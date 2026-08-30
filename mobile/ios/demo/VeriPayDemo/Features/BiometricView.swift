import SwiftUI

struct BiometricView: View {
  @EnvironmentObject private var store: DemoStore

  var body: some View {
    VStack(spacing: 26) {
      DemoTopBar(title: "Security check", onBack: { store.route = .accountSelection })
      Spacer()
      Image(systemName: store.account.biometricMethod.symbol)
        .font(.system(size: 72, weight: .medium))
        .foregroundColor(store.account.type == .personal ? VeriPayTheme.indigo : VeriPayTheme.steelBlue)
        .padding(30)
        .background((store.account.type == .personal ? VeriPayTheme.indigo : VeriPayTheme.steelBlue).opacity(0.1))
        .clipShape(Circle())
      Text("Verify with \(store.account.biometricMethod.rawValue)")
        .font(.system(size: 27, weight: .bold, design: .rounded))
        .foregroundColor(VeriPayTheme.primaryText)
      Text("This is a simulated biometric prompt. No biometric data leaves the device.")
        .multilineTextAlignment(.center).foregroundColor(VeriPayTheme.secondaryText)
      PrimaryActionButton("Use \(store.account.biometricMethod.rawValue)", symbol: "checkmark.shield.fill") {
        store.authenticateBiometric()
      }
      if !store.biometricMessage.isEmpty {
        Label(store.biometricMessage, systemImage: "checkmark.circle.fill")
          .font(.system(size: 13, weight: .semibold)).foregroundColor(VeriPayTheme.success)
          .multilineTextAlignment(.center)
      }
      Spacer()
    }
    .padding(20).background(VeriPayTheme.background.ignoresSafeArea())
  }
}
