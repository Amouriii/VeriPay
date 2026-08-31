import CoreImage
import CoreImage.CIFilterBuiltins
import SwiftUI
import UIKit

/// A QR code that opens a URL when scanned by a camera.
struct WebsiteQRCode: View {
  let urlString: String

  var body: some View {
    Button(action: openURL) {
      VStack(spacing: 12) {
        QRCodeImage(text: urlString)
          .frame(width: 128, height: 128)
          .padding(12)
          .background(VeriPayTheme.polarWhite)
          .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
          .shadow(color: Color.black.opacity(0.08), radius: 12, x: 0, y: 5)

        Text(urlString.replacingOccurrences(of: "https://", with: ""))
          .font(.system(size: 12, weight: .medium, design: .rounded))
          .foregroundColor(VeriPayTheme.secondaryText)
          .lineLimit(1)
      }
      .overlay(alignment: .topTrailing) {
        Image(systemName: "arrow.up.right.square")
          .font(.system(size: 13, weight: .bold))
          .foregroundColor(VeriPayTheme.indigo)
          .padding(12)
      }
    }
    .buttonStyle(ScaleButtonStyle())
    .accessibilityElement(children: .combine)
    .accessibilityLabel("Open \(urlString) in Safari")
  }

  private func openURL() {
    guard let url = URL(string: urlString) else { return }
    UIApplication.shared.open(url)
  }
}

private struct QRCodeImage: View {
  let text: String

  var body: some View {
    if let image = generateQRCode(from: text) {
      Image(uiImage: image)
        .resizable()
        .interpolation(.none)
        .scaledToFit()
    } else {
      Image(systemName: "qrcode")
        .font(.system(size: 60))
        .foregroundColor(VeriPayTheme.primaryText)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
  }

  private func generateQRCode(from string: String) -> UIImage? {
    let context = CIContext()
    let filter = CIFilter.qrCodeGenerator()
    filter.message = Data(string.utf8)
    filter.correctionLevel = "M"

    guard let output = filter.outputImage else { return nil }
    // Scale the small QR output up to a sharp, scan-friendly size.
    let scaled = output.transformed(by: CGAffineTransform(scaleX: 10, y: 10))
    guard let cgImage = context.createCGImage(scaled, from: scaled.extent) else { return nil }
    return UIImage(cgImage: cgImage)
  }
}

struct BrandMark: View {
  var compact = false

  var body: some View {
    HStack(spacing: compact ? 9 : 12) {
      ZStack {
        RoundedRectangle(cornerRadius: compact ? 10 : 14, style: .continuous)
          .fill(VeriPayTheme.brandGradient)
        Image(systemName: "checkmark.shield.fill")
          .font(.system(size: compact ? 17 : 23, weight: .semibold))
          .foregroundColor(.white)
      }
      .frame(width: compact ? 38 : 50, height: compact ? 38 : 50)
      .shadow(color: VeriPayTheme.indigo.opacity(0.25), radius: 12, x: 0, y: 6)

      Text("VeriPay")
        .font(.system(size: compact ? 22 : 29, weight: .bold, design: .rounded))
        .foregroundColor(VeriPayTheme.primaryText)
    }
    .accessibilityElement(children: .combine)
    .accessibilityLabel("VeriPay")
  }
}

struct PrototypePill: View {
  var body: some View {
    Label("PRESENTATION DEMO", systemImage: "sparkles")
      .font(.system(size: 10, weight: .bold, design: .rounded))
      .tracking(0.8)
      .foregroundColor(VeriPayTheme.indigo)
      .padding(.horizontal, 12)
      .padding(.vertical, 7)
      .background(VeriPayTheme.indigo.opacity(0.1))
      .clipShape(Capsule())
  }
}

struct PrimaryActionButton: View {
  let title: String
  let symbol: String?
  let action: () -> Void

  init(_ title: String, symbol: String? = nil, action: @escaping () -> Void) {
    self.title = title
    self.symbol = symbol
    self.action = action
  }

