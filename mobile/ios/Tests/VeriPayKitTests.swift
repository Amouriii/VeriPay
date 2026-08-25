import Foundation
import XCTest
@testable import VeriPayKit

final class VeriPayKitTests: XCTestCase {
    func testDeviceIdentityUsesProviderBoundary() throws {
        let provider = InMemoryDeviceIdentityProvider(keyReference: "key-1")
        XCTAssertEqual(try DeviceIdentity.generateKey(using: provider), "key-1")
        XCTAssertEqual(try DeviceIdentity.attest(challenge: Data("challenge".utf8), using: provider), Data("Y2hhbGxlbmdl".utf8))
    }

    func testDcvvRequiresAuthenticationAndProviderValue() throws {
        let value = try DCvvDisplay.reveal(
            using: AllowAllBiometricAuthenticator(),
            provider: InMemoryDcvvProvider(value: "123")
        )
        XCTAssertEqual(value, "123")
        XCTAssertThrowsError(try DCvvDisplay.reveal()) { error in
            XCTAssertEqual(error as? DCvvDisplayError, .dcvvUnavailable)
        }
    }

    func testNonceIsSingleUseAndExpires() {
        var current = Date(timeIntervalSince1970: 0)
        let store = SingleUseNonceStore(
            now: { current },
            nonceFactory: { "nonce-1" }
        )
        let nonce = store.issue(ttl: 90)
        XCTAssertTrue(store.consume(nonce))
        XCTAssertFalse(store.consume(nonce))

        let expired = store.issue(ttl: 90)
        current = Date(timeIntervalSince1970: 91)
        XCTAssertFalse(store.consume(expired))
    }
}
