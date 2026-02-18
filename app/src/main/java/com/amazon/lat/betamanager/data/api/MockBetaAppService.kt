package com.amazon.lat.betamanager.data.api

import com.amazon.lat.betamanager.data.model.*
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow

/**
 * Mock implementation of [BetaAppService] for development and testing.
 *
 * Provides 7 sample beta apps in various states:
 * - 2 apps with UPDATE_AVAILABLE (Weather Pro, FitTrack TV)
 * - 2 apps INSTALLED and up-to-date (RecipeBox, PhotoFrame Pro)
 * - 3 apps NOT_INSTALLED (LearnPlay Kids, BeatStream, RetroArcade)
 *
 * All methods include simulated network delays to mimic real API latency.
 * State changes (install/uninstall) are persisted in-memory for the session.
 *
 * =====================================================================================
 * WHEN REPLACING WITH REAL API:
 *
 * 1. Create RealBetaAppService.kt implementing BetaAppService
 * 2. Constructor should accept: AuthManager, OkHttpClient, Context (for PackageManager)
 * 3. Each method maps to a REST endpoint or on-device API (see BetaAppService docs)
 * 4. JSON parsing: use Gson or kotlinx.serialization to map responses to data models
 * 5. Error handling: wrap in try/catch, throw descriptive exceptions
 * 6. In ServiceLocator.kt, change: useMockApi = false
 *
 * Example skeleton:
 *   class RealBetaAppService(
 *       private val authManager: AuthManager,
 *       private val httpClient: OkHttpClient,
 *       private val context: Context
 *   ) : BetaAppService {
 *       private val baseUrl = "https://developer.amazon.com/api/appstore"
 *       private val gson = Gson()
 *
 *       override suspend fun getBetaApps(): List<BetaApp> {
 *           val token = authManager.getAccessToken()
 *           val request = Request.Builder()
 *               .url("$baseUrl/beta/apps")
 *               .addHeader("Authorization", "Bearer $token")
 *               .build()
 *           val response = httpClient.newCall(request).await()
 *           val body = response.body?.string() ?: throw IOException("Empty response")
 *           val cloudApps = gson.fromJson(body, Array<CloudBetaApp>::class.java)
 *           return cloudApps.map { it.toBetaApp(context.packageManager) }
 *       }
 *       // ... etc
 *   }
 * =====================================================================================
 */
class MockBetaAppService : BetaAppService {

    private var notificationPrefs = NotificationPreference()

