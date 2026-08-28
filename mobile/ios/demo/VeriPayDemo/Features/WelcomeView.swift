import SwiftUI

struct WelcomeView: View {
  @EnvironmentObject private var store: DemoStore
  @State private var email = "maya.bennett@example.com"
  @State private var password = "veripaydemo"
  @State private var contentVisible = false

  var body: some View {
    ZStack {
      background

      ScrollView(showsIndicators: false) {
        VStack(spacing: 0) {
          HStack {
            PrototypePill()
            Spacer()
          }
          .padding(.top, 12)

          VStack(spacing: 18) {
            BrandMark()
            VStack(spacing: 8) {
              Text("Banking that watches out for you.")
                .font(.system(size: 31, weight: .bold, design: .rounded))
                .multilineTextAlignment(.center)
                .foregroundColor(VeriPayTheme.primaryText)
              Text("Secure, intelligent payments with every purchase.")
                .font(.system(size: 16, weight: .regular))
                .multilineTextAlignment(.center)
                .foregroundColor(VeriPayTheme.secondaryText)
            }
          }
          .padding(.top, 42)

          VStack(spacing: 16) {
            inputField(
              title: "Email address",
              symbol: "envelope.fill",
              content: AnyView(
                TextField("Email address", text: $email)
                  .keyboardType(.emailAddress)
                  .textContentType(.username)
                  .autocapitalization(.none)
              )
            )

            inputField(
              title: "Password",
              symbol: "lock.fill",
              content: AnyView(
                SecureField("Password", text: $password)
                  .textContentType(.password)
              )
            )

            HStack {
              Label("Demo credentials are prefilled", systemImage: "info.circle.fill")
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(VeriPayTheme.secondaryText)
              Spacer()
            }

            PrimaryActionButton("Sign in to VeriPay", symbol: "arrow.right") {
              store.signIn()
            }
            .padding(.top, 5)

            HStack(spacing: 10) {
              Rectangle()
                .fill(VeriPayTheme.secondaryText.opacity(0.18))
                .frame(height: 1)
              Text("OR")
                .font(.system(size: 10, weight: .bold))
                .foregroundColor(VeriPayTheme.secondaryText)
              Rectangle()
                .fill(VeriPayTheme.secondaryText.opacity(0.18))
                .frame(height: 1)
            }

            SecondaryActionButton("Continue with Face ID", symbol: "faceid") {
              store.signIn()
            }
          }
          .veriPayCard(padding: 22)
          .padding(.top, 34)

          Text("Protected by VeriPay intelligent fraud monitoring")
            .font(.system(size: 11, weight: .medium))
            .foregroundColor(VeriPayTheme.secondaryText)
            .padding(.top, 22)
            .padding(.bottom, 24)
        }
        .padding(.horizontal, 22)
        .opacity(contentVisible ? 1 : 0)
        .offset(y: contentVisible ? 0 : 14)
      }
    }
    .onAppear {
      withAnimation(.easeOut(duration: 0.65)) {
        contentVisible = true
      }
    }
  }

  private var background: some View {
    ZStack {
      VeriPayTheme.background.ignoresSafeArea()
      Circle()
        .fill(VeriPayTheme.violet.opacity(0.13))
        .frame(width: 330, height: 330)
        .blur(radius: 18)
        .offset(x: 170, y: -300)
      Circle()
        .fill(VeriPayTheme.cyan.opacity(0.09))
        .frame(width: 290, height: 290)
        .blur(radius: 22)
        .offset(x: -175, y: 330)
    }
  }

  private func inputField(title: String, symbol: String, content: AnyView) -> some View {
    HStack(spacing: 13) {
      Image(systemName: symbol)
        .font(.system(size: 16, weight: .semibold))
        .foregroundColor(VeriPayTheme.indigo)
        .frame(width: 22)
      content
        .font(.system(size: 15, weight: .medium))
        .foregroundColor(VeriPayTheme.primaryText)
    }
    .padding(.horizontal, 16)
    .frame(height: 56)
    .background(VeriPayTheme.secondarySurface)
    .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
    .accessibilityLabel(title)
  }
}
