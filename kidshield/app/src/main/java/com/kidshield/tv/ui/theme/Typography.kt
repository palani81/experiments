package com.kidshield.tv.ui.theme

import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

// Custom text styles for TV viewing distance
object TvTextStyles {
    val displayLarge = TextStyle(
        fontSize = 48.sp,
        fontWeight = FontWeight.Bold,
        letterSpacing = (-0.25).sp
    )

    val headlineLarge = TextStyle(
        fontSize = 32.sp,
        fontWeight = FontWeight.Bold
    )

    val headlineMedium = TextStyle(
        fontSize = 28.sp,
        fontWeight = FontWeight.SemiBold
    )

    val titleLarge = TextStyle(
        fontSize = 22.sp,
        fontWeight = FontWeight.Medium
    )

    val bodyLarge = TextStyle(
        fontSize = 18.sp,
        fontWeight = FontWeight.Normal
    )

    val labelLarge = TextStyle(
        fontSize = 16.sp,
        fontWeight = FontWeight.Medium
    )

    val labelSmall = TextStyle(
        fontSize = 12.sp,
        fontWeight = FontWeight.Medium
    )
}
