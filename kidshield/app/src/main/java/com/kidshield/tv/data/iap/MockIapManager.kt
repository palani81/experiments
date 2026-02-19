package com.kidshield.tv.data.iap

import android.content.Context
import android.util.Log
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Mock IAP Manager for development testing when Amazon services aren't available
 * Use this for sideloading and local development
 */
@Singleton
class MockIapManager @Inject constructor(
    @ApplicationContext private val context: Context
) {

    companion object {
        private const val TAG = "MockIapManager"
        
        // Same SKUs as real implementation
        const val PREMIUM_MONTHLY_SKU = "com.kidshield.tv.premium.monthly"
        const val PREMIUM_YEARLY_SKU = "com.kidshield.tv.premium.yearly"
        const val PREMIUM_FAMILY_SKU = "com.kidshield.tv.premium.family"
    }

    private val _subscriptionState = MutableStateFlow(MockSubscriptionState())
    val subscriptionState: StateFlow<MockSubscriptionState> = _subscriptionState.asStateFlow()

    init {
        Log.d(TAG, "Mock IAP Manager initialized for development testing")
        
        // Simulate loading products
        _subscriptionState.value = _subscriptionState.value.copy(
            availableProducts = mapOf(
                PREMIUM_MONTHLY_SKU to MockProduct(
                    sku = PREMIUM_MONTHLY_SKU,
                    title = "Monthly Premium",
                    description = "Full access to all premium features, billed monthly",
                    price = "$4.99"
                ),
                PREMIUM_YEARLY_SKU to MockProduct(
                    sku = PREMIUM_YEARLY_SKU,
                    title = "Yearly Premium", 
                    description = "Full access to all premium features, billed yearly",
                    price = "$39.99"
                ),
                PREMIUM_FAMILY_SKU to MockProduct(
                    sku = PREMIUM_FAMILY_SKU,
                    title = "Family Premium",
                    description = "Premium features for up to 5 children, billed yearly", 
                    price = "$59.99"
                )
            )
        )
    }

    /**
     * Initialize mock IAP
     */
    fun initialize() {
        Log.d(TAG, "Mock IAP initialized - simulating Amazon services")
        // Simulate successful initialization
        _subscriptionState.value = _subscriptionState.value.copy(
            purchaseError = null
        )
    }

    /**
     * Simulate subscription purchase
     */
    suspend fun purchaseSubscription(sku: String) {
        Log.d(TAG, "Mock purchase initiated for SKU: $sku")
        
        // Show purchasing state
        _subscriptionState.value = _subscriptionState.value.copy(
            isPurchasing = true,
            purchaseError = null
        )
        
        // Simulate purchase processing delay
        delay(2000)
        
        // Simulate successful purchase
        _subscriptionState.value = _subscriptionState.value.copy(
            isPurchasing = false,
            hasActiveSubscription = true,
            activeSubscriptionSku = sku,
            purchaseDate = System.currentTimeMillis()
        )
        
        Log.d(TAG, "Mock purchase completed successfully for SKU: $sku")
    }

    /**
     * Check if user has active premium subscription
     */
    fun hasPremiumSubscription(): Boolean {
        return _subscriptionState.value.hasActiveSubscription
    }

    /**
     * Reset subscription for testing
     */
    fun resetSubscription() {
        _subscriptionState.value = _subscriptionState.value.copy(
            hasActiveSubscription = false,
            activeSubscriptionSku = null,
            purchaseDate = null
        )
        Log.d(TAG, "Mock subscription reset")
    }

    data class MockSubscriptionState(
        val hasActiveSubscription: Boolean = false,
        val activeSubscriptionSku: String? = null,
        val purchaseDate: Long? = null,
        val availableProducts: Map<String, MockProduct> = emptyMap(),
        val isPurchasing: Boolean = false,
        val purchaseError: String? = null
    )

    data class MockProduct(
        val sku: String,
        val title: String,
        val description: String,
        val price: String
    )
}