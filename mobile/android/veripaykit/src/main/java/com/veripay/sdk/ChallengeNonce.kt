package com.veripay.sdk

import java.util.UUID

data class ChallengeNonce(
    val value: String,
    val expiresAtMillis: Long
)

class SingleUseNonceStore(
    private val nowMillis: () -> Long = { System.currentTimeMillis() },
    private val nonceFactory: () -> String = { UUID.randomUUID().toString() }
) {
    private val expirations = mutableMapOf<String, Long>()

    fun issue(ttlMillis: Long = 90_000): ChallengeNonce {
        require(ttlMillis > 0) { "TTL must be positive" }
        val value = nonceFactory()
        val expiresAt = nowMillis() + ttlMillis
        expirations[value] = expiresAt
        return ChallengeNonce(value, expiresAt)
    }

    fun consume(nonce: ChallengeNonce): Boolean {
        val expiration = expirations.remove(nonce.value) ?: return false
        return expiration > nowMillis()
    }
}
