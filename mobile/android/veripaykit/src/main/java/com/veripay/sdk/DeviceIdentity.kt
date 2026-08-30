package com.veripay.sdk

import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import java.security.KeyPairGenerator
import java.security.spec.ECGenParameterSpec
import java.util.UUID

class DeviceIdentityException(message: String) : Exception(message)

interface DeviceIdentityProvider {
    fun generateKeyReference(): String
    fun attest(challenge: ByteArray): ByteArray
}

class AndroidKeystoreDeviceIdentityProvider(
    private val aliasPrefix: String = "veripay-device"
) : DeviceIdentityProvider {
    override fun generateKeyReference(): String {
        val alias = "$aliasPrefix-${UUID.randomUUID()}"
        val generator = KeyPairGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_EC,
            "AndroidKeyStore"
        )
        val spec = KeyGenParameterSpec.Builder(
            alias,
            KeyProperties.PURPOSE_SIGN or KeyProperties.PURPOSE_VERIFY
        )
            .setAlgorithmParameterSpec(ECGenParameterSpec("secp256r1"))
            .setDigests(KeyProperties.DIGEST_SHA256)
            .build()
        generator.initialize(spec)
        generator.generateKeyPair()
        return alias
    }

    override fun attest(challenge: ByteArray): ByteArray {
        throw DeviceIdentityException("Play Integrity provider must supply attestation")
    }
}

class InMemoryDeviceIdentityProvider(
    private val keyReference: String = "test-key-reference"
) : DeviceIdentityProvider {
    override fun generateKeyReference(): String = keyReference

    override fun attest(challenge: ByteArray): ByteArray =
        challenge.copyOf()
}

object DeviceIdentity {
    @JvmStatic
    fun generateKey(
        provider: DeviceIdentityProvider = InMemoryDeviceIdentityProvider()
    ): String = provider.generateKeyReference()

    @JvmStatic
    fun attest(
        challenge: ByteArray,
        provider: DeviceIdentityProvider = InMemoryDeviceIdentityProvider()
    ): ByteArray = provider.attest(challenge)
}