  var body: some View {
    Button(action: action) {
      HStack(spacing: 10) {
        Text(title)
        if let symbol {
          Image(systemName: symbol)
        }
      }
      .font(.system(size: 17, weight: .semibold, design: .rounded))
      .foregroundColor(.white)
      .frame(maxWidth: .infinity)
      .frame(height: 58)
      .background(VeriPayTheme.brandGradient)
      .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
      .shadow(color: VeriPayTheme.indigo.opacity(0.26), radius: 14, x: 0, y: 8)
    }
    .buttonStyle(ScaleButtonStyle())
  }
}

struct SecondaryActionButton: View {
  let title: String
  let symbol: String?
  let tint: Color
  let action: () -> Void

  init(
    _ title: String,
    symbol: String? = nil,
    tint: Color = VeriPayTheme.indigo,
    action: @escaping () -> Void
  ) {
    self.title = title
    self.symbol = symbol
    self.tint = tint
    self.action = action
  }

  var body: some View {
    Button(action: action) {
      HStack(spacing: 10) {
        if let symbol {
          Image(systemName: symbol)
        }
        Text(title)
      }
      .font(.system(size: 17, weight: .semibold, design: .rounded))
      .foregroundColor(tint)
      .frame(maxWidth: .infinity)
      .frame(height: 56)
      .background(tint.opacity(0.1))
      .overlay(
        RoundedRectangle(cornerRadius: 18, style: .continuous)
          .stroke(tint.opacity(0.16), lineWidth: 1)
      )
      .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
    }
    .buttonStyle(ScaleButtonStyle())
  }
}

struct ScaleButtonStyle: ButtonStyle {
  func makeBody(configuration: Configuration) -> some View {
    configuration.label
      .scaleEffect(configuration.isPressed ? 0.975 : 1)
      .opacity(configuration.isPressed ? 0.9 : 1)
      .animation(.easeOut(duration: 0.14), value: configuration.isPressed)
  }
}

struct TransactionRow: View {
  let transaction: DemoTransaction

  var body: some View {
    HStack(spacing: 14) {
      ZStack {
        RoundedRectangle(cornerRadius: 14, style: .continuous)
          .fill(iconTint.opacity(0.11))
        Image(systemName: transaction.symbol)
          .font(.system(size: 18, weight: .semibold))
          .foregroundColor(iconTint)
      }
      .frame(width: 48, height: 48)

      VStack(alignment: .leading, spacing: 4) {
        Text(transaction.merchant)
          .font(.system(size: 15, weight: .semibold))
          .foregroundColor(VeriPayTheme.primaryText)
          .lineLimit(1)
        HStack(spacing: 5) {
          Text(transaction.category)
          Text("•")
          Text(transaction.shortDateText)
        }
        .font(.system(size: 12, weight: .medium))
        .foregroundColor(VeriPayTheme.secondaryText)
      }

      Spacer(minLength: 8)

      VStack(alignment: .trailing, spacing: 4) {
        Text("−\(transaction.amountText)")
          .font(.system(size: 15, weight: .semibold, design: .rounded))
          .foregroundColor(VeriPayTheme.primaryText)
        if transaction.status != .completed {
          Text(statusText)
            .font(.system(size: 10, weight: .bold, design: .rounded))
            .foregroundColor(iconTint)
            .textCase(.uppercase)
        }
      }
    }
    .padding(.vertical, 7)
    .accessibilityElement(children: .combine)
  }

  private var iconTint: Color {
    switch transaction.status {
    case .approved: return VeriPayTheme.success
    case .blocked: return VeriPayTheme.danger
    case .pending: return VeriPayTheme.warning
    case .completed: return VeriPayTheme.indigo
    }
  }

  private var statusText: String {
    switch transaction.status {
    case .approved: return "Approved"
    case .blocked: return "Blocked"
    case .pending: return "Pending"
    case .completed: return "Completed"
    }
  }
}

struct RiskGauge: View {
  let score: Int
  let level: FraudAnalysis.RiskLevel
  @State private var animatedProgress: CGFloat = 0

