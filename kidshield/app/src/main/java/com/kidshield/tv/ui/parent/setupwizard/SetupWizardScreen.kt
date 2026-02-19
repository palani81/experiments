package com.kidshield.tv.ui.parent.setupwizard

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.filled.Apps
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Timer
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.tv.material3.ClickableSurfaceDefaults
import androidx.tv.material3.Icon
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Surface
import androidx.tv.material3.Text
import com.kidshield.tv.ui.theme.KidShieldGreen
import com.kidshield.tv.ui.theme.TvTextStyles

@Composable
fun SetupWizardScreen(
    initialStep: Int = 0,
    onBack: () -> Unit,
    onNavigateToAppManagement: () -> Unit = {},
    onNavigateToTimeLimits: () -> Unit = {}
) {
    var currentStep by remember { mutableIntStateOf(initialStep) }
    val totalSteps = 4

    Column(
        modifier = Modifier.fillMaxSize().padding(48.dp)
    ) {
        // Header with better navigation
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Surface(
                    onClick = {
                        if (currentStep > 0) currentStep-- else onBack()
                    },
                    shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(8.dp)),
                    scale = ClickableSurfaceDefaults.scale(focusedScale = 1.1f)
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back"
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            if (currentStep > 0) "Previous" else "Exit",
                            style = TvTextStyles.bodyLarge
                        )
                    }
                }
                Spacer(modifier = Modifier.width(24.dp))
                Column {
                    Text("🚀 Setup Wizard", style = TvTextStyles.headlineLarge)
                    Text(
                        "Step ${currentStep + 1} of $totalSteps",
                        style = TvTextStyles.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            
            // Progress indicator
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                repeat(totalSteps) { index ->
                    Surface(
                        onClick = {},
                        shape = ClickableSurfaceDefaults.shape(shape = CircleShape),
                        modifier = Modifier.size(12.dp),
                        colors = ClickableSurfaceDefaults.colors(
                            containerColor = if (index <= currentStep) 
                                MaterialTheme.colorScheme.primary 
                            else MaterialTheme.colorScheme.surfaceVariant
                        )
                    ) {}
                }
            }
        }

        Spacer(modifier = Modifier.height(32.dp))

        // Step content
        when (currentStep) {
            0 -> WelcomeStep(
                onNext = { currentStep++ }
            )
            1 -> AppSelectionStep(
                onNext = { currentStep++ },
                onSkip = { currentStep++ },
                onNavigateToAppManagement = onNavigateToAppManagement
            )
            2 -> TimeLimitsStep(
                onNext = { currentStep++ },
                onSkip = { currentStep++ },
                onNavigateToTimeLimits = onNavigateToTimeLimits
            )
            3 -> CompletionStep(
                onFinish = onBack
            )
        }
    }
}

@Composable
private fun WelcomeStep(onNext: () -> Unit) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            "👋 Welcome to KidShield Setup!",
            style = TvTextStyles.headlineMedium,
            color = MaterialTheme.colorScheme.primary
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Text(
            "Let's get your child's safe TV environment ready in just a few steps.",
            style = TvTextStyles.titleLarge,
            color = MaterialTheme.colorScheme.onSurface
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            "This wizard will help you:",
            style = TvTextStyles.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        
        Spacer(modifier = Modifier.height(12.dp))
        
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            BulletPoint("✅ Choose which apps your child can use")
            BulletPoint("⏰ Set daily time limits for each app")
            BulletPoint("🛡️ Configure age-appropriate content filters")
        }
        
        Spacer(modifier = Modifier.height(32.dp))
        
        Surface(
            onClick = onNext,
            shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
            scale = ClickableSurfaceDefaults.scale(focusedScale = 1.05f),
            colors = ClickableSurfaceDefaults.colors(
                containerColor = MaterialTheme.colorScheme.primary,
                focusedContainerColor = MaterialTheme.colorScheme.primary
            )
        ) {
            Row(
                modifier = Modifier.padding(horizontal = 32.dp, vertical = 16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    "Let's Get Started",
                    style = TvTextStyles.titleLarge,
                    color = Color.White
                )
                Spacer(modifier = Modifier.width(12.dp))
                Icon(
                    Icons.AutoMirrored.Filled.ArrowForward,
                    contentDescription = null,
                    tint = Color.White
                )
            }
        }
    }
}

