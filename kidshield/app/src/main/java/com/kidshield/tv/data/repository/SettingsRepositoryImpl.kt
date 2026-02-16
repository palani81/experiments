package com.kidshield.tv.data.repository

import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import com.kidshield.tv.domain.model.AgeProfile
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject

class SettingsRepositoryImpl @Inject constructor(
    private val dataStore: DataStore<Preferences>
) : SettingsRepository {

    companion object {
        val KEY_AGE_PROFILE = stringPreferencesKey("age_profile")
        val KEY_FIRST_LAUNCH = booleanPreferencesKey("first_launch")
    }

    override fun getAgeProfile(): Flow<AgeProfile> {
        return dataStore.data.map { prefs ->
            val name = prefs[KEY_AGE_PROFILE] ?: AgeProfile.CHILD.name
            try { AgeProfile.valueOf(name) } catch (_: Exception) { AgeProfile.CHILD }
        }
    }

    override suspend fun setAgeProfile(profile: AgeProfile) {
        dataStore.edit { prefs ->
            prefs[KEY_AGE_PROFILE] = profile.name
        }
    }

    override fun isFirstLaunch(): Flow<Boolean> {
        return dataStore.data.map { prefs ->
            prefs[KEY_FIRST_LAUNCH] ?: true
        }
    }

    override suspend fun setFirstLaunchComplete() {
        dataStore.edit { prefs ->
            prefs[KEY_FIRST_LAUNCH] = false
        }
    }
}
