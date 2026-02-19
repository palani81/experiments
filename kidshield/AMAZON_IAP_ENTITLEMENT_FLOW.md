# Amazon IAP Entitlement Flow

## Overview

This document explains how KidShield handles subscription entitlements using Amazon's IAP APIs to ensure users get access to premium features even if purchase callbacks fail.

## Amazon IAP APIs Used

### 1. `PurchasingService.getPurchaseUpdates(reset: Boolean)`

**Purpose**: Retrieves all active purchases/subscriptions for the current user.

**When to use**:
- App startup (with `reset = true`)
- Before initiating a new purchase (with `reset = false`)
- When app resumes from background (with `reset = false`)
- After purchase timeout (with `reset = false`)

**Returns**: `onPurchaseUpdatesResponse()` callback with list of receipts

### 2. `PurchasingService.purchase(sku: String)`

**Purpose**: Initiates a purchase flow for a specific SKU.

**Returns**: `onPurchaseResponse()` callback with purchase result

### 3. Receipt Properties

Each receipt contains:
- `sku`: The subscription SKU
- `receiptId`: Unique receipt identifier
- `productType`: SUBSCRIPTION, ENTITLED, or CONSUMABLE
- `isCanceled`: Whether subscription is canceled
- `purchaseDate`: When the purchase was made

## Entitlement Flow

### Scenario 1: Normal Purchase Flow

```
1. User clicks "Subscribe"
2. App calls getPurchaseUpdates(false) to check existing entitlements
3. If no existing subscription, call purchase(sku)
4. Amazon shows purchase dialog
5. User completes purchase
6. onPurchaseResponse() called with SUCCESSFUL
7. handleReceipt() grants entitlement
8. User gets premium access
```

### Scenario 2: Purchase Succeeds But Callback Fails

```
1. User clicks "Subscribe"
2. App calls getPurchaseUpdates(false) to check existing entitlements
3. Call purchase(sku)
4. Amazon shows purchase dialog
5. User completes purchase
6. ❌ onPurchaseResponse() NOT called (Amazon bug/network issue)
7. App shows "Processing..." for 2 minutes
8. Timeout triggers
9. App calls getPurchaseUpdates(false) again
10. onPurchaseUpdatesResponse() receives the new receipt
11. handleReceipt() grants entitlement
12. User gets premium access
```

### Scenario 3: User Returns to App After Purchase

```
1. User clicks "Subscribe"
2. Amazon dialog opens (app goes to background)
3. User completes purchase in Amazon
4. User presses back/home to return to app
5. MainActivity.onResume() called
6. App calls getPurchaseUpdates(false)
7. onPurchaseUpdatesResponse() receives the receipt
8. handleReceipt() grants entitlement
9. Purchasing state cleared
10. User gets premium access immediately
```

### Scenario 4: Already Subscribed

```
1. User clicks "Subscribe"
2. App calls getPurchaseUpdates(false)
3. onPurchaseUpdatesResponse() finds existing active subscription
4. App shows "You already have an active subscription"
5. Purchase not initiated
```

## Implementation Details

### Before Purchase Check

```kotlin
fun purchaseSubscription(sku: String) {
    // Check for existing entitlements FIRST
    PurchasingService.getPurchaseUpdates(false)
    
    // Verify not already subscribed
    if (hasActiveSubscription && activeSubscriptionSku == sku) {
        showError("Already subscribed")
        return
    }
    
    // Proceed with purchase
    PurchasingService.purchase(sku)
}
```

### Timeout Handler with Retry

```kotlin
purchaseTimeoutJob = coroutineScope.launch {
    delay(120000) // 2 minutes
    
    if (isPurchasing) {
        // Try to refresh entitlements one more time
        PurchasingService.getPurchaseUpdates(false)
        delay(2000) // Wait for response
        
        if (still isPurchasing) {
            showTimeoutError()
        }
    }
}
```

### Receipt Processing

```kotlin
private fun handleSubscriptionReceipt(receipt: Receipt) {
    val isActive = !receipt.isCanceled && 
                   receipt.sku in [MONTHLY, YEARLY, FAMILY]
    
    if (isActive) {
        // Grant entitlement
        hasActiveSubscription = true
        activeSubscriptionSku = receipt.sku
        
        // Clear purchasing state if in progress
        if (isPurchasing) {
            isPurchasing = false
            cancelTimeout()
        }
    }
}
```

### App Resume Handler

```kotlin
override fun onResume() {
    super.onResume()
    
    // Always refresh purchase status when app resumes
    iapManager.refreshPurchaseStatus()
}

fun refreshPurchaseStatus() {
    // Cancel any pending timeout
    purchaseTimeoutJob?.cancel()
    
    // Clear stuck purchasing state
    if (isPurchasing) {
        isPurchasing = false
    }
    
    // Fetch latest purchases from Amazon
    PurchasingService.getPurchaseUpdates(false)
}
```

## Key Benefits

1. **Resilient**: Works even if `onPurchaseResponse()` fails
2. **Immediate**: Grants access as soon as receipt is found
3. **Accurate**: Always checks Amazon's source of truth
4. **User-Friendly**: No manual refresh needed
5. **Prevents Duplicates**: Checks before allowing purchase

## Testing Scenarios

### Test 1: Normal Purchase
- Click subscribe → Complete purchase → Verify immediate access

### Test 2: Slow Network
- Click subscribe → Wait 2+ minutes → Verify timeout → Verify access granted after timeout

### Test 3: App Backgrounded
- Click subscribe → Switch to Amazon → Complete → Return to app → Verify immediate access

### Test 4: Already Subscribed
- Have active subscription → Click subscribe → Verify blocked with message

### Test 5: Canceled Subscription
- Cancel subscription → Wait for cancellation → Verify access removed

## Amazon Documentation References

- [IAP Overview](https://developer.amazon.com/docs/in-app-purchasing/iap-overview.html)
- [getPurchaseUpdates](https://developer.amazon.com/docs/in-app-purchasing/iap-implement-iap.html#getpurchaseupdates)
- [Receipt Verification](https://developer.amazon.com/docs/in-app-purchasing/iap-rvs-for-android-apps.html)

## Summary

By calling `getPurchaseUpdates()` at strategic points (before purchase, on timeout, on resume), we ensure users always get their entitlements even when Amazon's callbacks fail. This provides a robust, user-friendly subscription experience.
