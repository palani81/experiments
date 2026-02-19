package com.kidshield.tv.ui.parent.dashboard

import android.content.Intent
import android.provider.Settings as AndroidSettings
import androidx.compose.material.icons.filled.Settings
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Apps
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Security
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.filled.Timer
import androidx.compose.material.icons.filled.Warning
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.tv.material3.ClickableSurfaceDefaults
import androidx.tv.material3.Icon
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Surface
import androidx.tv.material3.Text
import com.kidshield.tv.domain.model.UsageRecord
import com.kidshield.tv.service.LockTaskHelper
import com.kidshield.tv.ui.theme.KidShieldGreen
import com.kidshield.tv.ui.theme.KidShieldOrange
import com.kidshield.tv.ui.theme.TvTextStyles

@Composable
fun ParentDashboardScreen(
    viewModel: ParentDashboardViewModel = hiltViewModel(),
    lockTaskHelper: LockTaskHelper? = null,
    onNavigateToTimeLimits: () -> Unit,
    onNavigateToAppTimeLimit: (String, String) -> Unit = { _, _ -> },
    onNavigateToAppManagement: () -> Unit,
    onNavigateToContentSafety: () -> Unit,
    onNavigateToSetupWizard: () -> Unit,
    onNavigateToSubscription: () -> Unit,
    onBackToKids: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val context = LocalContext.current
    val isProtected = lockTaskHelper?.isDeviceOwner == true || lockTaskHelper?.isDefaultLauncher == true

    // Use a single LazyColumn for the entire screen so everything scrolls with D-pad
    LazyColumn(
        modifier = Modifier.fillMaxSize().padding(48.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        // First-time user guidance
        if (uiState.appUsages.isEmpty()) {
            item {
                Surface(
                    onClick = onNavigateToSetupWizard,
                    shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
                    scale = ClickableSurfaceDefaults.scale(focusedScale = 1.02f),
                    colors = ClickableSurfaceDefaults.colors(
                        containerColor = MaterialTheme.colorScheme.primaryContainer,
                        focusedContainerColor = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.8f)
                    )
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth().padding(20.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            Icons.Default.Settings,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.onPrimaryContainer
                        )
                        Spacer(modifier = Modifier.width(16.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                "🚀 Get Started with Setup Wizard",
                                style = TvTextStyles.titleLarge,
                                color = MaterialTheme.colorScheme.onPrimaryContainer
                            )
                            Text(
                                "Click here for guided setup to choose apps and set time limits",
                                style = TvTextStyles.bodyLarge,
                                color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.8f)
                            )
                        }
                    }
                }
            }
        }
        // Home button protection warning
        if (!isProtected) {
            item {
                Surface(
                    onClick = {
                        // Multi-approach strategy for setting default launcher
                        try {
                            // Approach 1: Use Intent.createChooser to force launcher selection
                            val homeIntent = Intent(Intent.ACTION_MAIN).apply {
                                addCategory(Intent.CATEGORY_HOME)
                                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                                addFlags(Intent.FLAG_ACTIVITY_CLEAR_TASK)
                            }
                            
                            // Force the chooser dialog
                            val chooser = Intent.createChooser(homeIntent, "Choose Default Launcher")
                            chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                            context.startActivity(chooser)
                            
                        } catch (e: Exception) {
                            // Approach 2: Try to open home settings directly
                            try {
                                val settingsIntent = Intent().apply {
                                    action = AndroidSettings.ACTION_HOME_SETTINGS
                                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                                }
                                context.startActivity(settingsIntent)
                                
                            } catch (e2: Exception) {
                                // Approach 3: Open general app settings
                                try {
                                    val appSettingsIntent = Intent().apply {
                                        action = AndroidSettings.ACTION_MANAGE_DEFAULT_APPS_SETTINGS
                                        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                                    }
                                    context.startActivity(appSettingsIntent)
                                    
                                } catch (e3: Exception) {
                                    // Approach 4: Open application settings
                                    try {
                                        val generalSettingsIntent = Intent().apply {
                                            action = AndroidSettings.ACTION_APPLICATION_SETTINGS
                                            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                                        }
                                        context.startActivity(generalSettingsIntent)
                                        
                                    } catch (e4: Exception) {
                                        // Final approach: Trigger home intent to show available launchers
                                        try {
                                            val basicHomeIntent = Intent(Intent.ACTION_MAIN).apply {
                                                addCategory(Intent.CATEGORY_HOME)
                                                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                                                // Clear the default to force selection
                                                addFlags(Intent.FLAG_ACTIVITY_CLEAR_TASK)
                                            }
                                            context.startActivity(basicHomeIntent)
                                        } catch (e5: Exception) {
                                            // If all else fails, at least we tried
                                            android.util.Log.w("KidShield", "Could not open launcher settings", e5)
                                        }
                                    }
                                }
                            }
                        }
                    },
                    shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
                    scale = ClickableSurfaceDefaults.scale(focusedScale = 1.02f),
                    colors = ClickableSurfaceDefaults.colors(
                        containerColor = Color(0xFF4A2020),
                        focusedContainerColor = Color(0xFF5A2020)
                    )
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth().padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            Icons.Default.Warning,
                            contentDescription = null,
                            tint = Color(0xFFFF6B6B)
                        )
                        Spacer(modifier = Modifier.width(12.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                "Home Button Not Protected",
                                style = TvTextStyles.titleLarge,
                                color = Color(0xFFFF6B6B)
                            )
                            Text(
                                "Click to choose KidShield as your default launcher",
                                style = TvTextStyles.bodyLarge,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            Text(
                                "Then select 'Always' when prompted",
                                style = TvTextStyles.labelLarge,
                                color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
                            )
                        }
                        Icon(Icons.Default.Home, contentDescription = null, tint = Color(0xFFFF6B6B))
                    }
                }
            }
        }

        // Header
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Parent Dashboard",
                    style = TvTextStyles.headlineLarge
                )
                Surface(
                    onClick = onBackToKids,
                    shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(8.dp)),
                    scale = ClickableSurfaceDefaults.scale(focusedScale = 1.05f)
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp, 8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Back to Kids", style = TvTextStyles.bodyLarge)
                    }
                }
            }
        }

        // Quick navigation buttons
        item {
            Spacer(modifier = Modifier.height(8.dp))
            LazyRow(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                item {
                    DashboardNavButton("Time Limits", Icons.Default.Timer, onNavigateToTimeLimits)
                }
                item {
                    DashboardNavButton("Manage Apps", Icons.Default.Apps, onNavigateToAppManagement)
                }
                item {
                    DashboardNavButton("Content Safety", Icons.Default.Security, onNavigateToContentSafety)
                }
                item {
                    DashboardNavButton("Setup Wizard", Icons.Default.Settings, onNavigateToSetupWizard)
                }
                item {
                    DashboardNavButton("Premium", Icons.Default.Star, onNavigateToSubscription)
                }
            }
        }

        // Today's summary
        item {
            Spacer(modifier = Modifier.height(16.dp))
            Text("Today's Screen Time", style = TvTextStyles.headlineMedium)
        }

        item {
            val hours = uiState.totalMinutesToday / 60
            val mins = uiState.totalMinutesToday % 60
            Text(
                text = if (hours > 0) "${hours}h ${mins}m" else "${mins} minutes",
                style = TvTextStyles.displayLarge,
                color = MaterialTheme.colorScheme.primary
            )
        }

        // Per-app usage header
        item {
            Spacer(modifier = Modifier.height(12.dp))
            Text("Per-App Usage", style = TvTextStyles.titleLarge)
        }

        // Per-app usage rows - clicking navigates to per-app Time Limit screen
        items(uiState.appUsages) { usage ->
            AppUsageRow(
                usage = usage,
                onClick = { onNavigateToAppTimeLimit(usage.packageName, usage.appName) }
            )
        }

        // Bottom spacer so last items can scroll into view
        item {
            Spacer(modifier = Modifier.height(48.dp))
        }
    }
}

