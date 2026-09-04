package com.brahma.connect.ui.theme

import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val BrahmaDarkColors = darkColorScheme(
    primary = Color(0xFFF4B400),
    onPrimary = Color.Black,
    secondary = Color(0xFFFFD54F),
    background = Color(0xFF020305),
    surface = Color(0xFF0B0D12),
    surfaceVariant = Color(0xFF10131A),
    onSurface = Color(0xFFF4F6F8),
    onSurfaceVariant = Color(0xFF8E949D),
    error = Color(0xFFFF6B6B),
)

@Composable
fun BrahmaConnectTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = BrahmaDarkColors,
        typography = androidx.compose.material3.Typography(),
        content = content,
    )
}
