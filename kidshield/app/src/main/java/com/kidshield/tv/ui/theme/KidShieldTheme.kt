package com.kidshield.tv.ui.theme

import androidx.compose.runtime.Composable
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.darkColorScheme

private val DarkColorScheme = darkColorScheme(
    primary = KidShieldBlue,
    onPrimary = androidx.compose.ui.graphics.Color.White,
    secondary = KidShieldGreen,
    onSecondary = androidx.compose.ui.graphics.Color.White,
    tertiary = KidShieldOrange,
    onTertiary = androidx.compose.ui.graphics.Color.Black,
    background = BackgroundDark,
    onBackground = androidx.compose.ui.graphics.Color.White,
    surface = SurfaceDark,
    onSurface = androidx.compose.ui.graphics.Color.White,
    surfaceVariant = SurfaceVariantDark,
    onSurfaceVariant = androidx.compose.ui.graphics.Color(0xFFCACACA),
    error = KidShieldRed,
    onError = androidx.compose.ui.graphics.Color.White,
)

@Composable
fun KidShieldTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = DarkColorScheme,
        content = content
    )
}
