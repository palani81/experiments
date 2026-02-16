package com.kidshield.tv.data.local.preferences

import android.content.SharedPreferences
import at.favre.lib.crypto.bcrypt.BCrypt

class PinManager(private val prefs: SharedPreferences) {

    companion object {
        private const val KEY_PIN_HASH = "pin_hash"
        private const val KEY_PIN_SET = "pin_is_set"
    }

    val isPinSet: Boolean
        get() = prefs.getBoolean(KEY_PIN_SET, false)

    fun setPin(pin: String) {
        val hash = BCrypt.withDefaults().hashToString(12, pin.toCharArray())
        prefs.edit()
            .putString(KEY_PIN_HASH, hash)
            .putBoolean(KEY_PIN_SET, true)
            .apply()
    }

    fun verifyPin(attempt: String): Boolean {
        val storedHash = prefs.getString(KEY_PIN_HASH, null) ?: return false
        return BCrypt.verifyer().verify(attempt.toCharArray(), storedHash).verified
    }

    fun clearPin() {
        prefs.edit()
            .remove(KEY_PIN_HASH)
            .putBoolean(KEY_PIN_SET, false)
            .apply()
    }
}
