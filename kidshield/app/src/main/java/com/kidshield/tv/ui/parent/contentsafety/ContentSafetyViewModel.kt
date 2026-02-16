package com.kidshield.tv.ui.parent.contentsafety

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.kidshield.tv.data.repository.SettingsRepository
import com.kidshield.tv.domain.model.AgeProfile
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ContentSafetyViewModel @Inject constructor(
    private val settingsRepository: SettingsRepository
) : ViewModel() {

    data class UiState(
        val selectedAgeProfile: AgeProfile = AgeProfile.CHILD,
        val ageProfiles: List<AgeProfile> = AgeProfile.entries
    )

    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            settingsRepository.getAgeProfile().collect { profile ->
                _uiState.update { it.copy(selectedAgeProfile = profile) }
            }
        }
    }

    fun setAgeProfile(profile: AgeProfile) {
        viewModelScope.launch {
            settingsRepository.setAgeProfile(profile)
        }
    }
}
