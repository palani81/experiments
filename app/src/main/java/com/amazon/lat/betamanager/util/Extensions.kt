package com.amazon.lat.betamanager.util

import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

fun Long.toRelativeTimeString(): String {
    val now = System.currentTimeMillis()
    val diff = now - this
    return when {
        diff < 60_000L -> "just now"
        diff < 3_600_000L -> "${diff / 60_000L}m ago"
        diff < 86_400_000L -> "${diff / 3_600_000L}h ago"
        diff < 604_800_000L -> "${diff / 86_400_000L}d ago"
        else -> {
            val sdf = SimpleDateFormat("MMM d, yyyy", Locale.US)
            sdf.format(Date(this))
        }
    }
}

fun Long.toFormattedSize(): String {
    return when {
        this < 1_000_000L -> "%.1f KB".format(this / 1_000.0)
        this < 1_000_000_000L -> "%.1f MB".format(this / 1_000_000.0)
        else -> "%.2f GB".format(this / 1_000_000_000.0)
    }
}
