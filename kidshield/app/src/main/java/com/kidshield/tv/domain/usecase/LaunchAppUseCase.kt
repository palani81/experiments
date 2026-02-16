package com.kidshield.tv.domain.usecase

import android.content.Context
import android.content.Intent
import com.kidshield.tv.data.local.db.dao.TimeLimitDao
import com.kidshield.tv.data.repository.AppRepository
import com.kidshield.tv.data.repository.UsageRepository
import dagger.hilt.android.qualifiers.ApplicationContext
import java.time.LocalTime
import javax.inject.Inject

class LaunchAppUseCase @Inject constructor(
    private val appRepository: AppRepository,
    private val usageRepository: UsageRepository,
    private val timeLimitDao: TimeLimitDao,
    @ApplicationContext private val context: Context
) {
    sealed class LaunchResult {
        data object Success : LaunchResult()
        data class TimeLimitReached(val appName: String) : LaunchResult()
        data class NotAllowed(val reason: String) : LaunchResult()
        data class OutsideSchedule(val allowedStart: String, val allowedEnd: String) : LaunchResult()
        data class AppNotInstalled(val packageName: String) : LaunchResult()
    }

    suspend operator fun invoke(packageName: String): LaunchResult {
        // Check if app is allowed
        val app = appRepository.getApp(packageName)
            ?: return LaunchResult.AppNotInstalled(packageName)
        if (!app.isAllowed) return LaunchResult.NotAllowed("App is not in the allowlist")

        // Check time-of-day schedule
        val timeLimit = timeLimitDao.getTimeLimitForAppOnce(packageName)
        if (timeLimit != null) {
            val now = LocalTime.now()
            val start = timeLimit.allowedStartTime?.let { LocalTime.parse(it) }
            val end = timeLimit.allowedEndTime?.let { LocalTime.parse(it) }
            if (start != null && end != null && (now.isBefore(start) || now.isAfter(end))) {
                return LaunchResult.OutsideSchedule(start.toString(), end.toString())
            }

            // Check allowed days of week
            val today = java.time.LocalDate.now().dayOfWeek.value
            val allowedDays = timeLimit.allowedDaysOfWeek.split(",").mapNotNull { it.trim().toIntOrNull() }
            if (allowedDays.isNotEmpty() && today !in allowedDays) {
                return LaunchResult.NotAllowed("Not available today")
            }
        }

        // Check daily time limit
        val todayUsage = usageRepository.getTodayUsage(packageName)
        val dailyLimit = timeLimit?.dailyLimitMinutes ?: Int.MAX_VALUE
        if (todayUsage >= dailyLimit) {
            return LaunchResult.TimeLimitReached(app.displayName)
        }

        // Launch the app
        val launchIntent = context.packageManager.getLaunchIntentForPackage(packageName)
        if (launchIntent != null) {
            launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(launchIntent)
            return LaunchResult.Success
        }
        return LaunchResult.AppNotInstalled(packageName)
    }
}
