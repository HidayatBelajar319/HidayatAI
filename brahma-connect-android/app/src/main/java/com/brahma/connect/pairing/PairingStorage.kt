package com.brahma.connect.pairing

import android.content.Context
import android.os.Build
import com.brahma.connect.core.DeviceCredential
import com.brahma.connect.core.PairingOffer
import org.json.JSONObject
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

class PairingStorage(context: Context) {
    private val prefs = EncryptedSharedPreferences.create(
        context,
        "brahma_connect_secure",
        MasterKey.Builder(context).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build(),
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
    )

    fun saveCredential(credential: DeviceCredential) {
        prefs.edit()
            .putString("device_credential", JSONObject()
                .put("device_id", credential.deviceId)
                .put("device_secret", credential.deviceSecret)
                .put("device_name", credential.deviceName)
                .put("gateway_host", credential.gatewayHost)
                .put("gateway_port", credential.gatewayPort)
                .put("paired_at", credential.pairedAt)
                .toString())
            .apply()
    }

    fun loadCredential(): DeviceCredential? {
        val raw = prefs.getString("device_credential", null) ?: return null
        return try {
            val json = JSONObject(raw)
            DeviceCredential(
                deviceId = json.optString("device_id"),
                deviceSecret = json.optString("device_secret"),
                deviceName = json.optString("device_name", Build.MODEL),
                gatewayHost = json.optString("gateway_host"),
                gatewayPort = json.optInt("gateway_port", 8765),
                pairedAt = json.optString("paired_at"),
            )
        } catch (_: Exception) {
            null
        }
    }

    fun clearCredential() {
        prefs.edit().remove("device_credential").apply()
    }

    fun saveGatewayHint(offer: PairingOffer) {
        prefs.edit()
            .putString("last_pairing_offer", offer.toJson().toString())
            .apply()
    }

    fun loadGatewayHint(): PairingOffer? {
        val raw = prefs.getString("last_pairing_offer", null) ?: return null
        return try {
            PairingOffer.fromJson(JSONObject(raw))
        } catch (_: Exception) {
            null
        }
    }
}
