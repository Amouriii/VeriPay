import Foundation

/// Secure in-app dCVV display requiring biometric confirmation (PLAN §16).
public enum DCvvDisplay {
    /// Reveal the active dCVV after biometric step-up. Stubbed.
    public static func reveal() throws -> String {
        fatalError("not implemented")
    }
}
