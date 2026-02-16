package com.kidshield.tv.data.repository

import com.kidshield.tv.data.local.db.dao.UsageLogDao
import com.kidshield.tv.data.model.UsageLogEntity
import kotlinx.coroutines.flow.Flow
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import javax.inject.Inject

class UsageRepositoryImpl @Inject constructor(
    private val usageLogDao: UsageLogDao
) : UsageRepository {

    private val dateFormatter = DateTimeFormatter.ISO_LOCAL_DATE

    private fun today(): String = LocalDate.now().format(dateFormatter)

    override suspend fun recordUsage(packageName: String, minutes: Int) {
        val date = today()
        val existing = usageLogDao.getUsageForDate(packageName, date)
        if (existing != null) {
            usageLogDao.upsertUsageLog(
                existing.copy(
                    totalMinutesUsed = existing.totalMinutesUsed + minutes,
                    lastSessionEndEpoch = System.currentTimeMillis()
                )
            )
        } else {
            usageLogDao.upsertUsageLog(
                UsageLogEntity(
                    packageName = packageName,
                    date = date,
                    totalMinutesUsed = minutes,
                    sessionCount = 1,
                    lastSessionStartEpoch = System.currentTimeMillis()
                )
            )
        }
    }

    override suspend fun getTodayUsage(packageName: String): Int {
        return usageLogDao.getUsageForDate(packageName, today())?.totalMinutesUsed ?: 0
    }

    override fun getTodayAllUsage(): Flow<List<UsageLogEntity>> {
        return usageLogDao.getAllUsageForDate(today())
    }

    override fun getWeeklyUsage(packageName: String): Flow<List<UsageLogEntity>> {
        return usageLogDao.getRecentUsage(packageName, 7)
    }

    override suspend fun cleanOldRecords(retentionDays: Int) {
        val cutoff = LocalDate.now().minusDays(retentionDays.toLong()).format(dateFormatter)
        usageLogDao.deleteOldLogs(cutoff)
    }
}
