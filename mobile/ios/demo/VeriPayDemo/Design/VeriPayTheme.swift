import SwiftUI

enum VeriPayTheme {
  // Product palette: institutional surfaces with role-specific accents.
  static let obsidian = Color(red: 0.043, green: 0.075, blue: 0.122)
  static let polarWhite = Color(red: 0.980, green: 0.980, blue: 0.988)
  static let coolGray = Color(red: 0.941, green: 0.953, blue: 0.969)
  static let charcoal = Color(red: 0.200, green: 0.227, blue: 0.282)
  static let indigo = Color(red: 0.310, green: 0.275, blue: 0.898)
  static let steelBlue = Color(red: 0.008, green: 0.518, blue: 0.780)
  static let violet = indigo
  static let cyan = steelBlue
  static let success = Color(red: 0.10, green: 0.66, blue: 0.43)
  static let warning = Color(red: 0.95, green: 0.57, blue: 0.18)
  static let danger = Color(red: 0.91, green: 0.24, blue: 0.33)

  static let background = polarWhite
  static let surface = polarWhite
  static let secondarySurface = coolGray
  static let primaryText = charcoal
  static let secondaryText = Color(red: 0.290, green: 0.322, blue: 0.388)

  static let cardGradient = LinearGradient(
    colors: [obsidian, indigo, steelBlue],
    startPoint: .topLeading,
    endPoint: .bottomTrailing
  )

  static let brandGradient = LinearGradient(
    colors: [indigo, steelBlue],
    startPoint: .leading,
    endPoint: .trailing
  )
}

extension View {
  func veriPayCard(padding: CGFloat = 20) -> some View {
    self
      .padding(padding)
      .background(VeriPayTheme.surface)
      .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
      .shadow(color: Color.black.opacity(0.06), radius: 18, x: 0, y: 8)
  }
}
