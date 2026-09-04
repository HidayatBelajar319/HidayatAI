package com.brahma.connect.network

import android.content.Context
import android.net.nsd.NsdManager
import android.net.nsd.NsdServiceInfo
import com.brahma.connect.core.AgentStateStore
import com.brahma.connect.core.GatewayEndpoint

class BrahmaGatewayDiscovery(private val context: Context) {
    private val nsdManager = context.getSystemService(Context.NSD_SERVICE) as NsdManager
    private var discoveryListener: NsdManager.DiscoveryListener? = null
    private var resolveListener: NsdManager.ResolveListener? = null

    fun start(onFound: (GatewayEndpoint) -> Unit, onError: (String) -> Unit = {}) {
        stop()
        resolveListener = object : NsdManager.ResolveListener {
            override fun onResolveFailed(serviceInfo: NsdServiceInfo?, errorCode: Int) {
                onError("Resolve failed: $errorCode")
            }

            override fun onServiceResolved(serviceInfo: NsdServiceInfo) {
                val host = serviceInfo.host?.hostAddress.orEmpty()
                val port = serviceInfo.port
                if (host.isNotBlank() && port > 0) {
                    val endpoint = GatewayEndpoint(
                        name = serviceInfo.serviceName ?: "Brahma PC",
                        host = host,
                        port = port,
                    )
                    AgentStateStore.setGateway(endpoint)
                    onFound(endpoint)
                }
            }
        }

        discoveryListener = object : NsdManager.DiscoveryListener {
            override fun onStartDiscoveryFailed(serviceType: String?, errorCode: Int) {
                onError("Discovery start failed: $errorCode")
            }

            override fun onStopDiscoveryFailed(serviceType: String?, errorCode: Int) {
                onError("Discovery stop failed: $errorCode")
            }

            override fun onDiscoveryStarted(serviceType: String?) = Unit
            override fun onDiscoveryStopped(serviceType: String?) = Unit

            override fun onServiceFound(serviceInfo: NsdServiceInfo) {
                val serviceType = serviceInfo.serviceType ?: return
                if (!serviceType.contains("_BRAHMA._tcp", ignoreCase = true)) return
                resolveListener?.let { nsdManager.resolveService(serviceInfo, it) }
            }

            override fun onServiceLost(serviceInfo: NsdServiceInfo) = Unit
        }

        runCatching {
            nsdManager.discoverServices("_BRAHMA._tcp.", NsdManager.PROTOCOL_DNS_SD, discoveryListener)
        }.onFailure {
            onError(it.message ?: "Discovery unavailable.")
        }
    }

    fun stop() {
        discoveryListener?.let { listener ->
            runCatching { nsdManager.stopServiceDiscovery(listener) }
        }
        discoveryListener = null
        resolveListener = null
    }
}
