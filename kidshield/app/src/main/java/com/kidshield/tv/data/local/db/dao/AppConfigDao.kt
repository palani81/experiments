package com.kidshield.tv.data.local.db.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Query
import androidx.room.Upsert
import com.kidshield.tv.data.model.AppConfigEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface AppConfigDao {

    @Query("SELECT * FROM app_configs WHERE isAllowed = 1 ORDER BY sortOrder")
    fun getAllowedApps(): Flow<List<AppConfigEntity>>

    @Query("SELECT * FROM app_configs ORDER BY displayName")
    fun getAllApps(): Flow<List<AppConfigEntity>>

    @Query("SELECT * FROM app_configs WHERE packageName = :pkg")
    suspend fun getAppByPackage(pkg: String): AppConfigEntity?

    @Upsert
    suspend fun upsertApp(app: AppConfigEntity)

    @Upsert
    suspend fun upsertApps(apps: List<AppConfigEntity>)

    @Query("UPDATE app_configs SET isAllowed = :allowed WHERE packageName = :pkg")
    suspend fun setAllowed(pkg: String, allowed: Boolean)

    @Delete
    suspend fun deleteApp(app: AppConfigEntity)
}
