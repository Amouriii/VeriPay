package com.veripay.sdk

class DcvvDisplayException(message: String) : Exception(message)

fun interface BiometricAuthenticator {
    fun authenticate(reason: String): Boolean
}

fun interface DcvvProvider {
    fun fetchDcvv(): String?
}

object DCvvDisplay {
    @JvmStatic
    fun reveal(): String =
        throw DcvvDisplayException("Biometric and vault providers are required")

    @JvmStatic
    fun reveal(
        authenticator: BiometricAuthenticator,
        provider: DcvvProvider,
        reason: String = "Verify your identity to reveal the dynamic CVV"
    ): String {
        if (!authenticator.authenticate(reason)) {
            throw DcvvDisplayException("Biometric authentication rejected")
        }
        return provider.fetchDcvv()?.takeIf { it.isNotEmpty() }
            ?: throw DcvvDisplayException("Dynamic CVV is unavailable")
    }
}
