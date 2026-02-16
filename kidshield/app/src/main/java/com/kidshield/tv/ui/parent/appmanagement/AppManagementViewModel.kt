package com.kidshield.tv.ui.parent.appmanagement

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.kidshield.tv.data.repository.AppRepository
import com.kidshield.tv.domain.model.StreamingApp
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class AppManagementViewModel @Inject constructor(
    private val appRepository: AppRepository
) : ViewModel() {

    data class UiState(
        val apps: List<StreamingApp> = emptyList(),
        val isLoading: Boolean = true
    )

    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    init {
        loadApps()
    }

    private fun loadApps() {
        viewModelScope.launch {
            appRepository.syncInstalledApps()
            appRepository.getAllApps().collect { apps ->
                _uiState.update { it.copy(apps = apps, isLoading = false) }
            }
        }
    }

    fun toggleAppAllowed(packageName: String, allowed: Boolean) {
        viewModelScope.launch {
            appRepository.setAppAllowed(packageName, allowed)
        }
    }
}
