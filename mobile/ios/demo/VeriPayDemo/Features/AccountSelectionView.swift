import SwiftUI

struct AccountSelectionView: View {
  @EnvironmentObject private var store: DemoStore

  var body: some View {
    VStack(spacing: 24) {
      DemoTopBar(title: "Choose demo account", onBack: { store.route = .welcome })
      VStack(spacing: 8) {
        Text("Select an account")
          .font(.system(size: 30, weight: .bold, design: .rounded))
          .foregroundColor(VeriPayTheme.primaryText)
        Text("Test customer and business verification flows with fictional data.")
          .multilineTextAlignment(.center)
          .foregroundColor(VeriPayTheme.secondaryText)
      }
      ForEach(DemoAccountType.allCases) { type in
        Button { store.chooseAccount(type) } label: {
          HStack(spacing: 16) {
            Image(systemName: type.symbol).font(.system(size: 28)).foregroundColor(type == .personal ? VeriPayTheme.indigo : VeriPayTheme.steelBlue)
            VStack(alignment: .leading, spacing: 5) {
              Text(type.title).font(.system(size: 18, weight: .bold, design: .rounded))
              Text(type.subtitle).font(.system(size: 13)).foregroundColor(VeriPayTheme.secondaryText)
            }
            Spacer(); Image(systemName: "chevron.right").foregroundColor(VeriPayTheme.secondaryText)
          }
          .foregroundColor(VeriPayTheme.primaryText)
          .padding(20).background(VeriPayTheme.surface)
          .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
        }
      }
      Spacer()
    }
    .padding(20).background(VeriPayTheme.background.ignoresSafeArea())
  }
}
