package com.kidshield.tv.ui.parent.timelimits

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Remove
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.graphics.drawable.toBitmap
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.tv.material3.Border
import androidx.tv.material3.ClickableSurfaceDefaults
import androidx.tv.material3.Icon
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Surface
import androidx.tv.material3.Text
import com.kidshield.tv.ui.theme.KidShieldBlue
import com.kidshield.tv.ui.theme.TvTextStyles

@Composable
fun AppTimeLimitScreen(
    packageName: String,
    appName: String,
    viewModel: TimeLimitsViewModel = hiltViewModel(),
    onBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val appLimit = uiState.apps.find { it.packageName == packageName }

    val currentMinutes = appLimit?.dailyLimitMinutes ?: 60
    val hours = currentMinutes / 60
    val mins = currentMinutes % 60
    val timeText = if (hours > 0) "${hours}h ${mins}m" else "${mins}m"

    // Load app icon from package manager
    val context = LocalContext.current
    val appIcon = remember(packageName) {
        try {
            context.packageManager.getApplicationIcon(packageName).toBitmap(128, 128).asImageBitmap()
        } catch (_: Exception) {
            null
        }
    }

    Column(
        modifier = Modifier.fillMaxSize().padding(48.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Header with back button
        Row(
            verticalAlignment = Alignment.CenterVertically
        ) {
            Surface(
                onClick = onBack,
                shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(8.dp)),
                scale = ClickableSurfaceDefaults.scale(focusedScale = 1.05f)
            ) {
                Icon(
                    Icons.AutoMirrored.Filled.ArrowBack,
                    contentDescription = "Back",
                    modifier = Modifier.padding(12.dp)
                )
            }
        }

        Spacer(modifier = Modifier.weight(1f))

        // App icon
        if (appIcon != null) {
            Image(
                bitmap = appIcon,
                contentDescription = appName,
                modifier = Modifier.size(80.dp)
            )
            Spacer(modifier = Modifier.height(12.dp))
        }

        // App name — large and prominent
        Text(
            text = appName,
            style = TvTextStyles.headlineLarge,
            color = MaterialTheme.colorScheme.onBackground
        )

        Spacer(modifier = Modifier.height(24.dp))

        // Current time display — large and centered
        Text(
            text = timeText,
            style = TvTextStyles.displayLarge,
            color = KidShieldBlue
        )
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = "daily limit",
            style = TvTextStyles.titleLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )

        Spacer(modifier = Modifier.height(40.dp))

        // - and + buttons side by side
        Row(
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Decrease button
            Surface(
                onClick = {
                    val newLimit = (currentMinutes - 15).coerceAtLeast(15)
                    viewModel.updateDailyLimit(packageName, newLimit)
                },
                modifier = Modifier.size(width = 160.dp, height = 64.dp),
                shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
                scale = ClickableSurfaceDefaults.scale(focusedScale = 1.05f),
                border = ClickableSurfaceDefaults.border(
                    focusedBorder = Border(
                        border = BorderStroke(2.dp, KidShieldBlue),
                        shape = RoundedCornerShape(12.dp)
                    )
                ),
                colors = ClickableSurfaceDefaults.colors(
                    containerColor = Color(0xFF3A2020),
                    focusedContainerColor = Color(0xFF4A2020)
                )
            ) {
                Box(contentAlignment = Alignment.Center, modifier = Modifier.fillMaxSize()) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            Icons.Default.Remove,
                            contentDescription = "Decrease",
                            modifier = Modifier.size(28.dp),
                            tint = Color(0xFFFF6B6B)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("15 min", style = TvTextStyles.titleLarge, color = Color(0xFFFF6B6B))
                    }
                }
            }

            Spacer(modifier = Modifier.width(40.dp))

            // Increase button
            Surface(
                onClick = {
                    val newLimit = (currentMinutes + 15).coerceAtMost(480)
                    viewModel.updateDailyLimit(packageName, newLimit)
                },
                modifier = Modifier.size(width = 160.dp, height = 64.dp),
                shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
                scale = ClickableSurfaceDefaults.scale(focusedScale = 1.05f),
                border = ClickableSurfaceDefaults.border(
                    focusedBorder = Border(
                        border = BorderStroke(2.dp, KidShieldBlue),
                        shape = RoundedCornerShape(12.dp)
                    )
                ),
                colors = ClickableSurfaceDefaults.colors(
                    containerColor = Color(0xFF203A20),
                    focusedContainerColor = Color(0xFF204A20)
                )
            ) {
                Box(contentAlignment = Alignment.Center, modifier = Modifier.fillMaxSize()) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            Icons.Default.Add,
                            contentDescription = "Increase",
                            modifier = Modifier.size(28.dp),
                            tint = Color(0xFF69DB7C)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("15 min", style = TvTextStyles.titleLarge, color = Color(0xFF69DB7C))
                    }
                }
            }
        }

        Spacer(modifier = Modifier.weight(1f))
    }
}
