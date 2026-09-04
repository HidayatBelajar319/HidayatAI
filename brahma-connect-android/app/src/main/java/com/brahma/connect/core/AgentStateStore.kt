package com.brahma.connect.core

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

object AgentStateStore {
    private val _connectionState = MutableStateFlow(ConnectionState.DISCONNECTED)
    val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()

    private val _gateway = MutableStateFlow<GatewayEndpoint?>(null)
    val gateway: StateFlow<GatewayEndpoint?> = _gateway.asStateFlow()

    private val _pairingOffer = MutableStateFlow<PairingOffer?>(null)
    val pairingOffer: StateFlow<PairingOffer?> = _pairingOffer.asStateFlow()

    private val _credential = MutableStateFlow<DeviceCredential?>(null)
    val credential: StateFlow<DeviceCredential?> = _credential.asStateFlow()

    private val _statusText = MutableStateFlow("Ready")
    val statusText: StateFlow<String> = _statusText.asStateFlow()

    private val _lastError = MutableStateFlow<String?>(null)
    val lastError: StateFlow<String?> = _lastError.asStateFlow()

    private val _logs = MutableStateFlow<List<String>>(emptyList())
    val logs: StateFlow<List<String>> = _logs.asStateFlow()

    private val _chatHistory = MutableStateFlow<List<ChatMessage>>(emptyList())
    val chatHistory: StateFlow<List<ChatMessage>> = _chatHistory.asStateFlow()

    fun setConnectionState(state: ConnectionState) {
        _connectionState.value = state
    }

    fun setGateway(endpoint: GatewayEndpoint?) {
        _gateway.value = endpoint
    }

    fun setPairingOffer(offer: PairingOffer?) {
        _pairingOffer.value = offer
    }

    fun setCredential(credential: DeviceCredential?) {
        _credential.value = credential
    }

    fun setStatus(text: String) {
        _statusText.value = text
    }

    fun setError(text: String?) {
        _lastError.value = text
    }

    fun addLog(message: String) {
        _logs.value = (_logs.value + message).takeLast(50)
    }

    fun addChatMessage(msg: ChatMessage) {
        val current = _chatHistory.value.toMutableList()
        current.removeAll { it.id == msg.id }
        current.add(msg)
        _chatHistory.value = current
    }

    fun setChatHistory(messages: List<ChatMessage>) {
        _chatHistory.value = messages
    }
}

object BrahmaConnectCapabilities {
    val INITIAL = listOf(
        "device_info",
        "battery",
        "flashlight",
        "volume",
        "media",
        "launch_app",
        "apps",
        "open_url",
        "wifi_state",
    )
}
