package com.kidshield.tv.ui.parent.subscription

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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Star
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
import com.kidshield.tv.data.iap.AmazonIapManager
import com.kidshield.tv.ui.theme.KidShieldGreen
import com.kidshield.tv.ui.theme.TvTextStyles

@Composable
fun SubscriptionScreen(
    viewModel: SubscriptionViewModel = hiltViewModel(),
    onBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    LaunchedEffect(Unit) {
        viewModel.loadSubscriptionData()
    }

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
                Text("KidShield Premium", style = TvTextStyles.headlineLarge)
                if (uiState.hasActiveSubscription) {
                    Text(
                        "✓ Active Subscription",
                        style = TvTextStyles.bodyLarge,
                        color = KidShieldGreen
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(32.dp))

        LazyColumn(verticalArrangement = Arrangement.spacedBy(16.dp)) {
            // Premium Features
            item {
                PremiumFeaturesCard()
            }

            // Configuration Warning (Development Only)
            val configError = uiState.purchaseError
            if (configError != null && configError.contains("configuration")) {
                item {
                    Surface(
                        shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
                        colors = ClickableSurfaceDefaults.colors(
                            containerColor = MaterialTheme.colorScheme.errorContainer.copy(alpha = 0.3f)
                        ),
                        onClick = {}
                    ) {
                        Column(modifier = Modifier.fillMaxWidth().padding(16.dp)) {
                            Text(
                                "⚙️ Development Configuration",
                                style = TvTextStyles.titleLarge,
                                color = MaterialTheme.colorScheme.onErrorContainer
                            )
                            Text(
                                "Amazon IAP requires setup in Developer Console. This is normal during development.",
                                style = TvTextStyles.bodyLarge,
                                color = MaterialTheme.colorScheme.onErrorContainer.copy(alpha = 0.8f)
                            )
                        }
                    }
                }
            }

            // Purchase Error Display
            val purchaseError = uiState.purchaseError
            if (purchaseError != null && !purchaseError.contains("configuration")) {
                item {
                    Surface(
                        shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
                        colors = ClickableSurfaceDefaults.colors(
                            containerColor = MaterialTheme.colorScheme.errorContainer
                        ),
                        onClick = {}
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth().padding(16.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                "⚠️ $purchaseError",
                                style = TvTextStyles.bodyLarge,
                                color = MaterialTheme.colorScheme.onErrorContainer
                            )
                        }
                    }
                }
            }

            // Current Status
            if (uiState.hasActiveSubscription) {
                item {
                    ActiveSubscriptionCard(uiState.activeSubscriptionSku)
                }
            } else {
                // Show subscription plans
                item {
                    Text("Choose Your Plan", style = TvTextStyles.headlineMedium)
                    Text(
                        "Unlock all premium features with a subscription",
                        style = TvTextStyles.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(top = 8.dp)
                    )
                }

                // Show available products or default plans if products not loaded yet
                if (uiState.availableProducts.isNotEmpty()) {
                    uiState.availableProducts.forEach { (sku, product) ->
                        item {
                            SubscriptionPlanCard(
                                sku = sku,
                                product = product,
                                isPurchasing = uiState.isPurchasing,
                                onPurchase = { viewModel.purchaseSubscription(sku) }
                            )
                        }
                    }
                } else {
                    // Show default plans while loading
                    item {
                        DefaultSubscriptionPlanCard(
                            sku = AmazonIapManager.PREMIUM_MONTHLY_SKU,
                            title = "Monthly Premium",
                            description = "Full access to all premium features, billed monthly",
                            price = "$4.99/month",
                            isPurchasing = uiState.isPurchasing,
                            onPurchase = { viewModel.purchaseSubscription(AmazonIapManager.PREMIUM_MONTHLY_SKU) }
                        )
                    }
                    
                    item {
                        DefaultSubscriptionPlanCard(
                            sku = AmazonIapManager.PREMIUM_YEARLY_SKU,
                            title = "Yearly Premium",
                            description = "Full access to all premium features, billed yearly",
                            price = "$39.99/year",
                            badge = "🎉 Best Value - Save 20%",
                            isPurchasing = uiState.isPurchasing,
                            onPurchase = { viewModel.purchaseSubscription(AmazonIapManager.PREMIUM_YEARLY_SKU) }
                        )
                    }
                    
                    item {
                        DefaultSubscriptionPlanCard(
                            sku = AmazonIapManager.PREMIUM_FAMILY_SKU,
                            title = "Family Premium",
                            description = "Premium features for up to 5 children, billed yearly",
                            price = "$59.99/year",
                            isPurchasing = uiState.isPurchasing,
                            onPurchase = { viewModel.purchaseSubscription(AmazonIapManager.PREMIUM_FAMILY_SKU) }
                        )
                    }
                }
                
                // Loading/Purchasing indicator
                if (uiState.isLoading || uiState.isPurchasing) {
                    item {
                        Row(
                            modifier = Modifier.fillMaxWidth().padding(16.dp),
                            horizontalArrangement = Arrangement.Center
                        ) {
                            Text(
                                if (uiState.isPurchasing) "Processing purchase..." else "Loading subscription options...",
                                style = TvTextStyles.bodyLarge,
                                color = MaterialTheme.colorScheme.primary
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun PremiumFeaturesCard() {
    Surface(
        shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
        colors = ClickableSurfaceDefaults.colors(
            containerColor = MaterialTheme.colorScheme.primaryContainer
        ),
        onClick = {}
    ) {
        Column(modifier = Modifier.padding(24.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    Icons.Default.Star,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary
                )
                Spacer(modifier = Modifier.width(12.dp))
                Text(
                    "Premium Features",
                    style = TvTextStyles.headlineMedium,
                    color = MaterialTheme.colorScheme.onPrimaryContainer
                )
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            val features = listOf(
                "Unlimited app time limits and scheduling",
                "Advanced content filtering and age controls",
                "Multiple child profiles with individual settings",
                "Detailed usage analytics and reports",
                "Remote management from parent's phone",
                "Priority customer support",
                "Ad-free experience"
            )
            
            features.forEach { feature ->
                Row(
                    modifier = Modifier.padding(vertical = 4.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        Icons.Default.Check,
                        contentDescription = null,
                        tint = KidShieldGreen
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        feature,
                        style = TvTextStyles.bodyLarge,
                        color = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                }
            }
        }
    }
}

@Composable
private fun ActiveSubscriptionCard(activeSubscriptionSku: String?) {
    Surface(
        shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
        colors = ClickableSurfaceDefaults.colors(
            containerColor = KidShieldGreen.copy(alpha = 0.2f)
        ),
        onClick = {}
    ) {
        Column(modifier = Modifier.padding(24.dp)) {
            Text(
                "✓ Premium Active",
                style = TvTextStyles.headlineMedium,
                color = KidShieldGreen
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                "You have access to all premium features",
                style = TvTextStyles.bodyLarge,
                color = MaterialTheme.colorScheme.onSurface
            )
            activeSubscriptionSku?.let { sku ->
                Text(
                    "Plan: ${getPlanName(sku)}",
                    style = TvTextStyles.labelLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@Composable
private fun SubscriptionPlanCard(
    sku: String,
    product: com.amazon.device.iap.model.Product,
    isPurchasing: Boolean,
    onPurchase: () -> Unit
) {
    Surface(
        onClick = if (isPurchasing) { {} } else onPurchase,
        shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
        scale = ClickableSurfaceDefaults.scale(focusedScale = if (isPurchasing) 1.0f else 1.02f),
        colors = ClickableSurfaceDefaults.colors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant,
            focusedContainerColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.1f)
        )
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(24.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    product.title ?: getPlanName(sku),
                    style = TvTextStyles.titleLarge
                )
                Text(
                    product.description ?: getDefaultDescription(sku),
                    style = TvTextStyles.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                if (sku == AmazonIapManager.PREMIUM_YEARLY_SKU) {
                    Text(
                        "🎉 Best Value - Save 20%",
                        style = TvTextStyles.labelLarge,
                        color = KidShieldGreen
                    )
                }
            }
            
            Surface(
                onClick = if (isPurchasing) { {} } else onPurchase,
                shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(8.dp)),
                colors = ClickableSurfaceDefaults.colors(
                    containerColor = if (isPurchasing) 
                        MaterialTheme.colorScheme.surfaceVariant 
                    else MaterialTheme.colorScheme.primary,
                    focusedContainerColor = if (isPurchasing) 
                        MaterialTheme.colorScheme.surfaceVariant 
                    else MaterialTheme.colorScheme.primary
                )
            ) {
                Text(
                    if (isPurchasing) "Processing..." else (product.price ?: "Subscribe"),
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
                    style = TvTextStyles.labelLarge,
                    color = if (isPurchasing) 
                        MaterialTheme.colorScheme.onSurfaceVariant 
                    else Color.White
                )
            }
        }
    }
}

@Composable
private fun DefaultSubscriptionPlanCard(
    sku: String,
    title: String,
    description: String,
    price: String,
    badge: String? = null,
    isPurchasing: Boolean,
    onPurchase: () -> Unit
) {
    Surface(
        onClick = if (isPurchasing) { {} } else onPurchase,
        shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
        scale = ClickableSurfaceDefaults.scale(focusedScale = if (isPurchasing) 1.0f else 1.02f),
        colors = ClickableSurfaceDefaults.colors(
            containerColor = if (sku == AmazonIapManager.PREMIUM_YEARLY_SKU) 
                MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.3f)
            else MaterialTheme.colorScheme.surfaceVariant,
            focusedContainerColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.2f)
        )
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(24.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    title,
                    style = TvTextStyles.titleLarge,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Text(
                    description,
                    style = TvTextStyles.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(top = 4.dp)
                )
                badge?.let {
                    Text(
                        it,
                        style = TvTextStyles.labelLarge,
                        color = KidShieldGreen,
                        modifier = Modifier.padding(top = 4.dp)
                    )
                }
            }
            
            Spacer(modifier = Modifier.width(16.dp))
            
            Surface(
                onClick = if (isPurchasing) { {} } else onPurchase,
                shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(8.dp)),
                scale = ClickableSurfaceDefaults.scale(focusedScale = if (isPurchasing) 1.0f else 1.05f),
                colors = ClickableSurfaceDefaults.colors(
                    containerColor = if (isPurchasing) 
                        MaterialTheme.colorScheme.surfaceVariant 
                    else MaterialTheme.colorScheme.primary,
                    focusedContainerColor = if (isPurchasing) 
                        MaterialTheme.colorScheme.surfaceVariant 
                    else MaterialTheme.colorScheme.primary.copy(alpha = 0.8f)
                )
            ) {
                Text(
                    if (isPurchasing) "Processing..." else price,
                    modifier = Modifier.padding(horizontal = 20.dp, vertical = 12.dp),
                    style = TvTextStyles.titleLarge,
                    color = if (isPurchasing) 
                        MaterialTheme.colorScheme.onSurfaceVariant 
                    else Color.White
                )
            }
        }
    }
}

private fun getPlanName(sku: String): String {
    return when (sku) {
        AmazonIapManager.PREMIUM_MONTHLY_SKU -> "Monthly Premium"
        AmazonIapManager.PREMIUM_YEARLY_SKU -> "Yearly Premium"
        AmazonIapManager.PREMIUM_FAMILY_SKU -> "Family Premium"
        else -> "Premium Plan"
    }
}

private fun getDefaultDescription(sku: String): String {
    return when (sku) {
        AmazonIapManager.PREMIUM_MONTHLY_SKU -> "Full access to all premium features, billed monthly"
        AmazonIapManager.PREMIUM_YEARLY_SKU -> "Full access to all premium features, billed yearly"
        AmazonIapManager.PREMIUM_FAMILY_SKU -> "Premium features for up to 5 children, billed yearly"
        else -> "Access to premium features"
    }
}