import SwiftUI

enum VeriPayTheme {
  static let indigo = Color(red: 0.24, green: 0.23, blue: 0.86)
  static let violet = Color(red: 0.49, green: 0.31, blue: 0.96)
  static let cyan = Color(red: 0.18, green: 0.78, blue: 0.86)
  static let success = Color(red: 0.10, green: 0.66, blue: 0.43)
  static let warning = Color(red: 0.95, green: 0.57, blue: 0.18)
  static let danger = Color(red: 0.91, green: 0.24, blue: 0.33)

  static let background = Color(
    UIColor { traits in
      traits.userInterfaceStyle == .dark
        ? UIColor(red: 0.035, green: 0.045, blue: 0.085, alpha: 1)
        : UIColor(red: 0.958, green: 0.969, blue: 0.992, alpha: 1)
    }
  )

  static let surface = Color(
    UIColor { traits in
      traits.userInterfaceStyle == .dark
        ? UIColor(red: 0.075, green: 0.09, blue: 0.15, alpha: 1)
        : UIColor.white
    }
  )

  static let secondarySurface = Color(
    UIColor { traits in
      traits.userInterfaceStyle == .dark
        ? UIColor(red: 0.105, green: 0.12, blue: 0.19, alpha: 1)
        : UIColor(red: 0.925, green: 0.94, blue: 0.975, alpha: 1)
    }
  )

  static let primaryText = Color(
    UIColor { traits in
      traits.userInterfaceStyle == .dark
        ? UIColor.white
        : UIColor(red: 0.055, green: 0.07, blue: 0.13, alpha: 1)
    }
  )

  static let secondaryText = Color(
    UIColor { traits in
      traits.userInterfaceStyle == .dark
        ? UIColor(red: 0.68, green: 0.71, blue: 0.79, alpha: 1)
        : UIColor(red: 0.37, green: 0.40, blue: 0.48, alpha: 1)
    }
  )

  static let cardGradient = LinearGradient(
    colors: [Color(red: 0.10, green: 0.12, blue: 0.29), indigo, violet],
    startPoint: .topLeading,
    endPoint: .bottomTrailing
  )

  static let brandGradient = LinearGradient(
    colors: [indigo, violet],
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
