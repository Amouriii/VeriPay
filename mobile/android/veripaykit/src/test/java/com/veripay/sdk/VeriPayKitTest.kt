package com.veripay.sdk

import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class VeriPayKitTest {
    @Test
    fun deviceIdentityUsesProviderBoundary() {
        val provider = InMemoryDeviceIdentityProvider("key-1")
        assertEquals("key-1", DeviceIdentity.generateKey(provider))
        assertArrayEquals(
            "challenge".toByteArray(),
            DeviceIdentity.attest("challenge".toByteArray(), provider)
        )
    }

    @Test
    fun dcvvRequiresBiometricAndProviderValue() {
        val value = DCvvDisplay.reveal(
            BiometricAuthenticator { true },
            DcvvProvider { "123" }
        )
        assertEquals("123", value)
        assertThrows(DcvvDisplayException::class.java) {
            DCvvDisplay.reveal(BiometricAuthenticator { false }, DcvvProvider { "123" })
        }
    }

    @Test
    fun nonceIsSingleUseAndExpires() {
        var current = 0L
        val store = SingleUseNonceStore(nowMillis = { current }, nonceFactory = { "nonce-1" })
        val nonce = store.issue(90_000)
        assertTrue(store.consume(nonce))
        assertFalse(store.consume(nonce))

        val expired = store.issue(90_000)
        current = 90_001
        assertFalse(store.consume(expired))
    }
}
