package com.amazon.lat.betamanager.data.model

data class BetaApp(
    val id: String,
    val packageName: String,
    val title: String,
    val developer: String,
    val description: String,
    val iconUrl: String,
    /** Drawable resource name for local icon (used in mock mode). */
    val iconResName: String? = null,
    val currentVersion: String?,
    val availableVersion: String,
    val status: AppStatus,
    val category: String,
    val lastUpdated: Long,
    val changelog: String,
    val screenshots: List<String>,
    val sizeBytes: Long
)

enum class AppStatus {
    INSTALLED,
    UPDATE_AVAILABLE,
    NOT_INSTALLED
}