@Composable
private fun DashboardNavButton(
    label: String,
    icon: ImageVector,
    onClick: () -> Unit
) {
    Surface(
        onClick = onClick,
        shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
        scale = ClickableSurfaceDefaults.scale(focusedScale = 1.05f),
        colors = ClickableSurfaceDefaults.colors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant,
            focusedContainerColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.2f)
        )
    ) {
        Column(
            modifier = Modifier.padding(20.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(icon, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
            Spacer(modifier = Modifier.height(8.dp))
            Text(label, style = TvTextStyles.labelLarge)
        }
    }
}

@Composable
private fun AppUsageRow(usage: UsageRecord, onClick: () -> Unit) {
    Surface(
        onClick = onClick,
        shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(8.dp)),
        scale = ClickableSurfaceDefaults.scale(focusedScale = 1.02f),
        colors = ClickableSurfaceDefaults.colors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(usage.appName, style = TvTextStyles.bodyLarge)

            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = "${usage.minutesUsed}m",
                    style = TvTextStyles.bodyLarge,
                    color = when {
                        usage.limitMinutes == null -> MaterialTheme.colorScheme.onSurface
                        usage.minutesUsed >= usage.limitMinutes -> MaterialTheme.colorScheme.error
                        usage.minutesUsed >= usage.limitMinutes * 0.8 -> KidShieldOrange
                        else -> KidShieldGreen
                    }
                )
                if (usage.limitMinutes != null) {
                    Text(
                        text = " / ${usage.limitMinutes}m",
                        style = TvTextStyles.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }
    }
}

