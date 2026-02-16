package com.kidshield.tv.domain.usecase

import com.kidshield.tv.data.repository.AppRepository
import com.kidshield.tv.data.repository.SettingsRepository
import com.kidshield.tv.domain.model.AgeProfile
import com.kidshield.tv.domain.model.StreamingApp
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import javax.inject.Inject

class GetAllowedAppsUseCase @Inject constructor(
    private val appRepository: AppRepository,
    private val settingsRepository: SettingsRepository
) {
    operator fun invoke(): Flow<List<StreamingApp>> {
        return combine(
            appRepository.getAllowedApps(),
            settingsRepository.getAgeProfile()
        ) { apps, ageProfile ->
            val hasYouTubeKids = apps.any { it.packageName == "com.google.android.youtube.tvkids" }

            apps.filter { app ->
                when {
                    // If age is TODDLER or CHILD, hide regular YouTube when Kids version is available
                    app.packageName == "com.google.android.youtube.tv"
                        && hasYouTubeKids
                        && ageProfile in listOf(AgeProfile.TODDLER, AgeProfile.CHILD) -> false

                    // ALL means suitable for all ages — always show
                    app.ageProfile == AgeProfile.ALL -> true

                    // Filter by age profile: app's required age must not exceed the child's profile
                    app.ageProfile.ordinal > ageProfile.ordinal -> false

                    else -> true
                }
            }
        }
    }
}
