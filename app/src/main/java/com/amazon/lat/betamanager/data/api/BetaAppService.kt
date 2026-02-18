package com.amazon.lat.betamanager.data.api

import com.amazon.lat.betamanager.data.model.*
import kotlinx.coroutines.flow.Flow

/**
 * =====================================================================================
 * BetaAppService — Central API interface for all Beta App Manager operations.
 * =====================================================================================
 *
 * This interface defines every backend operation the app needs. Currently backed by
 * [MockBetaAppService] with hardcoded sample data. When real Amazon Appstore APIs are
 * ready, create a new class (e.g. [RealBetaAppService]) implementing this interface
 * and flip [ServiceLocator.useMockApi] to false.
 *
 * ## API Integration Strategy
 *
 * There are two categories of APIs this app will consume:
 *
 * ### 1. Cloud APIs (authenticated REST calls)
 * These require a valid LWA access token in the Authorization header.
 * Base URL (likely): https://developer.amazon.com/api/appstore/
 * Auth: Bearer token from [AuthManager.getAccessToken]
 *
 * Expected endpoints:
 * - GET  /beta/apps              → getBetaApps()        — List beta apps user is invited to
 * - GET  /beta/apps/{appId}      → getAppDetails()      — Single app details
 * - GET  /beta/apps/updates      → getUpdates()         — Apps with newer versions available
 * - POST /beta/apps/{appId}/iap/reset → resetIaps()     — Reset IAP purchases for testing
 * - GET  /beta/apps/{appId}/iap  → getIapItems()        — List IAP items for an app
 * - GET  /beta/notifications     → getNotificationPreferences()
 * - PUT  /beta/notifications     → updateNotificationPreferences()
 *
 * ### 2. On-Device APIs (Amazon Appstore APK on Fire TV)
 * These interact with the locally installed Amazon Appstore app via:
 * - ContentProvider queries (content://com.amazon.venezia.provider/...)
 * - Broadcast intents (com.amazon.intent.action.INSTALL_PACKAGE)
 * - PackageManager (for install/uninstall state queries)
 *
 * Expected on-device operations:
 * - downloadApp()  → Trigger download via Appstore; monitor via BroadcastReceiver
 * - uninstallApp() → PackageManager or intent-based uninstall
 * - App install state → PackageManager.getPackageInfo()
 *
 * ## How to Implement Real APIs
 *
 * 1. Create: data/api/RealBetaAppService.kt implementing this interface
 * 2. Inject: AuthManager for access tokens, OkHttpClient for HTTP calls
 * 3. Map:    JSON responses to existing data models (BetaApp, AppUpdate, etc.)
 * 4. Toggle: ServiceLocator.useMockApi = false
 *
 * See [MockBetaAppService] for the exact contract each method must fulfill.
 * =====================================================================================
 */
interface BetaAppService {

    /**
     * Fetch all beta apps the current user has been invited to test.
     *
     * TODO API: GET /beta/apps
     * Headers: Authorization: Bearer {lwa_token}
     * Response: JSON array of app objects → map to List<BetaApp>
     *
     * The response should include apps in ALL states (installed, update available,
     * not installed). The client-side repository handles filtering into rows.
     *
     * On-device enrichment: After fetching the cloud list, cross-reference with
     * PackageManager to determine actual install state and current version:
     *   - pm.getPackageInfo(packageName, 0).versionName → currentVersion
     *   - If installed & cloud version > local version → UPDATE_AVAILABLE
     *   - If installed & versions match → INSTALLED
     *   - If not installed → NOT_INSTALLED
     */
    suspend fun getBetaApps(): List<BetaApp>

    /**
     * Get detailed info for a specific beta app.
     *
     * TODO API: GET /beta/apps/{appId}
     * Headers: Authorization: Bearer {lwa_token}
     * Response: Single app JSON object → BetaApp
     *
     * This is called when navigating to the detail screen and after state changes
     * (install/uninstall/update) to refresh the UI.
     */
    suspend fun getAppDetails(appId: String): BetaApp

