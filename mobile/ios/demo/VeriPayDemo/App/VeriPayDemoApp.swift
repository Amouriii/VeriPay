import SwiftUI

@main
struct VeriPayDemoApp: App {
  @StateObject private var store = DemoStore()

  var body: some Scene {
    WindowGroup {
      ContentView()
        .environmentObject(store)
        .tint(VeriPayTheme.indigo)
    }
  }
}
