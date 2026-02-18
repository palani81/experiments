package com.amazon.lat.betamanager.data.repository

import com.amazon.lat.betamanager.data.api.MockBetaAppService
import com.amazon.lat.betamanager.data.model.AppStatus
import com.amazon.lat.betamanager.data.model.DownloadState
import com.amazon.lat.betamanager.data.model.NotificationPreference
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

/**
 * Unit tests for [BetaAppRepository].
 *
 * Tests the repository layer which handles caching, filtering, and
 * coordination between ViewModels and the BetaAppService.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class BetaAppRepositoryTest {

    private lateinit var service: MockBetaAppService
    private lateinit var repository: BetaAppRepository

    @Before
    fun setUp() {
        service = MockBetaAppService()
        repository = BetaAppRepository(service)
    }

    // ── Row classification: No overlap between categories ──

    @Test
    fun `app categories are mutually exclusive - no app appears in multiple rows`() = runTest {
        val updates = repository.getUpdatesAvailable().map { it.id }.toSet()
        val installed = repository.getInstalledApps().map { it.id }.toSet()
        val available = repository.getAvailableApps().map { it.id }.toSet()

        // No overlap between any two categories
        assertTrue("Updates and Installed should not overlap",
            updates.intersect(installed).isEmpty())
        assertTrue("Updates and Available should not overlap",
            updates.intersect(available).isEmpty())
        assertTrue("Installed and Available should not overlap",
            installed.intersect(available).isEmpty())
    }

    @Test
    fun `all apps accounted for in exactly one category`() = runTest {
        val allApps = repository.getBetaApps()
        val updates = repository.getUpdatesAvailable()
        val installed = repository.getInstalledApps()
        val available = repository.getAvailableApps()

        assertEquals(
            "Sum of categories should equal total apps",
            allApps.size,
            updates.size + installed.size + available.size
        )
    }

    // ── getUpdatesAvailable() ──

    @Test
    fun `getUpdatesAvailable returns only UPDATE_AVAILABLE apps`() = runTest {
        val updates = repository.getUpdatesAvailable()
        assertTrue("Should have updates", updates.isNotEmpty())
        for (app in updates) {
            assertEquals(AppStatus.UPDATE_AVAILABLE, app.status)
        }
    }

    @Test
    fun `getUpdatesAvailable apps have different current and available versions`() = runTest {
        val updates = repository.getUpdatesAvailable()
        for (app in updates) {
            assertNotNull("Update app should have currentVersion", app.currentVersion)
            assertNotEquals("Versions should differ", app.currentVersion, app.availableVersion)
        }
    }

    // ── getInstalledApps() ──

    @Test
    fun `getInstalledApps returns only INSTALLED apps`() = runTest {
        val installed = repository.getInstalledApps()
        assertTrue("Should have installed apps", installed.isNotEmpty())
        for (app in installed) {
            assertEquals(AppStatus.INSTALLED, app.status)
        }
    }

    @Test
    fun `getInstalledApps does NOT include UPDATE_AVAILABLE apps`() = runTest {
        val installed = repository.getInstalledApps()
        for (app in installed) {
            assertNotEquals(
                "Installed row should not include apps with updates",
                AppStatus.UPDATE_AVAILABLE, app.status
            )
        }
    }

    @Test
    fun `getInstalledApps apps have matching current and available versions`() = runTest {
        val installed = repository.getInstalledApps()
        for (app in installed) {
            assertEquals(
                "Installed (up-to-date) app should have matching versions",
                app.currentVersion, app.availableVersion
            )
        }
    }

    // ── getAvailableApps() ──

    @Test
    fun `getAvailableApps returns only NOT_INSTALLED apps`() = runTest {
        val available = repository.getAvailableApps()
        assertTrue("Should have available apps", available.isNotEmpty())
        for (app in available) {
            assertEquals(AppStatus.NOT_INSTALLED, app.status)
        }
    }

    // ── Caching ──

    @Test
    fun `getBetaApps uses cache on second call`() = runTest {
        val first = repository.getBetaApps()
        val second = repository.getBetaApps()
        // Both should return the same list instance (cached)
        assertSame("Second call should return cached list", first, second)
    }

    @Test
    fun `getBetaApps forceRefresh bypasses cache`() = runTest {
        val first = repository.getBetaApps()
        val second = repository.getBetaApps(forceRefresh = true)
        // forceRefresh creates a new list from service
        assertNotSame("Force refresh should create new list", first, second)
        // But content should be the same
        assertEquals("Content should match", first.size, second.size)
    }

    // ── State changes ──

    @Test
    fun `downloadApp invalidates cache`() = runTest {
        // Load initial data into cache
        val initial = repository.getBetaApps()

        // Download an app (should invalidate cache)
        repository.downloadApp("app_004").toList()

        // Next call should fetch fresh data (new list object)
        val after = repository.getBetaApps()
        assertNotSame("Cache should be invalidated after download", initial, after)
    }

    @Test
    fun `uninstallApp invalidates cache`() = runTest {
        val initial = repository.getBetaApps()

        repository.uninstallApp("app_003")

        val after = repository.getBetaApps()
        assertNotSame("Cache should be invalidated after uninstall", initial, after)
    }

    @Test
    fun `after install, app moves from Available to Installed`() = runTest {
        // Before: app_004 should be in Available, not in Installed
        val beforeAvailable = repository.getAvailableApps().map { it.id }
        assertTrue("app_004 should be available before install", beforeAvailable.contains("app_004"))

        // Install
        repository.downloadApp("app_004").toList()

        // After: app_004 should be in Installed, not in Available
        val afterAvailable = repository.getAvailableApps().map { it.id }
        val afterInstalled = repository.getInstalledApps().map { it.id }
        assertFalse("app_004 should NOT be available after install", afterAvailable.contains("app_004"))
        assertTrue("app_004 should be installed after install", afterInstalled.contains("app_004"))
    }

    @Test
    fun `after uninstall, app moves from Installed to Available`() = runTest {
        // Before: app_003 should be installed
        val beforeInstalled = repository.getInstalledApps().map { it.id }
        assertTrue("app_003 should be installed", beforeInstalled.contains("app_003"))

        // Uninstall
        repository.uninstallApp("app_003")

        // After: app_003 should be in Available
        val afterInstalled = repository.getInstalledApps().map { it.id }
        val afterAvailable = repository.getAvailableApps().map { it.id }
        assertFalse("app_003 should NOT be installed after uninstall", afterInstalled.contains("app_003"))
        assertTrue("app_003 should be available after uninstall", afterAvailable.contains("app_003"))
    }

    @Test
    fun `after update, app moves from Updates to Installed`() = runTest {
        // Before: app_001 has update available
        val beforeUpdates = repository.getUpdatesAvailable().map { it.id }
        assertTrue("app_001 should have update", beforeUpdates.contains("app_001"))

        // Update (same as install)
        repository.downloadApp("app_001").toList()

        // After: app_001 should be in Installed, not Updates
        val afterUpdates = repository.getUpdatesAvailable().map { it.id }
        val afterInstalled = repository.getInstalledApps().map { it.id }
        assertFalse("app_001 should NOT have update after updating", afterUpdates.contains("app_001"))
        assertTrue("app_001 should be installed after updating", afterInstalled.contains("app_001"))
    }

    // ── Download progress ──

    @Test
    fun `downloadApp emits progress states`() = runTest {
        val states = repository.downloadApp("app_005").toList()
        assertTrue("Should have multiple states", states.size > 3)
        assertTrue("Should start with Downloading", states.first() is DownloadState.Downloading)
        assertTrue("Should end with Completed", states.last() is DownloadState.Completed)
    }

    // ── IAP operations ──

    @Test
    fun `getIapItems returns items for app with IAPs`() = runTest {
        val items = repository.getIapItems("app_003")
        assertTrue("RecipeBox should have IAP items", items.isNotEmpty())
    }

    @Test
    fun `getIapItems returns empty for app without IAPs`() = runTest {
        val items = repository.getIapItems("app_007")
        assertTrue("RetroArcade should have no IAP items", items.isEmpty())
    }

    @Test
    fun `resetIaps succeeds`() = runTest {
        val result = repository.resetIaps("app_003")
        assertTrue("IAP reset should succeed", result)
    }

    // ── Notification preferences ──

    @Test
    fun `notification preferences round-trip works`() = runTest {
        // Get defaults
        val defaults = repository.getNotificationPreferences()
        assertTrue(defaults.notifyOnUpdate)
        assertTrue(defaults.notifyOnNewInvite)

        // Update
        val newPrefs = NotificationPreference(notifyOnUpdate = false, notifyOnNewInvite = false)
        repository.updateNotificationPreferences(newPrefs)

        // Verify
        val updated = repository.getNotificationPreferences()
        assertFalse(updated.notifyOnUpdate)
        assertFalse(updated.notifyOnNewInvite)
    }

    // ── getAppDetails() ──

    @Test
    fun `getAppDetails returns correct app`() = runTest {
        val app = repository.getAppDetails("app_001")
        assertEquals("app_001", app.id)
        assertEquals("Weather Pro", app.title)
        assertEquals("SkyView Labs", app.developer)
    }

    @Test
    fun `getAppDetails reflects state changes after install`() = runTest {
        // Install app_004
        repository.downloadApp("app_004").toList()

        // Detail should show installed state
        val app = repository.getAppDetails("app_004")
        assertEquals(AppStatus.INSTALLED, app.status)
        assertNotNull(app.currentVersion)
    }
}
