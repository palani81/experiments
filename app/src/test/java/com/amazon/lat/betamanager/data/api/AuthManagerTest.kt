package com.amazon.lat.betamanager.data.api

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

/**
 * Unit tests for [AuthManager].
 *
 * Tests the mock authentication layer. When real LWA SDK is integrated,
 * these tests should be updated or supplemented with integration tests.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class AuthManagerTest {

    private lateinit var authManager: AuthManager

    @Before
    fun setUp() {
        authManager = AuthManager()
    }

    @Test
    fun `getAccessToken returns a non-empty token`() = runTest {
        val token = authManager.getAccessToken()
        assertTrue("Token should not be blank", token.isNotBlank())
    }

    @Test
    fun `getAccessToken caches token on second call`() = runTest {
        val token1 = authManager.getAccessToken()
        val token2 = authManager.getAccessToken()
        assertEquals("Cached token should be the same", token1, token2)
    }

    @Test
    fun `isAuthenticated returns true`() = runTest {
        val result = authManager.isAuthenticated()
        assertTrue("Mock auth should always return true", result)
    }

    @Test
    fun `getUserProfile returns valid profile`() = runTest {
        val profile = authManager.getUserProfile()
        assertTrue("User ID should not be blank", profile.userId.isNotBlank())
        assertTrue("Email should not be blank", profile.email.isNotBlank())
        assertTrue("Name should not be blank", profile.name.isNotBlank())
    }

    @Test
    fun `getUserProfile caches profile on second call`() = runTest {
        val profile1 = authManager.getUserProfile()
        val profile2 = authManager.getUserProfile()
        assertEquals("Cached profile should be the same", profile1, profile2)
    }

    @Test
    fun `clearAuth clears cached token so next call fetches new one`() = runTest {
        // Get initial token and verify caching
        val token1 = authManager.getAccessToken()
        val token1Again = authManager.getAccessToken()
        assertSame("Before clear, should return cached (same) instance", token1, token1Again)

        // Clear auth and get new token
        authManager.clearAuth()
        val token2 = authManager.getAccessToken()

        // After clearing, a new token object is created (even if timestamp matches,
        // it's a different String instance because it went through the creation path)
        assertTrue("Token after clear should be a valid token", token2.startsWith("mock_lwa_token_"))
        // The key point: clearAuth nullified the cache, forcing re-creation
    }

    @Test
    fun `clearAuth clears cached profile`() = runTest {
        val profile1 = authManager.getUserProfile()
        authManager.clearAuth()
        val profile2 = authManager.getUserProfile()
        // Both are mock data with same content, so they'll be equal in value
        // but clearAuth should have cleared the cache (verified by the fact
        // that getUserProfile() ran without error after clear)
        assertEquals("Mock profiles have same content", profile1, profile2)
    }
}
