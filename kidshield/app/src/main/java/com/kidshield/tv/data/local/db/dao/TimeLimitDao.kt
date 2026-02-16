package com.kidshield.tv.data.local.db.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Query
import androidx.room.Upsert
import com.kidshield.tv.data.model.TimeLimitEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface TimeLimitDao {

    @Query("SELECT * FROM time_limits WHERE packageName = :pkg")
    fun getTimeLimitForApp(pkg: String): Flow<TimeLimitEntity?>

    @Query("SELECT * FROM time_limits WHERE packageName = :pkg")
    suspend fun getTimeLimitForAppOnce(pkg: String): TimeLimitEntity?

    @Query("SELECT * FROM time_limits")
    fun getAllTimeLimits(): Flow<List<TimeLimitEntity>>

    @Upsert
    suspend fun upsertTimeLimit(limit: TimeLimitEntity)

    @Delete
    suspend fun deleteTimeLimit(limit: TimeLimitEntity)
}
