package com.kidshield.tv.ui.parent.setupwizard.steps

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.tv.material3.ClickableSurfaceDefaults
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Surface
import androidx.tv.material3.Text
import com.kidshield.tv.ui.theme.KidShieldGreen
import com.kidshield.tv.ui.theme.KidShieldRed
import com.kidshield.tv.ui.theme.TvTextStyles

@Composable
fun YouTubeKidsSetupStep(onComplete: () -> Unit) {
    val steps = listOf(
        "Install YouTube Kids from the Google Play Store on your TV",
        "Open YouTube Kids and sign in with your Google account",
        "Select your child's age range (Preschool, Younger, or Older)",
        "Choose whether to allow Search (recommended: OFF for younger kids)",
        "Review and approve the content settings",
        "Set a custom passcode for the parent area within YouTube Kids",
        "KidShield will automatically show YouTube Kids instead of regular YouTube for younger profiles"
    )

    LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            Text(
                "Set Up YouTube Kids",
                style = TvTextStyles.headlineMedium,
                color = KidShieldRed
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                "YouTube Kids provides a curated, safer experience for children with " +
                        "content filtered by age. KidShield will automatically use YouTube Kids " +
                        "instead of regular YouTube when the age profile is set to Toddler or Child.",
                style = TvTextStyles.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(modifier = Modifier.height(16.dp))
        }

        itemsIndexed(steps) { index, step ->
            SetupStepRow(stepNumber = index + 1, text = step)
        }

        item {
            Spacer(modifier = Modifier.height(24.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                Surface(
                    onClick = onComplete,
                    shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
                    scale = ClickableSurfaceDefaults.scale(focusedScale = 1.05f),
                    colors = ClickableSurfaceDefaults.colors(
                        containerColor = KidShieldGreen,
                        focusedContainerColor = KidShieldGreen
                    )
                ) {
                    Text(
                        "All Done!",
                        modifier = Modifier.padding(horizontal = 24.dp, vertical = 12.dp),
                        style = TvTextStyles.labelLarge,
                        color = Color.White
                    )
                }
                Surface(
                    onClick = onComplete,
                    shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
                    scale = ClickableSurfaceDefaults.scale(focusedScale = 1.05f),
                    colors = ClickableSurfaceDefaults.colors(
                        containerColor = MaterialTheme.colorScheme.surfaceVariant
                    )
                ) {
                    Text(
                        "Skip for now",
                        modifier = Modifier.padding(horizontal = 24.dp, vertical = 12.dp),
                        style = TvTextStyles.labelLarge
                    )
                }
            }
        }
    }
}
