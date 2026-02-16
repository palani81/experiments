package com.kidshield.tv.domain.model

data class UsageRecord(
    val packageName: String,
    val appName: String,
    val date: String,
    val minutesUsed: Int,
    val limitMinutes: Int?
)
