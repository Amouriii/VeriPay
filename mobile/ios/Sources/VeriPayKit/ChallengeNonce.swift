import Foundation

public struct ChallengeNonce: Equatable {
    public let value: String
    public let expiresAt: Date

    public init(value: String, expiresAt: Date) {
        self.value = value
        self.expiresAt = expiresAt
    }
}

public final class SingleUseNonceStore {
    private var expirations: [String: Date] = [:]
    private let now: () -> Date
    private let nonceFactory: () -> String

    public init(
        now: @escaping () -> Date = Date.init,
        nonceFactory: @escaping () -> String = { UUID().uuidString }
    ) {
        self.now = now
        self.nonceFactory = nonceFactory
    }

    public func issue(ttl: TimeInterval = 90) -> ChallengeNonce {
        let nonce = nonceFactory()
        let expiresAt = now().addingTimeInterval(ttl)
        expirations[nonce] = expiresAt
        return ChallengeNonce(value: nonce, expiresAt: expiresAt)
    }

    public func consume(_ challenge: ChallengeNonce) -> Bool {
        guard let expiration = expirations.removeValue(forKey: challenge.value) else {
            return false
        }
        return expiration > now()
    }
}
