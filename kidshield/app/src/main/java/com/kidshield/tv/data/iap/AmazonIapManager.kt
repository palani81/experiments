package com.kidshield.tv.data.iap

import android.content.Context
import android.util.Log
import com.amazon.device.iap.PurchasingListener
import com.amazon.device.iap.PurchasingService
import com.amazon.device.iap.model.*
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AmazonIapManager @Inject constructor(
    @ApplicationContext private val context: Context
) : PurchasingListener {

    companion object {
        private const val TAG = "AmazonIapManager"
        
        // Subscription SKUs - Define these in Amazon Developer Console
        const val PREMIUM_MONTHLY_SKU = "com.kidshield.tv.premium.monthly"
        const val PREMIUM_YEARLY_SKU = "com.kidshield.tv.premium.yearly"
        const val PREMIUM_FAMILY_SKU = "com.kidshield.tv.premium.family"
    }

    private val _subscriptionState = MutableStateFlow(SubscriptionState())
    val subscriptionState: StateFlow<SubscriptionState> = _subscriptionState.asStateFlow()

    private var currentUserId: String? = null
    private var currentMarketplace: String? = null
    private var purchaseTimeoutJob: kotlinx.coroutines.Job? = null
    private val coroutineScope = CoroutineScope(SupervisorJob() + Dispatchers.Main)

    init {
        // Register this class as the purchasing listener
        PurchasingService.registerListener(context, this)
        
        // Enable pending purchases support
        PurchasingService.enablePendingPurchases()
        
        // Validate public key exists
        validatePublicKey()
        
        Log.d(TAG, "Amazon IAP Manager initialized")
        Log.d(TAG, "Package name: ${context.packageName}")
        Log.d(TAG, "SKUs configured: $PREMIUM_MONTHLY_SKU, $PREMIUM_YEARLY_SKU, $PREMIUM_FAMILY_SKU")
    }

    /**
     * Validate that the required public key file exists
     */
    private fun validatePublicKey() {
        try {
            val assetManager = context.assets
            val inputStream = assetManager.open("AppstoreAuthenticationKey.pem")
            inputStream.close()
            Log.d(TAG, "Public key file found - IAP security enabled")
        } catch (e: Exception) {
            Log.w(TAG, "Public key file not found. IAP may not work properly. " +
                "Please add AppstoreAuthenticationKey.pem to assets folder. Error: ${e.message}")
            
            // Update state to show configuration error
            _subscriptionState.value = _subscriptionState.value.copy(
                purchaseError = "IAP configuration incomplete. Please contact support."
            )
        }
    }

    /**
     * Initialize IAP - call this when app starts
     */
    fun initialize() {
        Log.d(TAG, "Initializing Amazon IAP")
        
        // Get user data
        PurchasingService.getUserData()
        
        // Validate product SKUs
        val productSkus = setOf(
            PREMIUM_MONTHLY_SKU,
            PREMIUM_YEARLY_SKU,
            PREMIUM_FAMILY_SKU
        )
        PurchasingService.getProductData(productSkus)
        
        // Get existing purchases
        PurchasingService.getPurchaseUpdates(true)
    }

    /**
     * Refresh purchase status - call when app resumes to catch purchases completed in background
     */
    fun refreshPurchaseStatus() {
        Log.d(TAG, "Refreshing purchase status")
        
        // Cancel any pending timeout since we're refreshing
        purchaseTimeoutJob?.cancel()
        
        // Clear purchasing state if stuck
        if (_subscriptionState.value.isPurchasing) {
            Log.d(TAG, "Clearing stuck purchasing state")
            _subscriptionState.value = _subscriptionState.value.copy(
                isPurchasing = false,
                purchaseError = null
            )
        }
        
        // Refresh purchase data from Amazon
        PurchasingService.getPurchaseUpdates(false)
    }

    /**
     * Purchase a subscription
     */
    fun purchaseSubscription(sku: String) {
        Log.d(TAG, "Initiating purchase for SKU: $sku")
        Log.d(TAG, "Current user ID: $currentUserId")
        Log.d(TAG, "Current marketplace: $currentMarketplace")
        
        // First, refresh purchase status to check for existing entitlements
        // This catches purchases that completed but callback wasn't received
        Log.d(TAG, "Checking for existing entitlements before purchase...")
        PurchasingService.getPurchaseUpdates(false)
        
        // Check if already subscribed to this SKU
        if (_subscriptionState.value.hasActiveSubscription && 
            _subscriptionState.value.activeSubscriptionSku == sku) {
            Log.w(TAG, "User already has active subscription to $sku")
            _subscriptionState.value = _subscriptionState.value.copy(
                purchaseError = "You already have an active subscription to this plan."
            )
            return
        }
        
        // Cancel any existing timeout
        purchaseTimeoutJob?.cancel()
        
        // Update state to show purchase is in progress
        _subscriptionState.value = _subscriptionState.value.copy(
            isPurchasing = true,
            purchaseError = null
        )
        
        // Set timeout for purchase (2 minutes to allow for full purchase flow)
        purchaseTimeoutJob = coroutineScope.launch {
            delay(120000) // 2 minutes
            if (_subscriptionState.value.isPurchasing) {
                Log.w(TAG, "Purchase timeout - no response received after 2 minutes")
                Log.d(TAG, "Attempting to refresh purchase status after timeout...")
                
                // Try to refresh purchase status one more time
                PurchasingService.getPurchaseUpdates(false)
                
                // Give it a moment to process
                delay(2000)
                
                // If still purchasing after refresh, show timeout message
                if (_subscriptionState.value.isPurchasing) {
                    _subscriptionState.value = _subscriptionState.value.copy(
                        isPurchasing = false,
                        purchaseError = "Purchase timed out. If you completed the purchase, please restart the app to refresh your subscription status."
                    )
                }
            }
        }
        
        try {
            val requestId = PurchasingService.purchase(sku)
            Log.d(TAG, "Purchase request sent with ID: $requestId")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to initiate purchase", e)
            purchaseTimeoutJob?.cancel()
            _subscriptionState.value = _subscriptionState.value.copy(
                isPurchasing = false,
                purchaseError = "Failed to start purchase: ${e.message}"
            )
        }
    }

    /**
     * Check if user has active premium subscription
     */
    fun hasPremiumSubscription(): Boolean {
        return _subscriptionState.value.hasActiveSubscription
    }

    /**
     * Check if IAP is properly configured with public key
     */
    fun isIapConfigured(): Boolean {
        return try {
            val assetManager = context.assets
            val inputStream = context.assets.open("AppstoreAuthenticationKey.pem")
            inputStream.close()
            true
        } catch (e: Exception) {
            false
        }
    }

    /**
     * Get configuration status for debugging
     */
    fun getConfigurationStatus(): String {
        return if (isIapConfigured()) {
            "IAP properly configured with public key"
        } else {
            "IAP configuration incomplete - missing AppstoreAuthenticationKey.pem"
        }
    }

    // PurchasingListener implementation
    override fun onUserDataResponse(response: UserDataResponse) {
        Log.d(TAG, "onUserDataResponse: ${response.requestStatus}")
        
        when (response.requestStatus) {
            UserDataResponse.RequestStatus.SUCCESSFUL -> {
                currentUserId = response.userData.userId
                currentMarketplace = response.userData.marketplace
                Log.d(TAG, "User ID: $currentUserId, Marketplace: $currentMarketplace")
                
                // Clear any previous configuration errors
                if (_subscriptionState.value.purchaseError?.contains("configuration") == true) {
                    _subscriptionState.value = _subscriptionState.value.copy(purchaseError = null)
                }
            }
            UserDataResponse.RequestStatus.FAILED -> {
                Log.e(TAG, "Failed to get user data - possible security/configuration issue")
                _subscriptionState.value = _subscriptionState.value.copy(
                    purchaseError = "Development mode: Amazon services not available. Create subscription SKUs in Developer Console or test with Amazon App Tester."
                )
            }
            else -> {
                Log.w(TAG, "User data request not successful: ${response.requestStatus}")
                _subscriptionState.value = _subscriptionState.value.copy(
                    purchaseError = "Development mode: Amazon IAP services not fully available. This is normal during development."
                )
            }
        }
    }

    override fun onProductDataResponse(response: ProductDataResponse) {
        Log.d(TAG, "onProductDataResponse: ${response.requestStatus}")
        Log.d(TAG, "Request ID: ${response.requestId}")
        
        when (response.requestStatus) {
            ProductDataResponse.RequestStatus.SUCCESSFUL -> {
                val availableProducts = mutableMapOf<String, Product>()
                val unavailableSkus = mutableSetOf<String>()
                
                Log.d(TAG, "Product data response - Available: ${response.productData.size}, Unavailable: ${response.unavailableSkus.size}")
                
                for (product in response.productData.values) {
                    Log.d(TAG, "Available product: ${product.sku} - ${product.title} - ${product.price}")
                    Log.d(TAG, "  Product type: ${product.productType}")
                    Log.d(TAG, "  Description: ${product.description}")
                    availableProducts[product.sku] = product
                }
                
                for (sku in response.unavailableSkus) {
                    Log.w(TAG, "Unavailable SKU: $sku - This SKU is not configured in Developer Console or not live")
                    unavailableSkus.add(sku)
                }
                
                if (availableProducts.isEmpty() && unavailableSkus.isNotEmpty()) {
                    Log.e(TAG, "All SKUs are unavailable! Check Developer Console configuration.")
                    _subscriptionState.value = _subscriptionState.value.copy(
                        purchaseError = "Subscription products not configured. Please contact support."
                    )
                }
                
                _subscriptionState.value = _subscriptionState.value.copy(
                    availableProducts = availableProducts,
                    unavailableSkus = unavailableSkus
                )
            }
            ProductDataResponse.RequestStatus.FAILED -> {
                Log.e(TAG, "Failed to get product data")
                _subscriptionState.value = _subscriptionState.value.copy(
                    purchaseError = "Failed to load subscription options. Please try again."
                )
            }
            ProductDataResponse.RequestStatus.NOT_SUPPORTED -> {
                Log.e(TAG, "Product data request not supported")
                _subscriptionState.value = _subscriptionState.value.copy(
                    purchaseError = "In-app purchases not supported on this device."
                )
            }
        }
    }

    override fun onPurchaseResponse(response: PurchaseResponse) {
        Log.d(TAG, "onPurchaseResponse: ${response.requestStatus}")
        Log.d(TAG, "onPurchaseResponse - Request ID: ${response.requestId}")
        Log.d(TAG, "onPurchaseResponse - User ID: ${response.userData?.userId}")
        
        // Cancel timeout
        purchaseTimeoutJob?.cancel()
        
        // Clear purchasing state
        _subscriptionState.value = _subscriptionState.value.copy(isPurchasing = false)
        
        when (response.requestStatus) {
            PurchaseResponse.RequestStatus.SUCCESSFUL -> {
                val receipt = response.receipt
                Log.d(TAG, "Purchase successful: ${receipt.sku}")
                _subscriptionState.value = _subscriptionState.value.copy(purchaseError = null)
                handleReceipt(receipt)
            }
            PurchaseResponse.RequestStatus.ALREADY_PURCHASED -> {
                Log.d(TAG, "Already purchased: ${response.receipt.sku}")
                _subscriptionState.value = _subscriptionState.value.copy(purchaseError = null)
                handleReceipt(response.receipt)
            }
            PurchaseResponse.RequestStatus.INVALID_SKU -> {
                Log.e(TAG, "Invalid SKU in purchase response")
                _subscriptionState.value = _subscriptionState.value.copy(
                    purchaseError = "Invalid subscription plan. Please try again."
                )
            }
            PurchaseResponse.RequestStatus.FAILED -> {
                Log.e(TAG, "Purchase failed")
                _subscriptionState.value = _subscriptionState.value.copy(
                    purchaseError = "Purchase failed. Please check your payment method and try again."
                )
            }
            PurchaseResponse.RequestStatus.NOT_SUPPORTED -> {
                Log.e(TAG, "Purchase not supported")
                _subscriptionState.value = _subscriptionState.value.copy(
                    purchaseError = "Purchases are not supported on this device."
                )
            }
            PurchaseResponse.RequestStatus.PENDING -> {
                Log.d(TAG, "Purchase is pending")
                _subscriptionState.value = _subscriptionState.value.copy(
                    purchaseError = "Purchase is being processed. Please wait..."
                )
            }
        }
    }

    override fun onPurchaseUpdatesResponse(response: PurchaseUpdatesResponse) {
        Log.d(TAG, "onPurchaseUpdatesResponse: ${response.requestStatus}")
        
        when (response.requestStatus) {
            PurchaseUpdatesResponse.RequestStatus.SUCCESSFUL -> {
                currentUserId = response.userData.userId
                currentMarketplace = response.userData.marketplace
                
                Log.d(TAG, "Processing ${response.receipts.size} receipts")
                var foundActiveSubscription = false
                
                for (receipt in response.receipts) {
                    Log.d(TAG, "Receipt: SKU=${receipt.sku}, Type=${receipt.productType}, Canceled=${receipt.isCanceled}")
                    handleReceipt(receipt)
                    
                    // Check if this is an active subscription
                    if (receipt.productType == ProductType.SUBSCRIPTION && !receipt.isCanceled) {
                        foundActiveSubscription = true
                    }
                }
                
                // If we found an active subscription and were in purchasing state, clear it
                if (foundActiveSubscription && _subscriptionState.value.isPurchasing) {
                    Log.d(TAG, "Found active subscription during purchase check - clearing purchasing state")
                    purchaseTimeoutJob?.cancel()
                    _subscriptionState.value = _subscriptionState.value.copy(
                        isPurchasing = false,
                        purchaseError = null
                    )
                }
                
                // Check if there are more purchases to retrieve
                if (response.hasMore()) {
                    Log.d(TAG, "More purchases available, fetching...")
                    PurchasingService.getPurchaseUpdates(false)
                }
            }
            PurchaseUpdatesResponse.RequestStatus.FAILED -> {
                Log.e(TAG, "Failed to get purchase updates")
            }
            PurchaseUpdatesResponse.RequestStatus.NOT_SUPPORTED -> {
                Log.e(TAG, "Purchase updates not supported")
            }
        }
    }

    private fun handleReceipt(receipt: Receipt) {
        Log.d(TAG, "Handling receipt for SKU: ${receipt.sku}")
        
        when (receipt.productType) {
            ProductType.SUBSCRIPTION -> {
                handleSubscriptionReceipt(receipt)
            }
            ProductType.ENTITLED -> {
                // Handle one-time purchases if needed
                Log.d(TAG, "Entitled product: ${receipt.sku}")
            }
            ProductType.CONSUMABLE -> {
                // Handle consumable purchases if needed
                Log.d(TAG, "Consumable product: ${receipt.sku}")
                // For consumables, call notifyFulfillment after delivering the item
                PurchasingService.notifyFulfillment(receipt.receiptId, FulfillmentResult.FULFILLED)
            }
        }
    }

    private fun handleSubscriptionReceipt(receipt: Receipt) {
        Log.d(TAG, "Processing subscription receipt: ${receipt.sku}")
        Log.d(TAG, "Receipt ID: ${receipt.receiptId}")
        Log.d(TAG, "Is Canceled: ${receipt.isCanceled}")
        Log.d(TAG, "Purchase Date: ${receipt.purchaseDate}")
        
        // Check if subscription is active (not canceled)
        val isActive = when (receipt.sku) {
            PREMIUM_MONTHLY_SKU, PREMIUM_YEARLY_SKU, PREMIUM_FAMILY_SKU -> {
                // Subscription is active if:
                // 1. It's one of our subscription SKUs
                // 2. It's not canceled
                !receipt.isCanceled
            }
            else -> {
                Log.w(TAG, "Unknown subscription SKU: ${receipt.sku}")
                false
            }
        }
        
        if (isActive) {
            Log.d(TAG, "✓ Active subscription found: ${receipt.sku}")
            _subscriptionState.value = _subscriptionState.value.copy(
                hasActiveSubscription = true,
                activeSubscriptionSku = receipt.sku,
                purchaseDate = receipt.purchaseDate?.time
            )
        } else {
            Log.d(TAG, "✗ Subscription is canceled or invalid: ${receipt.sku}")
            // Only clear subscription if this was the active one
            if (_subscriptionState.value.activeSubscriptionSku == receipt.sku) {
                _subscriptionState.value = _subscriptionState.value.copy(
                    hasActiveSubscription = false,
                    activeSubscriptionSku = null,
                    purchaseDate = null
                )
            }
        }
    }

    /**
     * Data class to hold subscription state
     */
    data class SubscriptionState(
        val hasActiveSubscription: Boolean = false,
        val activeSubscriptionSku: String? = null,
        val purchaseDate: Long? = null,
        val availableProducts: Map<String, Product> = emptyMap(),
        val unavailableSkus: Set<String> = emptySet(),
        val isPurchasing: Boolean = false,
        val purchaseError: String? = null
    )
}