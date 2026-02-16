package com.kidshield.tv.ui.parent.contentsafety

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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.ChildCare
import androidx.compose.material.icons.filled.Face
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.PersonOutline
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.tv.material3.ClickableSurfaceDefaults
import androidx.tv.material3.Icon
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Surface
import androidx.tv.material3.Text
import com.kidshield.tv.domain.model.AgeProfile
import com.kidshield.tv.ui.theme.KidShieldBlue
import com.kidshield.tv.ui.theme.KidShieldGreen
import com.kidshield.tv.ui.theme.KidShieldOrange
import com.kidshield.tv.ui.theme.KidShieldPurple
import com.kidshield.tv.ui.theme.TvTextStyles

@Composable
fun ContentSafetyScreen(
    viewModel: ContentSafetyViewModel = hiltViewModel(),
    onBack: () -> Unit,
    onNavigateToSetupWizard: () -> Unit
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
            Text("Content Safety", style = TvTextStyles.headlineLarge)
        }

        Spacer(modifier = Modifier.height(24.dp))

        LazyColumn(verticalArrangement = Arrangement.spacedBy(24.dp)) {
            // Age Profile Section
            item {
                Text("Child's Age Profile", style = TvTextStyles.headlineMedium)
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    "This controls which apps and content are shown",
                    style = TvTextStyles.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(16.dp))

                LazyRow(
                    horizontalArrangement = Arrangement.spacedBy(16.dp),
                    contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 4.dp)
                ) {
                    item {
                        AgeProfileCard(
                            profile = AgeProfile.TODDLER,
                            label = "Toddler",
                            description = "Ages 2-5",
                            icon = Icons.Default.ChildCare,
                            isSelected = uiState.selectedAgeProfile == AgeProfile.TODDLER,
                            color = KidShieldGreen,
                            onClick = { viewModel.setAgeProfile(AgeProfile.TODDLER) }
                        )
                    }
                    item {
                        AgeProfileCard(
                            profile = AgeProfile.CHILD,
                            label = "Child",
                            description = "Ages 6-12",
                            icon = Icons.Default.Face,
                            isSelected = uiState.selectedAgeProfile == AgeProfile.CHILD,
                            color = KidShieldBlue,
                            onClick = { viewModel.setAgeProfile(AgeProfile.CHILD) }
                        )
                    }
                    item {
                        AgeProfileCard(
                            profile = AgeProfile.TEEN,
                            label = "Teen",
                            description = "Ages 13-17",
                            icon = Icons.Default.Person,
                            isSelected = uiState.selectedAgeProfile == AgeProfile.TEEN,
                            color = KidShieldOrange,
                            onClick = { viewModel.setAgeProfile(AgeProfile.TEEN) }
                        )
                    }
                    item {
                        AgeProfileCard(
                            profile = AgeProfile.ALL,
                            label = "No Filter",
                            description = "All ages",
                            icon = Icons.Default.PersonOutline,
                            isSelected = uiState.selectedAgeProfile == AgeProfile.ALL,
                            color = KidShieldPurple,
                            onClick = { viewModel.setAgeProfile(AgeProfile.ALL) }
                        )
                    }
                }
            }

            // Content Guidance
            item {
                Text("Content Guidance", style = TvTextStyles.headlineMedium)
                Spacer(modifier = Modifier.height(8.dp))

                when (uiState.selectedAgeProfile) {
                    AgeProfile.TODDLER -> Text(
                        "YouTube Kids will be shown instead of regular YouTube. " +
                                "Only apps rated for young children will appear.",
                        style = TvTextStyles.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    AgeProfile.CHILD -> Text(
                        "YouTube Kids will replace regular YouTube when available. " +
                                "Apps suitable for ages 6-12 will be shown.",
                        style = TvTextStyles.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    AgeProfile.TEEN -> Text(
                        "All allowed apps will be shown. " +
                                "We recommend setting up parental controls within each streaming app.",
                        style = TvTextStyles.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    AgeProfile.ALL -> Text(
                        "No content filtering is applied. All allowed apps are shown without restrictions.",
                        style = TvTextStyles.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            // Setup Wizard Button
            item {
                Spacer(modifier = Modifier.height(8.dp))
                Surface(
                    onClick = onNavigateToSetupWizard,
                    shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
                    scale = ClickableSurfaceDefaults.scale(focusedScale = 1.03f),
                    colors = ClickableSurfaceDefaults.colors(
                        containerColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.15f),
                        focusedContainerColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.25f)
                    )
                ) {
                    Column(modifier = Modifier.fillMaxWidth().padding(20.dp)) {
                        Text(
                            "Set Up Streaming App Parental Controls",
                            style = TvTextStyles.titleLarge
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            "Step-by-step guide to configure Netflix, JioHotstar, and YouTube Kids",
                            style = TvTextStyles.bodyLarge,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun AgeProfileCard(
    profile: AgeProfile,
    label: String,
    description: String,
    icon: ImageVector,
    isSelected: Boolean,
    color: androidx.compose.ui.graphics.Color,
    onClick: () -> Unit
) {
    Surface(
        onClick = onClick,
        shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(16.dp)),
        scale = ClickableSurfaceDefaults.scale(focusedScale = 1.03f),
        border = if (isSelected) {
            ClickableSurfaceDefaults.border(
                border = androidx.tv.material3.Border(
                    border = androidx.compose.foundation.BorderStroke(3.dp, color),
                    shape = RoundedCornerShape(16.dp)
                ),
                focusedBorder = androidx.tv.material3.Border(
                    border = androidx.compose.foundation.BorderStroke(3.dp, color),
                    shape = RoundedCornerShape(16.dp)
                )
            )
        } else {
            ClickableSurfaceDefaults.border()
        },
        colors = ClickableSurfaceDefaults.colors(
            containerColor = if (isSelected) color.copy(alpha = 0.2f)
            else MaterialTheme.colorScheme.surfaceVariant,
            focusedContainerColor = color.copy(alpha = 0.15f)
        )
    ) {
        Column(
            modifier = Modifier.padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                icon,
                contentDescription = null,
                tint = color,
                modifier = Modifier.padding(bottom = 8.dp)
            )
            Text(label, style = TvTextStyles.titleLarge, color = color)
            Text(
                description,
                style = TvTextStyles.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
