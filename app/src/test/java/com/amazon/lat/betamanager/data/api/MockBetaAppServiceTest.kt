package com.amazon.lat.betamanager.data.api

import com.amazon.lat.betamanager.data.model.AppStatus
import com.amazon.lat.betamanager.data.model.DownloadState
import com.amazon.lat.betamanager.data.model.IapType
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

/**
 * Unit tests for [MockBetaAppService].
 *
 * These tests verify the mock service contract, which serves as the specification
 * for what any real BetaAppService implementation must also satisfy.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class MockBetaAppServiceTest {

    private lateinit var service: MockBetaAppService

    @Before
    fun setUp() {
        service = MockBetaAppService()
    }

    // ── getBetaApps() ──

    @Test
    fun `getBetaApps returns 7 apps`() = runTest {
        val apps = service.getBetaApps()
        assertEquals(7, apps.size)
    }

    @Test
    fun `getBetaApps returns apps in all three states`() = runTest {
        val apps = service.getBetaApps()
        val stateCounts = apps.groupBy { it.status }.mapValues { it.value.size }

        assertEquals(2, stateCounts[AppStatus.UPDATE_AVAILABLE])
        assertEquals(2, stateCounts[AppStatus.INSTALLED])
        assertEquals(3, stateCounts[AppStatus.NOT_INSTALLED])
    }

    @Test
    fun `getBetaApps all apps have required fields populated`() = runTest {
        val apps = service.getBetaApps()
        for (app in apps) {
            assertTrue("App ${app.id} missing title", app.title.isNotBlank())
            assertTrue("App ${app.id} missing developer", app.developer.isNotBlank())
            assertTrue("App ${app.id} missing description", app.description.isNotBlank())
            assertTrue("App ${app.id} missing packageName", app.packageName.isNotBlank())
            assertTrue("App ${app.id} missing availableVersion", app.availableVersion.isNotBlank())
            assertTrue("App ${app.id} missing category", app.category.isNotBlank())
            assertTrue("App ${app.id} missing changelog", app.changelog.isNotBlank())
            assertTrue("App ${app.id} missing iconResName", app.iconResName?.isNotBlank() == true)
            assertTrue("App ${app.id} sizeBytes should be positive", app.sizeBytes > 0)
        }
    }

    @Test
    fun `getBetaApps installed apps have currentVersion set`() = runTest {
        val apps = service.getBetaApps()
        val installed = apps.filter { it.status == AppStatus.INSTALLED || it.status == AppStatus.UPDATE_AVAILABLE }
        for (app in installed) {
            assertNotNull("Installed app ${app.id} should have currentVersion", app.currentVersion)
        }
    }

    @Test
    fun `getBetaApps not-installed apps have null currentVersion`() = runTest {
        val apps = service.getBetaApps()
        val notInstalled = apps.filter { it.status == AppStatus.NOT_INSTALLED }
        for (app in notInstalled) {
            assertNull("Not-installed app ${app.id} should have null currentVersion", app.currentVersion)
        }
    }

    @Test
    fun `getBetaApps update-available apps have different current and available versions`() = runTest {
        val apps = service.getBetaApps()
        val updates = apps.filter { it.status == AppStatus.UPDATE_AVAILABLE }
        for (app in updates) {
            assertNotEquals(
                "App ${app.id}: currentVersion should differ from availableVersion",
                app.currentVersion, app.availableVersion
            )
        }
    }

    @Test
    fun `getBetaApps installed apps have matching current and available versions`() = runTest {
        val apps = service.getBetaApps()
        val installed = apps.filter { it.status == AppStatus.INSTALLED }
        for (app in installed) {
            assertEquals(
                "App ${app.id}: installed app should have matching versions",
                app.currentVersion, app.availableVersion
            )
        }
    }

    @Test
    fun `getBetaApps all app IDs are unique`() = runTest {
        val apps = service.getBetaApps()
        val ids = apps.map { it.id }
        assertEquals("App IDs should be unique", ids.size, ids.distinct().size)
    }

    @Test
    fun `getBetaApps all package names are unique`() = runTest {
        val apps = service.getBetaApps()
        val packages = apps.map { it.packageName }
        assertEquals("Package names should be unique", packages.size, packages.distinct().size)
    }

    // ── getAppDetails() ──

    @Test
    fun `getAppDetails returns correct app for valid ID`() = runTest {
        val app = service.getAppDetails("app_001")
        assertEquals("app_001", app.id)
        assertEquals("Weather Pro", app.title)
    }

    @Test(expected = NoSuchElementException::class)
    fun `getAppDetails throws for invalid ID`() = runTest {
        service.getAppDetails("nonexistent_app")
    }

    // ── getUpdates() ──

    @Test
    fun `getUpdates returns only update-available apps`() = runTest {
        val updates = service.getUpdates()
        assertEquals(2, updates.size)
        for (update in updates) {
            assertTrue("Update version should not be empty", update.toVersion.isNotBlank())
            assertTrue("Release notes should not be empty", update.releaseNotes.isNotBlank())
            assertTrue("Size should be positive", update.sizeBytes > 0)
        }
    }

    // ── downloadApp() ──

    @Test
    fun `downloadApp emits correct state sequence`() = runTest {
        val states = service.downloadApp("app_004").toList()

        // Should start with Downloading(0)
        assertTrue("First state should be Downloading(0)", states[0] is DownloadState.Downloading)
        assertEquals(0, (states[0] as DownloadState.Downloading).progressPercent)

        // Should have Installing state before Completed
        val installingIndex = states.indexOfFirst { it is DownloadState.Installing }
        val completedIndex = states.indexOfFirst { it is DownloadState.Completed }
        assertTrue("Should have Installing state", installingIndex >= 0)
        assertTrue("Should have Completed state", completedIndex >= 0)
        assertTrue("Installing should come before Completed", installingIndex < completedIndex)

        // Last state should be Completed
        assertTrue("Last state should be Completed", states.last() is DownloadState.Completed)
    }

    @Test
    fun `downloadApp changes app status to INSTALLED`() = runTest {
        // Verify initial state is NOT_INSTALLED
        val before = service.getAppDetails("app_004")
        assertEquals(AppStatus.NOT_INSTALLED, before.status)
        assertNull(before.currentVersion)

        // Download the app
        service.downloadApp("app_004").toList()

        // Verify state changed
        val after = service.getAppDetails("app_004")
        assertEquals(AppStatus.INSTALLED, after.status)
        assertEquals(before.availableVersion, after.currentVersion)
    }

    @Test
    fun `downloadApp for update-available app sets INSTALLED and updates version`() = runTest {
        val before = service.getAppDetails("app_001")
        assertEquals(AppStatus.UPDATE_AVAILABLE, before.status)
        assertEquals("2.3.0", before.currentVersion)

        service.downloadApp("app_001").toList()

        val after = service.getAppDetails("app_001")
        assertEquals(AppStatus.INSTALLED, after.status)
        assertEquals("2.4.0-beta.2", after.currentVersion)
    }

    @Test
    fun `downloadApp progress increases monotonically`() = runTest {
        val states = service.downloadApp("app_005").toList()
        val downloadStates = states.filterIsInstance<DownloadState.Downloading>()

        var prevProgress = -1
        for (state in downloadStates) {
            assertTrue(
                "Progress should increase: was $prevProgress, got ${state.progressPercent}",
                state.progressPercent > prevProgress
            )
            prevProgress = state.progressPercent
        }
        assertEquals("Download should reach 100%", 100, prevProgress)
    }

    // ── uninstallApp() ──

    @Test
    fun `uninstallApp changes status to NOT_INSTALLED`() = runTest {
        // Start with an installed app
        val before = service.getAppDetails("app_003")
        assertEquals(AppStatus.INSTALLED, before.status)

        val result = service.uninstallApp("app_003")
        assertTrue("Uninstall should succeed", result)

        val after = service.getAppDetails("app_003")
        assertEquals(AppStatus.NOT_INSTALLED, after.status)
        assertNull("currentVersion should be null after uninstall", after.currentVersion)
    }

    @Test
    fun `uninstallApp then reinstall works correctly`() = runTest {
        // Uninstall
        service.uninstallApp("app_003")
        val afterUninstall = service.getAppDetails("app_003")
        assertEquals(AppStatus.NOT_INSTALLED, afterUninstall.status)

        // Reinstall
        service.downloadApp("app_003").toList()
        val afterInstall = service.getAppDetails("app_003")
        assertEquals(AppStatus.INSTALLED, afterInstall.status)
        assertNotNull(afterInstall.currentVersion)
    }

    // ── getIapItems() ──

    @Test
    fun `getIapItems returns items for apps with IAPs`() = runTest {
        val items = service.getIapItems("app_003")
        assertEquals(3, items.size)

        // Verify all IAP types are represented
        val types = items.map { it.type }.toSet()
        assertTrue("Should have ENTITLEMENT", types.contains(IapType.ENTITLEMENT))
        assertTrue("Should have CONSUMABLE", types.contains(IapType.CONSUMABLE))
        assertTrue("Should have SUBSCRIPTION", types.contains(IapType.SUBSCRIPTION))
    }

    @Test
    fun `getIapItems returns empty for apps without IAPs`() = runTest {
        val items = service.getIapItems("app_004")
        assertTrue("Should be empty for apps without IAPs", items.isEmpty())
    }

    @Test
    fun `getIapItems items have valid fields`() = runTest {
        val items = service.getIapItems("app_003")
        for (item in items) {
            assertTrue("SKU should not be blank", item.sku.isNotBlank())
            assertTrue("Title should not be blank", item.title.isNotBlank())
            assertTrue("Price should not be blank", item.price.isNotBlank())
        }
    }

    // ── resetIaps() ──

    @Test
    fun `resetIaps returns true`() = runTest {
        val result = service.resetIaps("app_003")
        assertTrue("IAP reset should succeed", result)
    }

    // ── Notification Preferences ──

    @Test
    fun `getNotificationPreferences returns defaults`() = runTest {
        val prefs = service.getNotificationPreferences()
        assertTrue("Default: notify on update", prefs.notifyOnUpdate)
        assertTrue("Default: notify on invite", prefs.notifyOnNewInvite)
    }

    @Test
    fun `updateNotificationPreferences persists changes`() = runTest {
        val updated = com.amazon.lat.betamanager.data.model.NotificationPreference(
            notifyOnUpdate = false,
            notifyOnNewInvite = true
        )
        val result = service.updateNotificationPreferences(updated)
        assertTrue("Update should succeed", result)

        val fetched = service.getNotificationPreferences()
        assertFalse("notifyOnUpdate should be false", fetched.notifyOnUpdate)
        assertTrue("notifyOnNewInvite should be true", fetched.notifyOnNewInvite)
    }

    // ── State consistency ──

    @Test
    fun `getBetaApps reflects state changes from install and uninstall`() = runTest {
        // Initial state
        val initial = service.getBetaApps()
        val initialNotInstalled = initial.count { it.status == AppStatus.NOT_INSTALLED }

        // Install one app
        service.downloadApp("app_004").toList()

        val afterInstall = service.getBetaApps()
        val afterInstallNotInstalled = afterInstall.count { it.status == AppStatus.NOT_INSTALLED }
        assertEquals("One fewer NOT_INSTALLED after install", initialNotInstalled - 1, afterInstallNotInstalled)

        // Uninstall it
        service.uninstallApp("app_004")

        val afterUninstall = service.getBetaApps()
        val afterUninstallNotInstalled = afterUninstall.count { it.status == AppStatus.NOT_INSTALLED }
        assertEquals("Back to original NOT_INSTALLED count", initialNotInstalled, afterUninstallNotInstalled)
    }
}