    /**
     * In-memory list of mock beta apps. Mutable so install/uninstall can update state.
     *
     * REAL API NOTE: The real service would not hold state — it would fetch fresh data
     * from the cloud API each time, then cross-reference with PackageManager for
     * local install state.
     */
    private val mockApps = mutableListOf(
        BetaApp(
            id = "app_001",
            packageName = "com.example.weatherpro",
            title = "Weather Pro",
            developer = "SkyView Labs",
            description = "A next-generation weather app with real-time radar, hourly forecasts, and severe weather alerts. This beta includes the new animated radar overlay and redesigned 10-day forecast widget.",
            iconUrl = "mock://weather_pro_icon",
            iconResName = "ic_app_weather",
            currentVersion = "2.3.0",
            availableVersion = "2.4.0-beta.2",
            status = AppStatus.UPDATE_AVAILABLE,
            category = "Weather",
            lastUpdated = System.currentTimeMillis() - 86400000L, // 1 day ago
            changelog = "- New animated radar overlay\n- Redesigned 10-day forecast widget\n- Fixed location accuracy on Fire TV Stick 4K\n- Improved accessibility for D-pad navigation",
            screenshots = listOf("mock://weather_ss1", "mock://weather_ss2"),
            sizeBytes = 45_000_000L
        ),
        BetaApp(
            id = "app_002",
            packageName = "com.example.fitnesstracker",
            title = "FitTrack TV",
            developer = "HealthTech Inc.",
            description = "Follow guided workout videos on your big screen. Track progress, set goals, and sync with your phone. Beta includes new yoga routines and improved voice control.",
            iconUrl = "mock://fittrack_icon",
            iconResName = "ic_app_fitness",
            currentVersion = "1.1.0",
            availableVersion = "1.2.0-beta.1",
            status = AppStatus.UPDATE_AVAILABLE,
            category = "Health & Fitness",
            lastUpdated = System.currentTimeMillis() - 172800000L, // 2 days ago
            changelog = "- Added 15 new yoga routines\n- Voice control for hands-free workout navigation\n- Bug fix: timer not pausing on remote menu press",
            screenshots = listOf("mock://fit_ss1", "mock://fit_ss2", "mock://fit_ss3"),
            sizeBytes = 120_000_000L
        ),
        BetaApp(
            id = "app_003",
            packageName = "com.example.recipebox",
            title = "RecipeBox",
            developer = "CookSmart Studios",
            description = "Browse thousands of recipes with step-by-step video instructions optimized for your TV. New beta features include voice-guided cooking mode and shopping list sync.",
            iconUrl = "mock://recipebox_icon",
            iconResName = "ic_app_recipe",
            currentVersion = "3.0.1",
            availableVersion = "3.0.1",
            status = AppStatus.INSTALLED,
            category = "Food & Drink",
            lastUpdated = System.currentTimeMillis() - 604800000L, // 1 week ago
            changelog = "- Voice-guided cooking mode\n- Shopping list syncs to Alexa app\n- Performance improvements for older Fire TV devices",
            screenshots = listOf("mock://recipe_ss1"),
            sizeBytes = 67_000_000L
        ),
        BetaApp(
            id = "app_004",
            packageName = "com.example.kidseducation",
            title = "LearnPlay Kids",
            developer = "EduFun Games",
            description = "Educational games for kids ages 3-8. Math, reading, and science activities with parental controls. This beta adds the new Space Explorer mini-game.",
            iconUrl = "mock://learnplay_icon",
            iconResName = "ic_app_education",
            currentVersion = null,
            availableVersion = "4.1.0-beta.3",
            status = AppStatus.NOT_INSTALLED,
            category = "Education",
            lastUpdated = System.currentTimeMillis() - 259200000L, // 3 days ago
            changelog = "- New Space Explorer mini-game\n- Parental dashboard redesign\n- Fixed audio overlap in phonics module",
            screenshots = listOf("mock://learn_ss1", "mock://learn_ss2"),
            sizeBytes = 200_000_000L
        ),
        BetaApp(
            id = "app_005",
            packageName = "com.example.musicstreamer",
            title = "BeatStream",
            developer = "AudioWave Media",
            description = "Stream millions of songs in high-fidelity audio on your Fire TV. Features visualizers, lyrics display, and Alexa integration. Beta includes Dolby Atmos support.",
            iconUrl = "mock://beatstream_icon",
            iconResName = "ic_app_music",
            currentVersion = null,
            availableVersion = "2.0.0-beta.1",
            status = AppStatus.NOT_INSTALLED,
            category = "Music",
            lastUpdated = System.currentTimeMillis() - 432000000L, // 5 days ago
            changelog = "- Dolby Atmos spatial audio support\n- Real-time lyrics display\n- Improved Alexa voice commands\n- Visualizer themes",
            screenshots = listOf("mock://beat_ss1", "mock://beat_ss2", "mock://beat_ss3"),
            sizeBytes = 35_000_000L
        ),
        BetaApp(
            id = "app_006",
            packageName = "com.example.photoslideshow",
            title = "PhotoFrame Pro",
            developer = "PixelPerfect Apps",
            description = "Turn your Fire TV into a digital photo frame. Supports Amazon Photos, Google Photos, and local media. Beta features include Ken Burns effect and ambient mode.",
            iconUrl = "mock://photoframe_icon",
            iconResName = "ic_app_photo",
            currentVersion = "1.5.2",
            availableVersion = "1.5.2",
            status = AppStatus.INSTALLED,
            category = "Photography",
            lastUpdated = System.currentTimeMillis() - 1209600000L, // 2 weeks ago
            changelog = "- Ken Burns pan/zoom effect\n- Ambient mode with clock overlay\n- Support for HEIF image format",
            screenshots = listOf("mock://photo_ss1"),
            sizeBytes = 28_000_000L
        ),
        BetaApp(
            id = "app_007",
            packageName = "com.example.retrogames",
            title = "RetroArcade",
            developer = "PixelNostalgia",
            description = "Classic arcade-style games optimized for Fire TV game controllers. Includes leaderboards, achievements, and local multiplayer. Beta adds 5 new retro titles.",
            iconUrl = "mock://retroarcade_icon",
            iconResName = "ic_app_games",
            currentVersion = null,
            availableVersion = "1.0.0-beta.5",
            status = AppStatus.NOT_INSTALLED,
            category = "Games",
            lastUpdated = System.currentTimeMillis() - 86400000L, // 1 day ago
            changelog = "- 5 new retro game titles\n- Game controller mapping improvements\n- Local 2-player split screen\n- Leaderboard integration",
            screenshots = listOf("mock://retro_ss1", "mock://retro_ss2"),
            sizeBytes = 150_000_000L
        )
    )

    /**
     * Mock IAP items for 3 of the apps. Demonstrates all three IAP types.
     *
     * REAL API NOTE: IAP data comes from either:
     * - Cloud API: GET /beta/apps/{appId}/iap (server-side purchase records)
     * - Amazon IAP SDK: PurchasingService.getProductData() + getPurchaseUpdates()
     */
    private val mockIapItems = mapOf(
        "app_003" to listOf(
            IapItem("sku_premium", "Premium Recipes", "$4.99", IapType.ENTITLEMENT, System.currentTimeMillis() - 2592000000L),
            IapItem("sku_hints", "Cooking Hints (10 pack)", "$0.99", IapType.CONSUMABLE, System.currentTimeMillis() - 86400000L),
            IapItem("sku_monthly", "Monthly Meal Plans", "$2.99/mo", IapType.SUBSCRIPTION, System.currentTimeMillis() - 604800000L)
        ),
        "app_006" to listOf(
            IapItem("sku_themes", "Premium Themes", "$1.99", IapType.ENTITLEMENT, System.currentTimeMillis() - 1209600000L),
            IapItem("sku_cloud", "Cloud Storage 50GB", "$0.99/mo", IapType.SUBSCRIPTION, null)
        ),
        "app_002" to listOf(
            IapItem("sku_pro_workouts", "Pro Workout Pack", "$9.99", IapType.ENTITLEMENT, null),
            IapItem("sku_energy", "Energy Boost (consumable)", "$0.49", IapType.CONSUMABLE, System.currentTimeMillis() - 172800000L)
        )
    )

