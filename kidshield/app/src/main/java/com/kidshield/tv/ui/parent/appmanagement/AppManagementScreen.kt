package com.kidshield.tv.ui.parent.appmanagement

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
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.tv.material3.ClickableSurfaceDefaults
import androidx.tv.material3.Icon
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Surface
import androidx.tv.material3.Text
import com.kidshield.tv.domain.model.StreamingApp
import com.kidshield.tv.ui.theme.KidShieldGreen
import com.kidshield.tv.ui.theme.KidShieldRed
import com.kidshield.tv.ui.theme.TvTextStyles

@Composable
fun AppManagementScreen(
    viewModel: AppManagementViewModel = hiltViewModel(),
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
            Text("Manage Apps", style = TvTextStyles.headlineLarge)
        }

        Spacer(modifier = Modifier.height(8.dp))
        Text(
            "Choose which apps your kids can access",
            style = TvTextStyles.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )

        Spacer(modifier = Modifier.height(24.dp))

        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(uiState.apps) { app ->
                AppToggleRow(
                    app = app,
                    onToggle = { viewModel.toggleAppAllowed(app.packageName, !app.isAllowed) }
                )
            }
        }

        if (uiState.apps.isEmpty() && !uiState.isLoading) {
            Spacer(modifier = Modifier.height(32.dp))
            Text(
                "No streaming apps detected on this device.",
                style = TvTextStyles.titleLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
private fun AppToggleRow(
    app: StreamingApp,
    onToggle: () -> Unit
) {
    Surface(
        onClick = onToggle,
        shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
        scale = ClickableSurfaceDefaults.scale(focusedScale = 1.02f),
        colors = ClickableSurfaceDefaults.colors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant,
            focusedContainerColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.1f)
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(app.displayName, style = TvTextStyles.titleLarge)
                Text(
                    text = "${app.category.name} ${if (app.isKidsVariant) "- Kids" else ""}",
                    style = TvTextStyles.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            Surface(
                onClick = onToggle,
                shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(8.dp)),
                colors = ClickableSurfaceDefaults.colors(
                    containerColor = if (app.isAllowed)
                        KidShieldGreen.copy(alpha = 0.2f)
                    else
                        KidShieldRed.copy(alpha = 0.2f)
                ),
                scale = ClickableSurfaceDefaults.scale(focusedScale = 1.05f)
            ) {
                Text(
                    text = if (app.isAllowed) "Allowed" else "Blocked",
                    style = TvTextStyles.labelLarge,
                    color = if (app.isAllowed) KidShieldGreen else KidShieldRed,
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
                )
            }
        }
    }
}
