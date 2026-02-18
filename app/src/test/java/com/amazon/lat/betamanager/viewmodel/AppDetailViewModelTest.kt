package com.amazon.lat.betamanager.viewmodel

import androidx.arch.core.executor.testing.InstantTaskExecutorRule
import com.amazon.lat.betamanager.data.api.MockBetaAppService
import com.amazon.lat.betamanager.data.model.AppStatus
import com.amazon.lat.betamanager.data.model.DownloadState
import com.amazon.lat.betamanager.data.model.IapType
import com.amazon.lat.betamanager.data.repository.BetaAppRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Rule
import org.junit.Test

/**
 * Unit tests for [AppDetailViewModel].
 *
 * Tests the ViewModel that drives the detail screen including:
 * - Loading app details and IAP items
 * - Install/Update/Uninstall flows with download progress
 * - IAP reset
 */
@OptIn(ExperimentalCoroutinesApi::class)
class AppDetailViewModelTest {

    @get:Rule
    val instantExecutorRule = InstantTaskExecutorRule()

    private val testDispatcher = StandardTestDispatcher()
    private lateinit var service: MockBetaAppService
    private lateinit var repository: BetaAppRepository
    private lateinit var viewModel: AppDetailViewModel

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        service = MockBetaAppService()
        repository = BetaAppRepository(service)
        viewModel = AppDetailViewModel(repository)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    // ── loadApp() ──

    @Test
    fun `loadApp populates app details`() = runTest {
        viewModel.loadApp("app_001")
        advanceUntilIdle()

        val app = viewModel.app.value
        assertNotNull("App should be loaded", app)
        assertEquals("app_001", app!!.id)
        assertEquals("Weather Pro", app.title)
        assertEquals("SkyView Labs", app.developer)
        assertEquals(AppStatus.UPDATE_AVAILABLE, app.status)
    }

    @Test
    fun `loadApp populates IAP items for apps with IAPs`() = runTest {
        viewModel.loadApp("app_003")
        advanceUntilIdle()

        val items = viewModel.iapItems.value
        assertNotNull("IAP items should be loaded", items)
        assertEquals(3, items!!.size)
    }

    @Test
    fun `loadApp has empty IAP items for apps without IAPs`() = runTest {
        viewModel.loadApp("app_004")
        advanceUntilIdle()

        val items = viewModel.iapItems.value
        assertNotNull("IAP items should be loaded (empty)", items)
        assertTrue("Should be empty for apps without IAPs", items!!.isEmpty())
    }

    @Test
    fun `loadApp for not-installed app shows correct state`() = runTest {
        viewModel.loadApp("app_004")
        advanceUntilIdle()

        val app = viewModel.app.value!!
        assertEquals(AppStatus.NOT_INSTALLED, app.status)
        assertNull(app.currentVersion)
        assertTrue(app.availableVersion.isNotBlank())
    }

    // ── installApp() ──

    @Test
    fun `installApp changes app status to INSTALLED`() = runTest {
        viewModel.loadApp("app_004")
        advanceUntilIdle()

        assertEquals(AppStatus.NOT_INSTALLED, viewModel.app.value!!.status)

        viewModel.installApp("app_004")
        advanceUntilIdle()

        val app = viewModel.app.value!!
        assertEquals(AppStatus.INSTALLED, app.status)
        assertNotNull(app.currentVersion)
    }

    @Test
    fun `installApp resets download state to Idle after completion`() = runTest {
        viewModel.loadApp("app_004")
        advanceUntilIdle()

        viewModel.installApp("app_004")
        advanceUntilIdle()

        assertEquals(
            "Download state should reset to Idle after completion",
            DownloadState.Idle, viewModel.downloadState.value
        )
    }

    // ── updateApp() ──

    @Test
    fun `updateApp changes UPDATE_AVAILABLE to INSTALLED`() = runTest {
        viewModel.loadApp("app_001")
        advanceUntilIdle()

        assertEquals(AppStatus.UPDATE_AVAILABLE, viewModel.app.value!!.status)
        assertEquals("2.3.0", viewModel.app.value!!.currentVersion)

        viewModel.updateApp("app_001")
        advanceUntilIdle()

        val app = viewModel.app.value!!
        assertEquals(AppStatus.INSTALLED, app.status)
        assertEquals("2.4.0-beta.2", app.currentVersion)
    }

    // ── uninstallApp() ──

    @Test
    fun `uninstallApp changes status to NOT_INSTALLED`() = runTest {
        viewModel.loadApp("app_003")
        advanceUntilIdle()

        assertEquals(AppStatus.INSTALLED, viewModel.app.value!!.status)

        viewModel.uninstallApp("app_003")
        advanceUntilIdle()

        val app = viewModel.app.value!!
        assertEquals(AppStatus.NOT_INSTALLED, app.status)
        assertNull(app.currentVersion)
    }

    // ── resetIaps() ──

    @Test
    fun `resetIaps reports success`() = runTest {
        viewModel.loadApp("app_003")
        advanceUntilIdle()

        viewModel.resetIaps("app_003")
        advanceUntilIdle()

        assertEquals(true, viewModel.iapResetSuccess.value)
    }

    @Test
    fun `clearIapResetStatus clears the status`() = runTest {
        viewModel.loadApp("app_003")
        advanceUntilIdle()

        viewModel.resetIaps("app_003")
        advanceUntilIdle()

        assertEquals(true, viewModel.iapResetSuccess.value)

        viewModel.clearIapResetStatus()
        assertNull(viewModel.iapResetSuccess.value)
    }

    @Test
    fun `resetIaps refreshes IAP items`() = runTest {
        viewModel.loadApp("app_003")
        advanceUntilIdle()

        val itemsBefore = viewModel.iapItems.value
        assertNotNull(itemsBefore)

        viewModel.resetIaps("app_003")
        advanceUntilIdle()

        // IAP items should still be populated after reset
        val itemsAfter = viewModel.iapItems.value
        assertNotNull(itemsAfter)
        assertEquals(3, itemsAfter!!.size)
    }

    // ── Initial state ──

    @Test
    fun `initial download state is Idle`() {
        assertEquals(DownloadState.Idle, viewModel.downloadState.value)
    }

    @Test
    fun `initial app is null before loadApp`() {
        assertNull(viewModel.app.value)
    }

    @Test
    fun `initial iapResetSuccess is null`() {
        assertNull(viewModel.iapResetSuccess.value)
    }

    // ── Full lifecycle: install then uninstall ──

    @Test
    fun `full lifecycle install then uninstall`() = runTest {
        // Load a not-installed app
        viewModel.loadApp("app_005")
        advanceUntilIdle()
        assertEquals(AppStatus.NOT_INSTALLED, viewModel.app.value!!.status)

        // Install it
        viewModel.installApp("app_005")
        advanceUntilIdle()
        assertEquals(AppStatus.INSTALLED, viewModel.app.value!!.status)
        assertEquals("2.0.0-beta.1", viewModel.app.value!!.currentVersion)

        // Uninstall it
        viewModel.uninstallApp("app_005")
        advanceUntilIdle()
        assertEquals(AppStatus.NOT_INSTALLED, viewModel.app.value!!.status)
        assertNull(viewModel.app.value!!.currentVersion)
    }
}