@Composable
private fun AppSelectionStep(onNext: () -> Unit, onSkip: () -> Unit, onNavigateToAppManagement: () -> Unit) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Icon(
            Icons.Default.Apps,
            contentDescription = null,
            modifier = Modifier.size(48.dp),
            tint = MaterialTheme.colorScheme.primary
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            "Choose Your Child's Apps",
            style = TvTextStyles.headlineMedium,
            color = MaterialTheme.colorScheme.primary
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            "You can select which streaming apps your child can access.",
            style = TvTextStyles.titleLarge,
            color = MaterialTheme.colorScheme.onSurface
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Text(
            "💡 Tip: You can always change these later in the Parent Dashboard",
            style = TvTextStyles.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        
        Spacer(modifier = Modifier.height(32.dp))
        
        Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            Surface(
                onClick = onNavigateToAppManagement,
                shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
                scale = ClickableSurfaceDefaults.scale(focusedScale = 1.05f),
                colors = ClickableSurfaceDefaults.colors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    focusedContainerColor = MaterialTheme.colorScheme.primary
                )
            ) {
                Text(
                    "Choose Apps Now",
                    modifier = Modifier.padding(horizontal = 24.dp, vertical = 12.dp),
                    style = TvTextStyles.labelLarge,
                    color = Color.White
                )
            }
            
            Surface(
                onClick = onSkip,
                shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
                scale = ClickableSurfaceDefaults.scale(focusedScale = 1.05f),
                colors = ClickableSurfaceDefaults.colors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant
                )
            ) {
                Text(
                    "Skip for Now",
                    modifier = Modifier.padding(horizontal = 24.dp, vertical = 12.dp),
                    style = TvTextStyles.labelLarge
                )
            }
        }
    }
}

@Composable
private fun TimeLimitsStep(onNext: () -> Unit, onSkip: () -> Unit, onNavigateToTimeLimits: () -> Unit) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Icon(
            Icons.Default.Timer,
            contentDescription = null,
            modifier = Modifier.size(48.dp),
            tint = MaterialTheme.colorScheme.primary
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            "Set Time Limits",
            style = TvTextStyles.headlineMedium,
            color = MaterialTheme.colorScheme.primary
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            "Control how much time your child spends on each app daily.",
            style = TvTextStyles.titleLarge,
            color = MaterialTheme.colorScheme.onSurface
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            BulletPoint("⏰ Set limits from 15 minutes to 8 hours")
            BulletPoint("📊 Track usage in real-time")
            BulletPoint("🔒 Apps automatically lock when time is up")
        }
        
        Spacer(modifier = Modifier.height(32.dp))
        
        Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            Surface(
                onClick = onNavigateToTimeLimits,
                shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
                scale = ClickableSurfaceDefaults.scale(focusedScale = 1.05f),
                colors = ClickableSurfaceDefaults.colors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    focusedContainerColor = MaterialTheme.colorScheme.primary
                )
            ) {
                Text(
                    "Set Time Limits",
                    modifier = Modifier.padding(horizontal = 24.dp, vertical = 12.dp),
                    style = TvTextStyles.labelLarge,
                    color = Color.White
                )
            }
            
            Surface(
                onClick = onSkip,
                shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
                scale = ClickableSurfaceDefaults.scale(focusedScale = 1.05f),
                colors = ClickableSurfaceDefaults.colors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant
                )
            ) {
                Text(
                    "Skip for Now",
                    modifier = Modifier.padding(horizontal = 24.dp, vertical = 12.dp),
                    style = TvTextStyles.labelLarge
                )
            }
        }
    }
}

@Composable
private fun CompletionStep(onFinish: () -> Unit) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Icon(
            Icons.Default.CheckCircle,
            contentDescription = null,
            modifier = Modifier.size(64.dp),
            tint = KidShieldGreen
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Text(
            "🎉 Setup Complete!",
            style = TvTextStyles.headlineMedium,
            color = KidShieldGreen
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            "KidShield is now ready to keep your child safe while they enjoy their favorite shows.",
            style = TvTextStyles.titleLarge,
            color = MaterialTheme.colorScheme.onSurface
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            BulletPoint("🏠 Press the Home button to return to KidShield anytime")
            BulletPoint("⚙️ Access Parent Dashboard with your PIN")
            BulletPoint("🔄 Adjust settings anytime as your child grows")
        }
        
        Spacer(modifier = Modifier.height(32.dp))
        
        Surface(
            onClick = onFinish,
            shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
            scale = ClickableSurfaceDefaults.scale(focusedScale = 1.05f),
            colors = ClickableSurfaceDefaults.colors(
                containerColor = KidShieldGreen,
                focusedContainerColor = KidShieldGreen
            )
        ) {
            Row(
                modifier = Modifier.padding(horizontal = 32.dp, vertical = 16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    "Start Using KidShield",
                    style = TvTextStyles.titleLarge,
                    color = Color.White
                )
                Spacer(modifier = Modifier.width(12.dp))
                Icon(
                    Icons.Default.CheckCircle,
                    contentDescription = null,
                    tint = Color.White
                )
            }
        }
    }
}

@Composable
private fun BulletPoint(text: String) {
    Text(
        text = text,
        style = TvTextStyles.bodyLarge,
        color = MaterialTheme.colorScheme.onSurfaceVariant
    )
}