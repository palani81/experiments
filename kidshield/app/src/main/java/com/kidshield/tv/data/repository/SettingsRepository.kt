package com.kidshield.tv.data.repository

import com.kidshield.tv.domain.model.AgeProfile
import kotlinx.coroutines.flow.Flow

interface SettingsRepository {
    fun getAgeProfile(): Flow<AgeProfile>
    suspend fun setAgeProfile(profile: AgeProfile)
    fun isFirstLaunch(): Flow<Boolean>
    suspend fun setFirstLaunchComplete()
}
