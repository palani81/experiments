package com.kidshield.tv.service

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.kidshield.tv.data.repository.AppRepository
import com.kidshield.tv.data.repository.UsageRepository
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import kotlinx.coroutines.flow.first

@HiltWorker
class TimeEnforcementWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val usageRepository: UsageRepository,
    private val appRepository: AppRepository,
    private val lockTaskHelper: LockTaskHelper
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        // Clean up old usage logs (retain 30 days)
        usageRepository.cleanOldRecords(retentionDays = 30)

        // Unsuspend all allowed apps at the start of a new day
        val allowedApps = appRepository.getAllowedApps().first()
        lockTaskHelper.unsuspendAll(allowedApps.map { it.packageName })

        return Result.success()
    }
}
