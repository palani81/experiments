package com.kidshield.tv.ui.parent.timelimits

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Remove
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
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
fun TimeLimitsScreen(
    viewModel: TimeLimitsViewModel = hiltViewModel(),
    onBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    Column(
        modifier = Modifier.fillMaxSize().padding(48.dp)
    ) {
        // Header
        Row(verticalAlignment = Alignment.CenterVertically) {
            Surface(
                onClick = onBack,
                shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(8.dp)),
                scale = ClickableSurfaceDefaults.scale(focusedScale = 1.1f)
            ) {
                Icon(
                    Icons.AutoMirrored.Filled.ArrowBack,
                    contentDescription = "Back",
                    modifier = Modifier.padding(12.dp)
                )
            }
            Spacer(modifier = Modifier.width(16.dp))
            Text("Time Limits", style = TvTextStyles.headlineLarge)
        }

        Spacer(modifier = Modifier.height(8.dp))
        Text(
            "Set daily screen time limits for each app",
            style = TvTextStyles.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )

        Spacer(modifier = Modifier.height(24.dp))

        LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            items(uiState.apps) { appLimit ->
                TimeLimitCard(
                    appLimit = appLimit,
                    onIncrease = {
                        val newLimit = (appLimit.dailyLimitMinutes + 15).coerceAtMost(480)
                        viewModel.updateDailyLimit(appLimit.packageName, newLimit)
                    },
                    onDecrease = {
                        val newLimit = (appLimit.dailyLimitMinutes - 15).coerceAtLeast(15)
                        viewModel.updateDailyLimit(appLimit.packageName, newLimit)
                    }
                )
            }
        }
    }
}

@Composable
private fun TimeLimitCard(
    appLimit: TimeLimitsViewModel.AppTimeLimitUi,
    onIncrease: () -> Unit,
    onDecrease: () -> Unit
) {
    val hours = appLimit.dailyLimitMinutes / 60
    val mins = appLimit.dailyLimitMinutes % 60
    val timeText = if (hours > 0) "${hours}h ${mins}m" else "${mins}m"

    // Use a plain Box (not Surface) as the outer container so it doesn't steal focus
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(
                color = MaterialTheme.colorScheme.surfaceVariant,
                shape = RoundedCornerShape(12.dp)
            )
            .padding(16.dp)
    ) {
        Column {
            // Top row: App name and time
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(appLimit.appName, style = TvTextStyles.titleLarge)
                Text(
                    text = timeText,
                    style = TvTextStyles.headlineLarge,
                    color = KidShieldBlue
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Bottom row: - and + buttons
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Decrease button
                Surface(
                    onClick = onDecrease,
                    modifier = Modifier.size(width = 120.dp, height = 48.dp),
                    shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(8.dp)),
                    scale = ClickableSurfaceDefaults.scale(focusedScale = 1.1f),
                    border = ClickableSurfaceDefaults.border(
                        focusedBorder = Border(
                            border = BorderStroke(2.dp, KidShieldBlue),
                            shape = RoundedCornerShape(8.dp)
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
                                modifier = Modifier.size(24.dp),
                                tint = Color(0xFFFF6B6B)
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("15 min", style = TvTextStyles.bodyLarge, color = Color(0xFFFF6B6B))
                        }
                    }
                }

                Spacer(modifier = Modifier.width(24.dp))

                // Increase button
                Surface(
                    onClick = onIncrease,
                    modifier = Modifier.size(width = 120.dp, height = 48.dp),
                    shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(8.dp)),
                    scale = ClickableSurfaceDefaults.scale(focusedScale = 1.1f),
                    border = ClickableSurfaceDefaults.border(
                        focusedBorder = Border(
                            border = BorderStroke(2.dp, KidShieldBlue),
                            shape = RoundedCornerShape(8.dp)
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
                                modifier = Modifier.size(24.dp),
                                tint = Color(0xFF69DB7C)
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("15 min", style = TvTextStyles.bodyLarge, color = Color(0xFF69DB7C))
                        }
                    }
                }
            }
        }
    }
}