    /**
     * Get list of apps with available updates.
     *
     * TODO API: GET /beta/apps/updates
     * Headers: Authorization: Bearer {lwa_token}
     * Response: JSON array of update objects → List<AppUpdate>
     *
     * Alternative: This could be derived client-side from getBetaApps() by comparing
     * local version (PackageManager) with cloud version. The dedicated endpoint
     * may be unnecessary if getBetaApps() returns version info.
     */
    suspend fun getUpdates(): List<AppUpdate>

    /**
     * Download and install a beta app. Returns a flow of download progress.
     *
     * TODO DEVICE API: This is an ON-DEVICE operation using the Amazon Appstore APK.
     *
     * Implementation approach:
     * 1. Send install intent to Amazon Appstore:
     *    Intent("com.amazon.intent.action.INSTALL_PACKAGE").apply {
     *        putExtra("packageName", packageName)
     *        putExtra("versionCode", targetVersionCode)
     *    }
     *
     * 2. Register BroadcastReceiver for progress:
     *    - com.amazon.intent.action.DOWNLOAD_PROGRESS → Downloading(percent)
     *    - com.amazon.intent.action.INSTALL_STARTED   → Installing
     *    - com.amazon.intent.action.INSTALL_COMPLETE  → Completed
     *    - com.amazon.intent.action.INSTALL_FAILED    → Failed(reason)
     *
     * 3. Emit states via Flow<DownloadState> as broadcasts arrive.
     *
     * Alternative: Use Amazon Appstore's PackageInstaller API if available.
     *
     * @return Flow emitting download/install progress states
     */
    fun downloadApp(appId: String): Flow<DownloadState>

    /**
     * Uninstall a beta app from the device.
     *
     * TODO DEVICE API: Use PackageManager or uninstall intent:
     *   Intent(Intent.ACTION_DELETE, Uri.parse("package:$packageName"))
     *   // or for silent uninstall (if system-level permission):
     *   packageInstaller.uninstall(packageName, statusReceiver)
     *
     * @return true if uninstall was successful
     */
    suspend fun uninstallApp(appId: String): Boolean

    /**
     * Get IAP items associated with a beta app.
     *
     * TODO API: GET /beta/apps/{appId}/iap
     * Headers: Authorization: Bearer {lwa_token}
     * Response: JSON array of IAP item objects → List<IapItem>
     *
     * This retrieves the catalog of in-app purchase items for the app,
     * including their purchase state (for reset functionality).
     *
     * Alternative: May use Amazon IAP SDK locally:
     *   PurchasingService.getPurchaseUpdates(false)
     *   PurchasingService.getProductData(skuSet)
     */
    suspend fun getIapItems(appId: String): List<IapItem>

    /**
     * Reset all in-app purchases for a beta app (for testing).
     *
     * TODO API: POST /beta/apps/{appId}/iap/reset
     * Headers: Authorization: Bearer {lwa_token}
     * Body: {} (empty or { "skus": ["all"] })
     * Response: { "success": true }
     *
     * This is a CLOUD operation that clears the user's IAP purchase records
     * on Amazon's backend so the tester can re-purchase items during testing.
     *
     * Alternative: May use Amazon App Tester tool's API if available locally:
     *   Intent("com.amazon.sdktool.iap.reset").putExtra("packageName", pkg)
     *
     * @return true if IAP reset was successful
     */
    suspend fun resetIaps(appId: String): Boolean

    /**
     * Get the user's notification preferences.
     *
     * TODO API: GET /beta/notifications
     * Headers: Authorization: Bearer {lwa_token}
     * Response: { "notifyOnUpdate": true, "notifyOnNewInvite": true }
     *
     * Alternative: Could be stored locally via SharedPreferences if
     * server-side notification preferences are not supported.
     */
    suspend fun getNotificationPreferences(): NotificationPreference

    /**
     * Update the user's notification preferences.
     *
     * TODO API: PUT /beta/notifications
     * Headers: Authorization: Bearer {lwa_token}
     * Body: { "notifyOnUpdate": true, "notifyOnNewInvite": false }
     * Response: { "success": true }
     *
     * Alternative: Could be stored locally via SharedPreferences.
     *
     * @return true if preferences were updated successfully
     */
    suspend fun updateNotificationPreferences(prefs: NotificationPreference): Boolean
}
