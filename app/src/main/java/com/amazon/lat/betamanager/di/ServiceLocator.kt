package com.amazon.lat.betamanager.di

import com.amazon.lat.betamanager.data.api.AuthManager
import com.amazon.lat.betamanager.data.api.BetaAppService
import com.amazon.lat.betamanager.data.api.MockBetaAppService
import com.amazon.lat.betamanager.data.repository.BetaAppRepository

/**
 * =====================================================================================
 * ServiceLocator — Lightweight dependency injection for Beta App Manager.
 * =====================================================================================
 *
 * Provides all dependencies used throughout the app. Uses lazy initialization
 * so objects are created only when first accessed.
 *
 * ## How to Switch from Mock to Real APIs
 *
 * 1. Create: data/api/RealBetaAppService.kt implementing BetaAppService
 *    - Constructor: RealBetaAppService(authManager: AuthManager, context: Context)
 *    - See BetaAppService.kt for detailed API endpoint documentation
 *
 * 2. Change: useMockApi = false (below)
 *
 * 3. Update: betaAppService lazy block to construct RealBetaAppService
 *    with proper dependencies (authManager, application context, OkHttpClient)
 *
 * 4. Enable: LWA SDK dependency in app/build.gradle:
 *    implementation files('libs/login-with-amazon-sdk.jar')
 *
 * 5. Update: AuthManager to use real LWA SDK calls (see TODOs in AuthManager.kt)
 *
 * ## Architecture
 *
 * ServiceLocator (DI root)
 *   ├── betaAppService: BetaAppService       ← Mock or Real API implementation
 *   ├── authManager: AuthManager             ← LWA SSO auth (mock or real)
 *   ├── betaAppRepository: BetaAppRepository ← Caching + coordination layer
 *   └── viewModelFactory: ViewModelFactory   ← Creates ViewModels with dependencies
 * =====================================================================================
 */
object ServiceLocator {

    /**
     * Master toggle for mock vs real API.
     *
     * TODO: Set to false when real Amazon Appstore APIs are integrated.
     * Consider making this a BuildConfig field for different build variants:
     *   buildConfigField("boolean", "USE_MOCK_API", "false")
     */
    private const val useMockApi = true

    /**
     * The API service implementation.
     *
     * When [useMockApi] is true: uses [MockBetaAppService] with hardcoded sample data.
     * When false: should use RealBetaAppService backed by Amazon Appstore cloud + device APIs.
     */
    val betaAppService: BetaAppService by lazy {
        if (useMockApi) {
            MockBetaAppService()
        } else {
            // TODO: Replace with real implementation:
            // RealBetaAppService(
            //     authManager = authManager,
            //     httpClient = OkHttpClient.Builder()
            //         .addInterceptor(AuthInterceptor(authManager))
            //         .connectTimeout(30, TimeUnit.SECONDS)
            //         .readTimeout(30, TimeUnit.SECONDS)
            //         .build(),
            //     context = applicationContext  // needs Application reference
            // )
            MockBetaAppService()
        }
    }

    /**
     * Authentication manager for Login with Amazon (LWA) SSO.
     *
     * TODO: When integrating real LWA, the AuthManager will need a Context
     * parameter for RequestContext initialization. Update this to:
     *   AuthManager(applicationContext)
     */
    val authManager: AuthManager by lazy {
        AuthManager()
    }

    /**
     * Repository layer that coordinates API calls and provides caching.
     * ViewModels should always go through this, never call betaAppService directly.
     */
    val betaAppRepository: BetaAppRepository by lazy {
        BetaAppRepository(betaAppService)
    }

    /**
     * Factory for creating ViewModels with their required dependencies.
     * Used by ViewModelProvider in Fragment/Activity code.
     */
    val viewModelFactory: ViewModelFactory by lazy {
        ViewModelFactory(betaAppRepository, authManager)
    }
}
