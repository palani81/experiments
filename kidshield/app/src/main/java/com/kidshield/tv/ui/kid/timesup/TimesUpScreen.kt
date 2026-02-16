package com.kidshield.tv.ui.kid.timesup

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.HourglassBottom
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.tv.material3.ClickableSurfaceDefaults
import androidx.tv.material3.Glow
import androidx.tv.material3.Icon
import androidx.tv.material3.Surface
import androidx.tv.material3.Text
import com.kidshield.tv.ui.theme.KidShieldGreen
import com.kidshield.tv.ui.theme.KidShieldOrange
import com.kidshield.tv.ui.theme.TvTextStyles

@Composable
fun TimesUpScreen(
    appName: String,
    onDismiss: () -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    colors = listOf(Color(0xFF1A237E), Color(0xFF0D47A1))
                )
            ),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Icon(
                Icons.Default.HourglassBottom,
                contentDescription = null,
                modifier = Modifier.size(120.dp),
                tint = KidShieldOrange
            )

            Spacer(modifier = Modifier.height(24.dp))

            Text(
                text = "Time's up for $appName!",
                style = TvTextStyles.displayLarge,
                color = Color.White,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                text = "Great job today! Let's take a break.",
                style = TvTextStyles.titleLarge,
                color = Color.White.copy(alpha = 0.8f)
            )

            Spacer(modifier = Modifier.height(48.dp))

            Surface(
                onClick = onDismiss,
                shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
                scale = ClickableSurfaceDefaults.scale(focusedScale = 1.05f),
                glow = ClickableSurfaceDefaults.glow(
                    focusedGlow = Glow(
                        elevationColor = KidShieldGreen.copy(alpha = 0.5f),
                        elevation = 12.dp
                    )
                ),
                colors = ClickableSurfaceDefaults.colors(
                    containerColor = KidShieldGreen,
                    focusedContainerColor = KidShieldGreen
                )
            ) {
                Text(
                    text = "Back to Home",
                    modifier = Modifier.padding(horizontal = 32.dp, vertical = 16.dp),
                    style = TvTextStyles.titleLarge,
                    color = Color.White
                )
            }
        }
    }
}
