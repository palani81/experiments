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
        KnownApp(
            packageName = "com.google.android.youtube.tv",
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
            packageName = "com.netflix.ninja",
            displayName = "Netflix",
            category = AppCategory.STREAMING,
            hasBuiltInParentalControls = true,
            setupGuideAvailable = true
        ),
        KnownApp(
            packageName = "in.startv.hotstar",
            displayName = "JioHotstar",
            category = AppCategory.STREAMING,
            hasBuiltInParentalControls = true,
            setupGuideAvailable = true
        ),
        KnownApp(
            packageName = "com.amazon.avod",
            displayName = "Prime Video",
            category = AppCategory.STREAMING,
            hasBuiltInParentalControls = true
        ),
        KnownApp(
            packageName = "com.disney.disneyplus",
            displayName = "Disney+",
            category = AppCategory.STREAMING,
            hasBuiltInParentalControls = true
        ),
        KnownApp(
            packageName = "com.apple.atve.androidtv.appletv",
            displayName = "Apple TV+",
            category = AppCategory.STREAMING
        ),
        KnownApp(
            packageName = "com.sonyliv",
            displayName = "SonyLIV",
            category = AppCategory.STREAMING
        ),
        KnownApp(
            packageName = "com.graymatrix.did",
            displayName = "ZEE5",
            category = AppCategory.STREAMING
        ),
        KnownApp(
            packageName = "com.mxtech.videoplayer.ad",
            displayName = "MX Player",
            category = AppCategory.STREAMING
        ),
    )

    fun findByPackage(pkg: String): KnownApp? = apps.find { it.packageName == pkg }
}
