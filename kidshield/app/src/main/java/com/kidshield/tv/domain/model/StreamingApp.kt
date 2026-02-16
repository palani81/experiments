package com.kidshield.tv.domain.model

import android.graphics.drawable.Drawable

data class StreamingApp(
    val packageName: String,
    val displayName: String,
    val isInstalled: Boolean,
    val isAllowed: Boolean,
    val category: AppCategory,
    val iconDrawable: Drawable?,
    val ageProfile: AgeProfile,
    val isKidsVariant: Boolean,
    val dailyMinutesRemaining: Int?,
    val dailyLimitMinutes: Int?
)
