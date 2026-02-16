package com.kidshield.tv.data.repository

import com.kidshield.tv.domain.model.StreamingApp
import kotlinx.coroutines.flow.Flow

interface AppRepository {
    fun getAllowedApps(): Flow<List<StreamingApp>>
    fun getAllApps(): Flow<List<StreamingApp>>
    suspend fun setAppAllowed(packageName: String, allowed: Boolean)
    suspend fun syncInstalledApps()
    suspend fun getApp(packageName: String): StreamingApp?
}
