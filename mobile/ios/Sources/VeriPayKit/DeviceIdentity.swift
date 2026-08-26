import Foundation

#if canImport(Security)
import Security
#endif

public enum DeviceIdentityError: Error, Equatable {
    case keyGenerationFailed
    case attestationUnavailable
}

public protocol DeviceIdentityProvider {
    func generateKeyReference() throws -> String
    func attest(challenge: Data) throws -> Data
}

public struct InMemoryDeviceIdentityProvider: DeviceIdentityProvider {
    private let keyReference: String

    public init(keyReference: String = "test-key-reference") {
        self.keyReference = keyReference
    }

    public func generateKeyReference() throws -> String {
        keyReference
    }

    public func attest(challenge: Data) throws -> Data {
        Data(challenge.base64EncodedString().utf8)
    }
}

#if canImport(Security)
public struct SecureEnclaveDeviceIdentityProvider: DeviceIdentityProvider {
    private let tagPrefix: String

    public init(tagPrefix: String = "com.veripay.sdk.device") {
        self.tagPrefix = tagPrefix
    }

    public func generateKeyReference() throws -> String {
        let tag = "\(tagPrefix).\(UUID().uuidString)"
        let attributes: [CFString: Any] = [
            kSecAttrKeyType: kSecAttrKeyTypeECSECPrimeRandom,
            kSecAttrKeySizeInBits: 256,
            kSecAttrTokenID: kSecAttrTokenIDSecureEnclave,
            kSecPrivateKeyAttrs: [
                kSecAttrIsPermanent: true,
                kSecAttrApplicationTag: Data(tag.utf8),
            ],
        ]
        var error: Unmanaged<CFError>?
        guard SecKeyCreateRandomKey(attributes as CFDictionary, &error) != nil else {
            _ = error?.takeRetainedValue()
            throw DeviceIdentityError.keyGenerationFailed
        }
        return tag
    }

    public func attest(challenge: Data) throws -> Data {
        _ = challenge
        throw DeviceIdentityError.attestationUnavailable
    }
}
#endif

public enum DeviceIdentity {
    public static func generateKey(
        using provider: any DeviceIdentityProvider = InMemoryDeviceIdentityProvider()
    ) throws -> String {
        try provider.generateKeyReference()
    }

    public static func attest(
        challenge: Data,
        using provider: any DeviceIdentityProvider = InMemoryDeviceIdentityProvider()
    ) throws -> Data {
        try provider.attest(challenge: challenge)
    }
}
