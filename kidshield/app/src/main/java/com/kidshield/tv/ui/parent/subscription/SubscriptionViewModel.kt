package com.kidshield.tv.ui.parent.subscription

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.amazon.device.iap.model.Product
import com.kidshield.tv.data.iap.AmazonIapManager
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SubscriptionViewModel @Inject constructor(
    private val iapManager: AmazonIapManager
) : ViewModel() {

    data class UiState(
        val hasActiveSubscription: Boolean = false,
        val activeSubscriptionSku: String? = null,
        val availableProducts: Map<String, Product> = emptyMap(),
        val isLoading: Boolean = false,
        val isPurchasing: Boolean = false,
        val purchaseError: String? = null
    )

    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    init {
        // Observe subscription state changes
        viewModelScope.launch {
            iapManager.subscriptionState.collect { subscriptionState ->
                _uiState.value = _uiState.value.copy(
                    hasActiveSubscription = subscriptionState.hasActiveSubscription,
                    activeSubscriptionSku = subscriptionState.activeSubscriptionSku,
                    availableProducts = subscriptionState.availableProducts,
                    isPurchasing = subscriptionState.isPurchasing,
                    purchaseError = subscriptionState.purchaseError
                )
            }
        }
    }

    fun loadSubscriptionData() {
        _uiState.value = _uiState.value.copy(isLoading = true)
        
        // Initialize IAP to refresh data
        iapManager.initialize()
        
        _uiState.value = _uiState.value.copy(isLoading = false)
    }

    fun purchaseSubscription(sku: String) {
        iapManager.purchaseSubscription(sku)
    }
}