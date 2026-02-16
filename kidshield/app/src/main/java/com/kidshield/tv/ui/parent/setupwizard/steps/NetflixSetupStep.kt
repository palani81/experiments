package com.kidshield.tv.ui.parent.setupwizard.steps

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
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
fun NetflixSetupStep(onComplete: () -> Unit) {
    val steps = listOf(
        "Open Netflix and sign in to your parent account",
        "Go to 'Manage Profiles' from the menu",
        "Select the profile your child will use",
        "Toggle ON the 'Kids Profile' switch",
        "Set the maturity rating (TV-Y, TV-Y7, or TV-G for young kids)",
        "Go back and enable 'Profile Lock' on all adult profiles with a PIN"
    )

    LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            Text(
                "Set Up Netflix Kids Profile",
                style = TvTextStyles.headlineMedium,
                color = KidShieldRed
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                "Netflix's Kids profile restricts content to age-appropriate shows and movies.",
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

@Composable
fun SetupStepRow(stepNumber: Int, text: String) {
    Row(
        verticalAlignment = Alignment.Top,
        modifier = Modifier.fillMaxWidth()
    ) {
        Surface(
            onClick = {},
            shape = ClickableSurfaceDefaults.shape(shape = CircleShape),
            modifier = Modifier.size(32.dp),
            colors = ClickableSurfaceDefaults.colors(
                containerColor = MaterialTheme.colorScheme.primary
            )
        ) {
            Box(contentAlignment = Alignment.Center) {
                Text(
                    "$stepNumber",
                    style = TvTextStyles.labelLarge,
                    color = Color.White
                )
            }
        }
        Spacer(modifier = Modifier.width(12.dp))
        Text(
            text = text,
            style = TvTextStyles.bodyLarge,
            modifier = Modifier.padding(top = 4.dp)
        )
    }
}
