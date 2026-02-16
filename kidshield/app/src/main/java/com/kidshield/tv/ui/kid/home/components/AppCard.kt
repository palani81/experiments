package com.kidshield.tv.ui.kid.home.components

import android.graphics.drawable.Drawable
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.core.graphics.drawable.toBitmap
import androidx.tv.material3.Border
import androidx.tv.material3.ClickableSurfaceDefaults
import androidx.tv.material3.Glow
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Surface
import androidx.tv.material3.Text
import com.kidshield.tv.domain.model.StreamingApp
import com.kidshield.tv.ui.theme.KidShieldGreen
import com.kidshield.tv.ui.theme.KidShieldOrange
import com.kidshield.tv.ui.theme.TvTextStyles

@Composable
fun AppCard(
    app: StreamingApp,
    onClick: () -> Unit
) {
    val timeColor = when {
        app.dailyMinutesRemaining == null -> Color.Transparent
        app.dailyMinutesRemaining > 30 -> KidShieldGreen
        app.dailyMinutesRemaining > 10 -> KidShieldOrange
        else -> Color.Red
    }

    Surface(
        onClick = onClick,
        modifier = Modifier.size(width = 200.dp, height = 160.dp),
        shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(16.dp)),
        scale = ClickableSurfaceDefaults.scale(focusedScale = 1.05f),
        glow = ClickableSurfaceDefaults.glow(
            focusedGlow = Glow(
                elevationColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.5f),
                elevation = 16.dp
            )
        ),
        border = ClickableSurfaceDefaults.border(
            focusedBorder = Border(
                border = androidx.compose.foundation.BorderStroke(
                    2.dp,
                    MaterialTheme.colorScheme.primary
                ),
                shape = RoundedCornerShape(16.dp)
            )
        ),
        colors = ClickableSurfaceDefaults.colors(
            containerColor = MaterialTheme.colorScheme.surface,
            focusedContainerColor = MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Column(
            modifier = Modifier.fillMaxSize().padding(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            if (app.iconDrawable != null) {
                val bitmap = remember(app.iconDrawable) {
                    app.iconDrawable.toBitmap(128, 128).asImageBitmap()
                }
                Image(
                    bitmap = bitmap,
                    contentDescription = app.displayName,
                    modifier = Modifier.size(64.dp)
                )
            } else {
                // Placeholder
                Surface(
                    modifier = Modifier.size(64.dp),
                    shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
                    colors = ClickableSurfaceDefaults.colors(
                        containerColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.3f)
                    ),
                    onClick = {}
                ) {
                    // Empty placeholder
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = app.displayName,
                style = TvTextStyles.bodyLarge,
                textAlign = TextAlign.Center,
                maxLines = 1
            )

            if (app.dailyMinutesRemaining != null) {
                TimeRemainingBadge(
                    minutesRemaining = app.dailyMinutesRemaining,
                    color = timeColor
                )
            }
        }
    }
}
