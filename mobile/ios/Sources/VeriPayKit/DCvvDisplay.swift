import Foundation

public enum DCvvDisplayError: Error, Equatable {
    case biometricRejected
    case dcvvUnavailable
    case emptyValue
}

public protocol BiometricAuthenticator {
    func authenticate(reason: String) throws
}

public protocol DcvvProvider {
    func fetchDcvv() throws -> String
}

public struct AllowAllBiometricAuthenticator: BiometricAuthenticator {
    public init() {}

    public func authenticate(reason: String) throws {
        _ = reason
    }
}

public struct InMemoryDcvvProvider: DcvvProvider {
    private let value: String?

    public init(value: String?) {
        self.value = value
    }

    public func fetchDcvv() throws -> String {
        guard let value else {
            throw DCvvDisplayError.dcvvUnavailable
        }
        return value
    }
}

public enum DCvvDisplay {
    public static func reveal() throws -> String {
        throw DCvvDisplayError.dcvvUnavailable
    }

    public static func reveal(
        using authenticator: any BiometricAuthenticator,
        provider: any DcvvProvider,
        reason: String = "Verify your identity to reveal the dynamic CVV"
    ) throws -> String {
        do {
            try authenticator.authenticate(reason: reason)
        } catch {
            throw DCvvDisplayError.biometricRejected
        }
        let value = try provider.fetchDcvv()
        guard !value.isEmpty else {
            throw DCvvDisplayError.emptyValue
        }
        return value
    }
}
