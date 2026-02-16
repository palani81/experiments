package com.kidshield.tv.domain.usecase

import com.kidshield.tv.data.local.db.dao.TimeLimitDao
import com.kidshield.tv.data.repository.UsageRepository
import javax.inject.Inject

class CheckTimeLimitUseCase @Inject constructor(
    private val usageRepository: UsageRepository,
    private val timeLimitDao: TimeLimitDao
) {
    data class TimeLimitStatus(
        val packageName: String,
        val dailyLimitMinutes: Int?,
        val minutesUsedToday: Int,
        val minutesRemaining: Int?,
        val isExceeded: Boolean
    )

    suspend operator fun invoke(packageName: String): TimeLimitStatus {
        val timeLimit = timeLimitDao.getTimeLimitForAppOnce(packageName)
        val todayUsage = usageRepository.getTodayUsage(packageName)
        val dailyLimit = timeLimit?.dailyLimitMinutes

        return TimeLimitStatus(
            packageName = packageName,
            dailyLimitMinutes = dailyLimit,
            minutesUsedToday = todayUsage,
            minutesRemaining = dailyLimit?.let { (it - todayUsage).coerceAtLeast(0) },
            isExceeded = dailyLimit != null && todayUsage >= dailyLimit
        )
    }
}
