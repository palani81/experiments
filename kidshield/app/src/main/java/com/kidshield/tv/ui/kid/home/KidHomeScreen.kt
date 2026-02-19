package com.kidshield.tv.ui.kid.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Settings
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.tv.material3.ClickableSurfaceDefaults
import androidx.tv.material3.Icon
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Surface
import androidx.tv.material3.Text
import com.kidshield.tv.ui.kid.home.components.AppCard
import com.kidshield.tv.ui.theme.TvTextStyles

@Composable
fun KidHomeScreen(
    viewModel: KidHomeViewModel = hiltViewModel(),
    onParentAccess: () -> Unit,
    onTimesUp: (String, String) -> Unit
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    // Handle times up navigation
    LaunchedEffect(uiState.timesUpApp) {
        uiState.timesUpApp?.let { (pkg, name) ->
            onTimesUp(pkg, name)
            viewModel.clearTimesUp()
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 48.dp, vertical = 24.dp)
    ) {
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.spacedBy(32.dp)
        ) {
            // Header
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            text = uiState.greeting,
                            style = TvTextStyles.displayLarge,
                            color = MaterialTheme.colorScheme.primary
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "What do you want to watch?",
                            style = TvTextStyles.titleLarge,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }

                    // Parent access button - more prominent for first-time users
                    Surface(
                        onClick = onParentAccess,
                        shape = ClickableSurfaceDefaults.shape(shape = CircleShape),
                        scale = ClickableSurfaceDefaults.scale(focusedScale = 1.1f),
                        modifier = Modifier.size(if (uiState.categories.isEmpty()) 56.dp else 48.dp),
                        colors = ClickableSurfaceDefaults.colors(
                            containerColor = if (uiState.categories.isEmpty()) 
                                MaterialTheme.colorScheme.primary.copy(alpha = 0.2f)
                            else Color.Transparent,
                            focusedContainerColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.3f)
                        )
                    ) {
                        Box(contentAlignment = Alignment.Center, modifier = Modifier.fillMaxSize()) {
                            Icon(
                                Icons.Default.Settings,
                                contentDescription = "Parent Settings - Click here to set up apps",
                                tint = if (uiState.categories.isEmpty()) 
                                    MaterialTheme.colorScheme.primary
                                else MaterialTheme.colorScheme.onSurfaceVariant,
                                modifier = Modifier.size(if (uiState.categories.isEmpty()) 28.dp else 24.dp)
                            )
                        }
                    }
                }
            }

            // Error message
            if (uiState.launchError != null) {
                item {
                    Surface(
                        colors = ClickableSurfaceDefaults.colors(
                            containerColor = MaterialTheme.colorScheme.error.copy(alpha = 0.2f)
                        ),
                        onClick = { viewModel.clearError() },
                        shape = ClickableSurfaceDefaults.shape(
                            shape = androidx.compose.foundation.shape.RoundedCornerShape(12.dp)
                        )
                    ) {
                        Text(
                            text = uiState.launchError!!,
                            style = TvTextStyles.bodyLarge,
                            color = MaterialTheme.colorScheme.error,
                            modifier = Modifier.padding(16.dp)
                        )
                    }
                }
            }

            // Category rows
            uiState.categories.forEach { (category, apps) ->
                item {
                    Text(
                        text = category,
                        style = TvTextStyles.headlineMedium,
                        color = MaterialTheme.colorScheme.onBackground
                    )
                }
                item {
                    LazyRow(
                        horizontalArrangement = Arrangement.spacedBy(20.dp),
                        contentPadding = PaddingValues(start = 8.dp, end = 48.dp)
                    ) {
                        items(apps, key = { it.packageName }) { app ->
                            AppCard(
                                app = app,
                                onClick = { viewModel.launchApp(app.packageName) }
                            )
                        }
                    }
                }
            }

            // Empty state - First time user experience
            if (uiState.categories.isEmpty() && !uiState.isLoading) {
                item {
                    Column(
                        modifier = Modifier.fillMaxWidth().padding(top = 32.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        // Welcome message for parents
                        Column(
                            modifier = Modifier.padding(24.dp),
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Text(
                                text = "👋 Welcome to KidShield!",
                                style = TvTextStyles.headlineMedium,
                                color = MaterialTheme.colorScheme.primary
                            )
                            Spacer(modifier = Modifier.height(12.dp))
                            Text(
                                text = "Parents: Click the settings gear (⚙️) above to get started",
                                style = TvTextStyles.titleLarge,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                text = "You'll create a PIN and choose which apps your kids can use",
                                style = TvTextStyles.bodyLarge,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                        
                        Spacer(modifier = Modifier.height(32.dp))
                        
                        // Kid-friendly message
                        Text(
                            text = "🎮 Your apps will appear here once a parent sets them up!",
                            style = TvTextStyles.titleLarge,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }

            // Footer
            item {
                Spacer(modifier = Modifier.height(24.dp))
                Text(
                    text = "Have fun! Remember to take breaks.",
                    style = TvTextStyles.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f)
                )
            }
        }
    }
}
