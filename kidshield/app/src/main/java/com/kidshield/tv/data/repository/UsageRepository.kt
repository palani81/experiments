package com.kidshield.tv.data.repository

import com.kidshield.tv.data.model.UsageLogEntity
import kotlinx.coroutines.flow.Flow

interface UsageRepository {
    suspend fun recordUsage(packageName: String, minutes: Int)
    suspend fun getTodayUsage(packageName: String): Int
    fun getTodayAllUsage(): Flow<List<UsageLogEntity>>
    fun getWeeklyUsage(packageName: String): Flow<List<UsageLogEntity>>
    suspend fun cleanOldRecords(retentionDays: Int = 30)
}
