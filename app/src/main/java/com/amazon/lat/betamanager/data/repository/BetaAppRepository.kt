package com.amazon.lat.betamanager.data.repository

import com.amazon.lat.betamanager.data.api.BetaAppService
import com.amazon.lat.betamanager.data.model.*
import kotlinx.coroutines.flow.Flow

/**
 * Repository layer that coordinates data access between the UI (ViewModels)
 * and the API layer (BetaAppService).
 *
 * Provides:
 * - In-memory caching of app list to avoid redundant API calls
 * - Filtering logic to separate apps into UI rows (updates, installed, available)
 * - Cache invalidation on state-changing operations (install, uninstall)
 *
 * The repository is agnostic to whether [service] is mock or real — it works
 * identically with either implementation.
 *
 * ## Row Classification Logic
 *
 * Apps are classified into three browse rows:
 * - "Updates Available"  → status == UPDATE_AVAILABLE (installed but newer version exists)
 * - "Installed Beta Apps" → status == INSTALLED (installed and fully up-to-date)
 * - "Available to Test"   → status == NOT_INSTALLED (invited but not yet installed)
 *
 * This ensures no app appears in multiple rows.
 */
class BetaAppRepository(private val service: BetaAppService) {

    private var cachedApps: List<BetaApp>? = null

    /**
     * Fetch all beta apps the user is invited to test.
     * Uses in-memory cache unless [forceRefresh] is true.
     */
    suspend fun getBetaApps(forceRefresh: Boolean = false): List<BetaApp> {
        if (!forceRefresh) {
            cachedApps?.let { return it }
        }
        val apps = service.getBetaApps()
        cachedApps = apps
        return apps
    }

    /**
     * Get detailed info for a single app. Always calls service (no caching)
     * to ensure fresh data after state changes.
     */
    suspend fun getAppDetails(appId: String): BetaApp {
        return service.getAppDetails(appId)
    }

    /**
     * Apps that are installed but have a newer beta version available.
     * Displayed in the "Updates Available" row on the main screen.
     */
    suspend fun getUpdatesAvailable(): List<BetaApp> {
        val apps = getBetaApps()
        return apps.filter { it.status == AppStatus.UPDATE_AVAILABLE }
    }

    /**
     * Apps that are installed and fully up-to-date (no pending update).
     * Displayed in the "Installed Beta Apps" row on the main screen.
     *
     * NOTE: Only includes INSTALLED status, NOT UPDATE_AVAILABLE.
     * Apps with updates appear only in the "Updates Available" row.
     */
    suspend fun getInstalledApps(): List<BetaApp> {
        val apps = getBetaApps()
        return apps.filter { it.status == AppStatus.INSTALLED }
    }

    /**
     * Apps the user has been invited to test but hasn't installed yet.
     * Displayed in the "Available to Test" row on the main screen.
     */
    suspend fun getAvailableApps(): List<BetaApp> {
        val apps = getBetaApps()
        return apps.filter { it.status == AppStatus.NOT_INSTALLED }
    }

    /**
     * Trigger download and installation. Invalidates cache since app state will change.
     * @return Flow emitting download/install progress
     */
    fun downloadApp(appId: String): Flow<DownloadState> {
        invalidateCache()
        return service.downloadApp(appId)
    }

    /**
     * Uninstall an app. Invalidates cache on success since app state changed.
     */
    suspend fun uninstallApp(appId: String): Boolean {
        val result = service.uninstallApp(appId)
        if (result) invalidateCache()
        return result
    }

    /**
     * Get IAP items for an app (for the Reset IAPs feature).
     */
    suspend fun getIapItems(appId: String): List<IapItem> {
        return service.getIapItems(appId)
    }

    /**
     * Reset all IAP purchases for an app so the tester can re-test purchase flows.
     */
    suspend fun resetIaps(appId: String): Boolean {
        return service.resetIaps(appId)
    }

    /**
     * Get user's notification preferences (update alerts, new invite alerts).
     */
    suspend fun getNotificationPreferences(): NotificationPreference {
        return service.getNotificationPreferences()
    }

    /**
     * Update notification preferences.
     */
    suspend fun updateNotificationPreferences(prefs: NotificationPreference): Boolean {
        return service.updateNotificationPreferences(prefs)
    }

    /**
     * Clear cached data so next fetch goes to the service.
     * Called after any state-changing operation.
     */
    private fun invalidateCache() {
        cachedApps = null
    }
}
