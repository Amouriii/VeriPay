# VeriPay iPhone Presentation Demo

This directory contains a self-contained native SwiftUI presentation prototype
for VeriPay. It demonstrates a polished fictional banking and fraud-review flow;
it is not a production banking application.

> **Prototype scope:** Every account, transaction, risk score, analysis reason,
> login action, approval, denial, and security response is mocked locally in the
> app. No network requests are made, no payment is processed, and no real
> authentication, fraud model, database, backend, or VeriPay SDK logic is used.

The upstream `PLAN.md` referenced by the repository documentation was unavailable
when this prototype was created. This demo therefore does **not** claim full
`PLAN.md` compliance.

## Requirements

- macOS with Xcode 15 or newer
- An iPhone Simulator running iOS 15 or newer, or a physical iPhone with iOS 15+
- No package installation or external dependency

## Open in Xcode

1. In Finder, open `mobile/ios/demo/`.
2. Double-click `VeriPayDemo.xcodeproj`.
3. Wait for Xcode to finish indexing.
4. Confirm the `VeriPayDemo` scheme is selected in the toolbar.

You can also open it from Terminal while at the repository root:

```bash
open mobile/ios/demo/VeriPayDemo.xcodeproj
```

## Run in the iPhone Simulator

1. In Xcode's run-destination menu, choose an iPhone simulator, such as
   **iPhone 16 Pro**.
2. Press **Command-R**, or choose **Product > Run**.
3. Use the prefilled fictional credentials or the mock Face ID button.
4. Tap **Simulate New Transaction** and choose either the low-risk or high-risk
   presentation scenario.

No signing team is required for the Simulator.

## Run on a physical iPhone

1. Connect the iPhone to the Mac, unlock it, and trust the Mac if prompted.
2. Open `VeriPayDemo.xcodeproj` in Xcode.
3. Select the **VeriPayDemo** project, then the **VeriPayDemo** target.
4. Open **Signing & Capabilities**, enable automatic signing, and select your
   Apple Developer team.
5. If Xcode reports that the bundle identifier is unavailable, replace
   `com.veripay.presentation.demo` with a unique identifier owned by your team.
6. Choose the connected iPhone as the run destination and press **Command-R**.
7. If requested by iOS, enable Developer Mode and trust the developer profile.

The app does not request Secure Enclave, App Attest, Face ID, network, or other
production entitlements. Its Face ID control is a clearly mocked presentation
interaction.

## Presentation flow

- Welcome and mock login
- Banking dashboard for fictional customer Maya Bennett
- Low-risk scenario: local analysis and automatic approval
- High-risk scenario: analysis, flagged reasons, and customer verification
- Approve and deny confirmations
- Reset Demo returns to the initial dashboard data for another presentation

## Implementation boundary

All source, mock data, project configuration, and documentation for the prototype
live in this directory. The project has no dependency on the adjacent
`mobile/ios/VeriPayKit` Swift package.
