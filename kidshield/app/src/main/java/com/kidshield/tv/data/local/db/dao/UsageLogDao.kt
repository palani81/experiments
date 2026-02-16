package com.kidshield.tv.data.local.db.dao

import androidx.room.Dao
import androidx.room.Query
import androidx.room.Upsert
import com.kidshield.tv.data.model.UsageLogEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface UsageLogDao {

    @Query("SELECT * FROM usage_logs WHERE packageName = :pkg AND date = :date")
    suspend fun getUsageForDate(pkg: String, date: String): UsageLogEntity?

    @Query("SELECT * FROM usage_logs WHERE date = :date")
    fun getAllUsageForDate(date: String): Flow<List<UsageLogEntity>>

    @Query("SELECT * FROM usage_logs WHERE packageName = :pkg ORDER BY date DESC LIMIT :days")
    fun getRecentUsage(pkg: String, days: Int = 7): Flow<List<UsageLogEntity>>

    @Upsert
    suspend fun upsertUsageLog(log: UsageLogEntity)

    @Query("DELETE FROM usage_logs WHERE date < :beforeDate")
    suspend fun deleteOldLogs(beforeDate: String)
}
