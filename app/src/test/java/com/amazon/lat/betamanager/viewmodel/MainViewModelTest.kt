package com.amazon.lat.betamanager.viewmodel

import androidx.arch.core.executor.testing.InstantTaskExecutorRule
import com.amazon.lat.betamanager.data.api.MockBetaAppService
import com.amazon.lat.betamanager.data.model.AppStatus
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
 * Unit tests for [MainViewModel].
 *
 * Tests the ViewModel that drives the main browse screen with three rows:
 * - Updates Available
 * - Installed Beta Apps
 * - Available to Test
 */
@OptIn(ExperimentalCoroutinesApi::class)
class MainViewModelTest {

    @get:Rule
    val instantExecutorRule = InstantTaskExecutorRule()

    private val testDispatcher = StandardTestDispatcher()
    private lateinit var service: MockBetaAppService
    private lateinit var repository: BetaAppRepository
    private lateinit var viewModel: MainViewModel

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        service = MockBetaAppService()
        repository = BetaAppRepository(service)
        viewModel = MainViewModel(repository)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `init loads all three app categories`() = runTest {
        advanceUntilIdle()

        val updates = viewModel.updatesAvailable.value
        val installed = viewModel.installedApps.value
        val available = viewModel.availableApps.value

        assertNotNull("Updates should not be null", updates)
        assertNotNull("Installed should not be null", installed)
        assertNotNull("Available should not be null", available)

        assertEquals(2, updates!!.size)
        assertEquals(2, installed!!.size)
        assertEquals(3, available!!.size)
    }

    @Test
    fun `updatesAvailable contains only UPDATE_AVAILABLE apps`() = runTest {
        advanceUntilIdle()

        val updates = viewModel.updatesAvailable.value!!
        for (app in updates) {
            assertEquals(AppStatus.UPDATE_AVAILABLE, app.status)
        }
    }

    @Test
    fun `installedApps contains only INSTALLED apps`() = runTest {
        advanceUntilIdle()

        val installed = viewModel.installedApps.value!!
        for (app in installed) {
            assertEquals(AppStatus.INSTALLED, app.status)
        }
    }

    @Test
    fun `availableApps contains only NOT_INSTALLED apps`() = runTest {
        advanceUntilIdle()

        val available = viewModel.availableApps.value!!
        for (app in available) {
            assertEquals(AppStatus.NOT_INSTALLED, app.status)
        }
    }

    @Test
    fun `no app appears in multiple categories`() = runTest {
        advanceUntilIdle()

        val updateIds = viewModel.updatesAvailable.value!!.map { it.id }.toSet()
        val installedIds = viewModel.installedApps.value!!.map { it.id }.toSet()
        val availableIds = viewModel.availableApps.value!!.map { it.id }.toSet()

        assertTrue("Updates and Installed overlap", updateIds.intersect(installedIds).isEmpty())
        assertTrue("Updates and Available overlap", updateIds.intersect(availableIds).isEmpty())
        assertTrue("Installed and Available overlap", installedIds.intersect(availableIds).isEmpty())
    }

    @Test
    fun `total apps across all categories equals 7`() = runTest {
        advanceUntilIdle()

        val total = viewModel.updatesAvailable.value!!.size +
                viewModel.installedApps.value!!.size +
                viewModel.availableApps.value!!.size

        assertEquals(7, total)
    }

    @Test
    fun `refresh reloads data`() = runTest {
        advanceUntilIdle()

        // Verify initial state
        assertNotNull(viewModel.updatesAvailable.value)

        // Trigger refresh
        viewModel.refresh()
        advanceUntilIdle()

        // Data should still be present and correct
        assertEquals(2, viewModel.updatesAvailable.value!!.size)
        assertEquals(2, viewModel.installedApps.value!!.size)
        assertEquals(3, viewModel.availableApps.value!!.size)
    }

    @Test
    fun `isLoading is false after load completes`() = runTest {
        advanceUntilIdle()
        assertEquals(false, viewModel.isLoading.value)
    }

    @Test
    fun `error is null on successful load`() = runTest {
        advanceUntilIdle()
        assertNull(viewModel.error.value)
    }
}
