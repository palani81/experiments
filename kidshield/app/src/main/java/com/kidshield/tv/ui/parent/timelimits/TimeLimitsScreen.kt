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
import androidx.compose.material.icons.automirrored.filled.ArrowForward
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
    onBack: () -> Unit,
    showContinueSetup: Boolean = false,
    onContinueSetup: () -> Unit = {}
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
            Column {
                Text(
                    if (showContinueSetup) "Setup: Set Time Limits" else "Time Limits", 
                    style = TvTextStyles.headlineLarge
                )
                if (showContinueSetup) {
                    Text(
                        "Step 3 of 4",
                        style = TvTextStyles.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(8.dp))
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                "Set daily screen time limits for each app",
                style = TvTextStyles.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            // Quick-set buttons for testing
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Surface(
                    onClick = { viewModel.setAllToMinutes(1) },
                    shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(8.dp)),
                    scale = ClickableSurfaceDefaults.scale(focusedScale = 1.1f),
                    border = ClickableSurfaceDefaults.border(
                        focusedBorder = Border(
                            border = BorderStroke(2.dp, Color(0xFFFF6B6B)),
                            shape = RoundedCornerShape(8.dp)
                        )
                    ),
                    colors = ClickableSurfaceDefaults.colors(
                        containerColor = Color(0xFF3A2020),
                        focusedContainerColor = Color(0xFF4A2020)
                    )
                ) {
                    Text(
                        "All → 1 min",
                        style = TvTextStyles.labelLarge,
                        color = Color(0xFFFF6B6B),
                        modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
                    )
                }
                Surface(
                    onClick = { viewModel.setAllToMinutes(60) },
                    shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(8.dp)),
                    scale = ClickableSurfaceDefaults.scale(focusedScale = 1.1f),
                    border = ClickableSurfaceDefaults.border(
                        focusedBorder = Border(
                            border = BorderStroke(2.dp, Color(0xFF69DB7C)),
                            shape = RoundedCornerShape(8.dp)
                        )
                    ),
                    colors = ClickableSurfaceDefaults.colors(
                        containerColor = Color(0xFF203A20),
                        focusedContainerColor = Color(0xFF204A20)
                    )
                ) {
                    Text(
                        "All → 1 hr",
                        style = TvTextStyles.labelLarge,
                        color = Color(0xFF69DB7C),
                        modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            items(uiState.apps) { appLimit ->
                TimeLimitCard(
                    appLimit = appLimit,
                    onDecrease15 = {
                        val newLimit = (appLimit.dailyLimitMinutes - 15).coerceAtLeast(1)
                        viewModel.updateDailyLimit(appLimit.packageName, newLimit)
                    },
                    onDecrease1 = {
                        val newLimit = (appLimit.dailyLimitMinutes - 1).coerceAtLeast(1)
                        viewModel.updateDailyLimit(appLimit.packageName, newLimit)
                    },
                    onIncrease1 = {
                        val newLimit = (appLimit.dailyLimitMinutes + 1).coerceAtMost(480)
                        viewModel.updateDailyLimit(appLimit.packageName, newLimit)
                    },
                    onIncrease15 = {
                        val newLimit = (appLimit.dailyLimitMinutes + 15).coerceAtMost(480)
                        viewModel.updateDailyLimit(appLimit.packageName, newLimit)
                    }
                )
            }
            
            // Continue setup button when accessed from setup wizard
            if (showContinueSetup && uiState.apps.isNotEmpty()) {
                item {
                    Spacer(modifier = Modifier.height(24.dp))
                    Surface(
                        onClick = onContinueSetup,
                        shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
                        scale = ClickableSurfaceDefaults.scale(focusedScale = 1.05f),
                        colors = ClickableSurfaceDefaults.colors(
                            containerColor = MaterialTheme.colorScheme.primary,
                            focusedContainerColor = MaterialTheme.colorScheme.primary
                        )
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 24.dp, vertical = 12.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                "Continue Setup",
                                style = TvTextStyles.labelLarge,
                                color = Color.White
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Icon(
                                androidx.compose.material.icons.Icons.AutoMirrored.Filled.ArrowForward,
                                contentDescription = null,
                                tint = Color.White
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun TimeLimitCard(
    appLimit: TimeLimitsViewModel.AppTimeLimitUi,
    onDecrease15: () -> Unit,
    onDecrease1: () -> Unit,
    onIncrease1: () -> Unit,
    onIncrease15: () -> Unit
) {
    val hours = appLimit.dailyLimitMinutes / 60
    val mins = appLimit.dailyLimitMinutes % 60
    val timeText = if (hours > 0) "${hours}h ${mins}m" else "${mins}m"

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

            // Bottom row: -15  -1  +1  +15 buttons
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                TimeLimitButton(
                    label = "- 15",
                    containerColor = Color(0xFF3A2020),
                    focusedColor = Color(0xFF4A2020),
                    tintColor = Color(0xFFFF6B6B),
                    onClick = onDecrease15
                )
                Spacer(modifier = Modifier.width(8.dp))
                TimeLimitButton(
                    label = "- 1",
                    containerColor = Color(0xFF3A2020),
                    focusedColor = Color(0xFF4A2020),
                    tintColor = Color(0xFFFF6B6B),
                    onClick = onDecrease1
                )
                Spacer(modifier = Modifier.width(16.dp))
                TimeLimitButton(
                    label = "+ 1",
                    containerColor = Color(0xFF203A20),
                    focusedColor = Color(0xFF204A20),
                    tintColor = Color(0xFF69DB7C),
                    onClick = onIncrease1
                )
                Spacer(modifier = Modifier.width(8.dp))
                TimeLimitButton(
                    label = "+ 15",
                    containerColor = Color(0xFF203A20),
                    focusedColor = Color(0xFF204A20),
                    tintColor = Color(0xFF69DB7C),
                    onClick = onIncrease15
                )
            }
        }
    }
}

@Composable
private fun TimeLimitButton(
    label: String,
    containerColor: Color,
    focusedColor: Color,
    tintColor: Color,
    onClick: () -> Unit
) {
    Surface(
        onClick = onClick,
        modifier = Modifier.size(width = 90.dp, height = 44.dp),
        shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(8.dp)),
        scale = ClickableSurfaceDefaults.scale(focusedScale = 1.1f),
        border = ClickableSurfaceDefaults.border(
            focusedBorder = Border(
                border = BorderStroke(2.dp, KidShieldBlue),
                shape = RoundedCornerShape(8.dp)
            )
        ),
        colors = ClickableSurfaceDefaults.colors(
            containerColor = containerColor,
            focusedContainerColor = focusedColor
        )
    ) {
        Box(contentAlignment = Alignment.Center, modifier = Modifier.fillMaxSize()) {
            Text(label, style = TvTextStyles.bodyLarge, color = tintColor)
        }
    }
}
