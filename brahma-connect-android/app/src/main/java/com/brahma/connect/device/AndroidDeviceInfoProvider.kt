package com.brahma.connect.device

import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.os.BatteryManager
import android.os.Build

data class AndroidDeviceInfo(
    val deviceName: String,
    val androidVersion: String,
    val batteryPercentage: Int,
    val charging: Boolean,
    val wifiEnabled: Boolean,
    val model: String,
)

class AndroidDeviceInfoProvider(private val context: Context) {
    fun snapshot(deviceName: String): AndroidDeviceInfo {
        val battery = batterySnapshot()
        return AndroidDeviceInfo(
            deviceName = deviceName,
            androidVersion = Build.VERSION.RELEASE ?: "Unknown",
            batteryPercentage = battery.first,
            charging = battery.second,
            wifiEnabled = wifiEnabled(),
            model = Build.MODEL ?: "Android",
        )
    }

    fun batterySnapshot(): Pair<Int, Boolean> {
        val intent = context.registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        val level = intent?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
        val scale = intent?.getIntExtra(BatteryManager.EXTRA_SCALE, -1) ?: -1
        val status = intent?.getIntExtra(BatteryManager.EXTRA_STATUS, -1) ?: -1
        val percentage = if (level >= 0 && scale > 0) ((level * 100f) / scale).toInt() else -1
        val charging = status == BatteryManager.BATTERY_STATUS_CHARGING || status == BatteryManager.BATTERY_STATUS_FULL
        return percentage.coerceIn(0, 100) to charging
    }

    fun wifiEnabled(): Boolean {
        val manager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager ?: return false
        val network = manager.activeNetwork ?: return false
        val caps = manager.getNetworkCapabilities(network) ?: return false
        return caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) || caps.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET)
    }
}