  var body: some View {
    ZStack {
      Circle()
        .stroke(gaugeColor.opacity(0.12), style: StrokeStyle(lineWidth: 14))
      Circle()
        .trim(from: 0, to: animatedProgress)
        .stroke(
          AngularGradient(
            colors: [gaugeColor.opacity(0.55), gaugeColor],
            center: .center
          ),
          style: StrokeStyle(lineWidth: 14, lineCap: .round)
        )
        .rotationEffect(.degrees(-90))
        .shadow(color: gaugeColor.opacity(0.25), radius: 8)

      VStack(spacing: 1) {
        Text("\(score)%")
          .font(.system(size: 38, weight: .bold, design: .rounded))
          .foregroundColor(VeriPayTheme.primaryText)
        Text("RISK")
          .font(.system(size: 10, weight: .bold, design: .rounded))
          .tracking(1.4)
          .foregroundColor(VeriPayTheme.secondaryText)
      }
    }
    .frame(width: 154, height: 154)
    .accessibilityElement(children: .ignore)
    .accessibilityLabel("Risk score \(score) percent")
    .onAppear {
      withAnimation(.easeOut(duration: 1.05).delay(0.12)) {
        animatedProgress = CGFloat(score) / 100
      }
    }
  }

  private var gaugeColor: Color {
    level == .low ? VeriPayTheme.success : VeriPayTheme.danger
  }
}

struct RiskReasonRow: View {
  let reason: RiskReason
  let tint: Color

  var body: some View {
    HStack(alignment: .top, spacing: 14) {
      ZStack {
        Circle().fill(tint.opacity(0.12))
        Image(systemName: reason.symbol)
          .font(.system(size: 16, weight: .semibold))
          .foregroundColor(tint)
      }
      .frame(width: 40, height: 40)

      VStack(alignment: .leading, spacing: 4) {
        Text(reason.title)
          .font(.system(size: 15, weight: .semibold))
          .foregroundColor(VeriPayTheme.primaryText)
        Text(reason.detail)
          .font(.system(size: 13, weight: .regular))
          .foregroundColor(VeriPayTheme.secondaryText)
          .fixedSize(horizontal: false, vertical: true)
      }
      Spacer(minLength: 0)
    }
    .accessibilityElement(children: .combine)
  }
}

struct DemoTopBar: View {
  let title: String?
  let onBack: (() -> Void)?
  let onReset: (() -> Void)?

  init(title: String? = nil, onBack: (() -> Void)? = nil, onReset: (() -> Void)? = nil) {
    self.title = title
    self.onBack = onBack
    self.onReset = onReset
  }

  var body: some View {
    HStack {
      if let onBack {
        Button(action: onBack) {
          Image(systemName: "chevron.left")
            .font(.system(size: 17, weight: .bold))
            .foregroundColor(VeriPayTheme.primaryText)
            .frame(width: 42, height: 42)
            .background(VeriPayTheme.surface)
            .clipShape(Circle())
        }
        .buttonStyle(ScaleButtonStyle())
      } else {
        BrandMark(compact: true)
      }

      Spacer()

      if let title {
        Text(title)
          .font(.system(size: 16, weight: .semibold, design: .rounded))
          .foregroundColor(VeriPayTheme.primaryText)
      }

      Spacer()

      if let onReset {
        Button(action: onReset) {
          Image(systemName: "arrow.counterclockwise")
            .font(.system(size: 16, weight: .semibold))
            .foregroundColor(VeriPayTheme.indigo)
            .frame(width: 42, height: 42)
            .background(VeriPayTheme.surface)
            .clipShape(Circle())
        }
        .buttonStyle(ScaleButtonStyle())
        .accessibilityLabel("Reset demo")
      } else {
        Color.clear.frame(width: 42, height: 42)
      }
    }
  }
}
