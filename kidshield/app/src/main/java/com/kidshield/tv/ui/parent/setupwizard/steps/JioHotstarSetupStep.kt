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
import com.kidshield.tv.ui.theme.KidShieldBlue
import com.kidshield.tv.ui.theme.KidShieldGreen
import com.kidshield.tv.ui.theme.TvTextStyles

@Composable
fun JioHotstarSetupStep(onComplete: () -> Unit) {
    val steps = listOf(
        "Open JioHotstar and sign in to your account",
        "Navigate to Settings (gear icon)",
        "Select 'Parental Lock' option",
        "Set a 4-digit PIN for parental controls",
        "Choose the content rating level for your child",
        "Enable 'Kids Mode' for a curated safe experience",
        "Create a separate Kids profile if available"
    )

    LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            Text(
                "Set Up JioHotstar Parental Controls",
                style = TvTextStyles.headlineMedium,
                color = KidShieldBlue
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                "JioHotstar has built-in parental controls with PIN protection and content filtering.",
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
                        "I've completed this step",
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
