package com.kidshield.tv.data

import com.kidshield.tv.domain.model.AgeProfile
import com.kidshield.tv.domain.model.AppCategory

object KnownStreamingApps {

    data class KnownApp(
        val packageName: String,
        val displayName: String,
        val category: AppCategory,
        val defaultAgeProfile: AgeProfile = AgeProfile.ALL,
        val isKidsVariant: Boolean = false,
        val hasBuiltInParentalControls: Boolean = false,
        val setupGuideAvailable: Boolean = false
    )

    val apps = listOf(
        // ── YouTube ──────────────────────────────────────────────
        KnownApp(
            packageName = "com.google.android.youtube.tv",
            displayName = "YouTube",
            category = AppCategory.STREAMING,
            hasBuiltInParentalControls = true,
            setupGuideAvailable = true
        ),
        KnownApp(
            packageName = "com.amazon.firetv.youtube",
            displayName = "YouTube",
            category = AppCategory.STREAMING,
            hasBuiltInParentalControls = true,
            setupGuideAvailable = true
        ),
        KnownApp(
            packageName = "com.google.android.youtube.tvkids",
            displayName = "YouTube Kids",
            category = AppCategory.STREAMING,
            defaultAgeProfile = AgeProfile.CHILD,
            isKidsVariant = true
        ),
        KnownApp(
            packageName = "com.amazon.firetv.youtube.kids",
            displayName = "YouTube Kids",
            category = AppCategory.STREAMING,
            defaultAgeProfile = AgeProfile.CHILD,
            isKidsVariant = true
        ),
        // ── Netflix ──────────────────────────────────────────────
        KnownApp(
            packageName = "com.netflix.ninja",
            displayName = "Netflix",
            category = AppCategory.STREAMING,
            hasBuiltInParentalControls = true,
            setupGuideAvailable = true
        ),
        // ── JioHotstar ───────────────────────────────────────────
        KnownApp(
            packageName = "in.startv.hotstar",
            displayName = "JioHotstar",
            category = AppCategory.STREAMING,
            hasBuiltInParentalControls = true,
            setupGuideAvailable = true
        ),
        KnownApp(
            packageName = "in.startv.hotstar.dplus.tv",
            displayName = "JioHotstar",
            category = AppCategory.STREAMING,
            hasBuiltInParentalControls = true,
            setupGuideAvailable = true
        ),
        // ── Prime Video ──────────────────────────────────────────
        KnownApp(
            packageName = "com.amazon.avod",
            displayName = "Prime Video",
            category = AppCategory.STREAMING,
            hasBuiltInParentalControls = true
        ),
        KnownApp(
            packageName = "com.amazon.firetv.pvod",
            displayName = "Prime Video",
            category = AppCategory.STREAMING,
            hasBuiltInParentalControls = true
        ),
        // ── Disney+ ─────────────────────────────────────────────
        KnownApp(
            packageName = "com.disney.disneyplus",
            displayName = "Disney+",
            category = AppCategory.STREAMING,
            hasBuiltInParentalControls = true
        ),
        KnownApp(
            packageName = "com.disney.disneyplus.tv",
            displayName = "Disney+",
            category = AppCategory.STREAMING,
            hasBuiltInParentalControls = true
        ),
        // ── Apple TV+ ───────────────────────────────────────────
        KnownApp(
            packageName = "com.apple.atve.androidtv.appletv",
            displayName = "Apple TV+",
            category = AppCategory.STREAMING
        ),
        // ── SonyLIV ─────────────────────────────────────────────
        KnownApp(
            packageName = "com.sonyliv",
            displayName = "SonyLIV",
            category = AppCategory.STREAMING
        ),
        // ── ZEE5 ────────────────────────────────────────────────
        KnownApp(
            packageName = "com.graymatrix.did",
            displayName = "ZEE5",
            category = AppCategory.STREAMING
        ),
        // ── MX Player ───────────────────────────────────────────
        KnownApp(
            packageName = "com.mxtech.videoplayer.ad",
            displayName = "MX Player",
            category = AppCategory.STREAMING
        ),
    )

    fun findByPackage(pkg: String): KnownApp? = apps.find { it.packageName == pkg }

    /**
     * Returns all known package names that map to the same app.
     * e.g. "YouTube" → ["com.google.android.youtube.tv", "com.amazon.firetv.youtube"]
     * Useful for treating Fire TV / Android TV variants as the same app for time limits.
     */
    fun findVariants(displayName: String): List<KnownApp> =
        apps.filter { it.displayName == displayName }

    /** All unique display names (deduplicates Fire TV / Android TV variants). */
    val uniqueAppNames: List<String>
        get() = apps.map { it.displayName }.distinct()
}
