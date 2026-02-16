package com.kidshield.tv.ui.parent.setupwizard

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.tv.material3.ClickableSurfaceDefaults
import androidx.tv.material3.Icon
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Surface
import androidx.tv.material3.Text
import com.kidshield.tv.ui.parent.setupwizard.steps.JioHotstarSetupStep
import com.kidshield.tv.ui.parent.setupwizard.steps.NetflixSetupStep
import com.kidshield.tv.ui.parent.setupwizard.steps.YouTubeKidsSetupStep
import com.kidshield.tv.ui.theme.KidShieldGreen
import com.kidshield.tv.ui.theme.TvTextStyles

@Composable
fun SetupWizardScreen(onBack: () -> Unit) {
    var currentStep by remember { mutableIntStateOf(0) }
    val totalSteps = 3

    Column(
        modifier = Modifier.fillMaxSize().padding(48.dp)
    ) {
        // Header
        Row(verticalAlignment = Alignment.CenterVertically) {
            Surface(
                onClick = {
                    if (currentStep > 0) currentStep-- else onBack()
                },
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
            Text("Setup Wizard", style = TvTextStyles.headlineLarge)
            Spacer(modifier = Modifier.width(16.dp))
            Text(
                "Step ${currentStep + 1} of $totalSteps",
                style = TvTextStyles.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Step content
        when (currentStep) {
            0 -> NetflixSetupStep(
                onComplete = { currentStep++ }
            )
            1 -> JioHotstarSetupStep(
                onComplete = { currentStep++ }
            )
            2 -> YouTubeKidsSetupStep(
                onComplete = onBack
            )
        }
    }
}