    /**
     * MOCK: Returns all 7 sample apps after 800ms simulated latency.
     *
     * REAL API: GET /beta/apps → parse JSON → cross-reference PackageManager for install state.
     */
    override suspend fun getBetaApps(): List<BetaApp> {
        delay(800)
        return mockApps.toList()
    }

    /**
     * MOCK: Returns a single app by ID after 400ms.
     *
     * REAL API: GET /beta/apps/{appId} or find from cached list.
     */
    override suspend fun getAppDetails(appId: String): BetaApp {
        delay(400)
        return mockApps.first { it.id == appId }
    }

    /**
     * MOCK: Filters mock apps with UPDATE_AVAILABLE status.
     *
     * REAL API: Could be a dedicated endpoint or derived from getBetaApps().
     */
    override suspend fun getUpdates(): List<AppUpdate> {
        delay(600)
        return mockApps
            .filter { it.status == AppStatus.UPDATE_AVAILABLE }
            .map { app ->
                AppUpdate(
                    appId = app.id,
                    fromVersion = app.currentVersion ?: "unknown",
                    toVersion = app.availableVersion,
                    releaseNotes = app.changelog,
                    sizeBytes = app.sizeBytes,
                    releaseDate = app.lastUpdated
                )
            }
    }

    /**
     * MOCK: Simulates download progress (0→100%), installation phase, then completion.
     * Updates internal state BEFORE emitting Completed so getAppDetails() returns
     * the updated state immediately.
     *
     * REAL API: Trigger Amazon Appstore download intent, then listen for broadcast
     * events (DOWNLOAD_PROGRESS, INSTALL_STARTED, INSTALL_COMPLETE, INSTALL_FAILED)
     * and emit corresponding DownloadState values.
     */
    override fun downloadApp(appId: String): Flow<DownloadState> = flow {
        emit(DownloadState.Downloading(0))
        for (progress in 10..90 step 10) {
            delay(300)
            emit(DownloadState.Downloading(progress))
        }
        delay(200)
        emit(DownloadState.Downloading(100))
        delay(500)
        emit(DownloadState.Installing)
        delay(1500)

        // Update mock data BEFORE emitting Completed
        val index = mockApps.indexOfFirst { it.id == appId }
        if (index >= 0) {
            val app = mockApps[index]
            mockApps[index] = app.copy(
                status = AppStatus.INSTALLED,
                currentVersion = app.availableVersion
            )
        }

        emit(DownloadState.Completed)
    }

    /**
     * MOCK: Simulates uninstall, updates in-memory state.
     *
     * REAL API: Use PackageManager uninstall intent or PackageInstaller API.
     * Then verify via PackageManager.getPackageInfo() that it's gone.
     */
    override suspend fun uninstallApp(appId: String): Boolean {
        delay(1000)
        val index = mockApps.indexOfFirst { it.id == appId }
        if (index >= 0) {
            val app = mockApps[index]
            mockApps[index] = app.copy(
                status = AppStatus.NOT_INSTALLED,
                currentVersion = null
            )
        }
        return true
    }

    /**
     * MOCK: Returns hardcoded IAP items for known app IDs.
     *
     * REAL API: GET /beta/apps/{appId}/iap or use Amazon IAP SDK locally.
     */
    override suspend fun getIapItems(appId: String): List<IapItem> {
        delay(500)
        return mockIapItems[appId] ?: emptyList()
    }

    /**
     * MOCK: Always returns true after 1.2s delay.
     *
     * REAL API: POST /beta/apps/{appId}/iap/reset to clear purchase records.
     * Or use Amazon App Tester intent for local reset.
     */
    override suspend fun resetIaps(appId: String): Boolean {
        delay(1200)
        return true
    }

    /**
     * MOCK: Returns in-memory notification preferences.
     *
     * REAL API: GET /beta/notifications or use local SharedPreferences.
     */
    override suspend fun getNotificationPreferences(): NotificationPreference {
        delay(300)
        return notificationPrefs
    }

    /**
     * MOCK: Updates in-memory preferences.
     *
     * REAL API: PUT /beta/notifications or save to local SharedPreferences.
     */
    override suspend fun updateNotificationPreferences(prefs: NotificationPreference): Boolean {
        delay(400)
        notificationPrefs = prefs
        return true
    }
}
