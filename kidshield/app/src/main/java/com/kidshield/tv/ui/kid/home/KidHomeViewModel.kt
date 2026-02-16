package com.kidshield.tv.ui.kid.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.kidshield.tv.data.repository.AppRepository
import com.kidshield.tv.data.repository.UsageRepository
import com.kidshield.tv.domain.model.AppCategory
import com.kidshield.tv.domain.model.StreamingApp
import com.kidshield.tv.domain.usecase.CheckTimeLimitUseCase
import com.kidshield.tv.domain.usecase.GetAllowedAppsUseCase
import com.kidshield.tv.domain.usecase.LaunchAppUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.time.LocalTime
import javax.inject.Inject

@HiltViewModel
class KidHomeViewModel @Inject constructor(
    private val getAllowedAppsUseCase: GetAllowedAppsUseCase,
    private val launchAppUseCase: LaunchAppUseCase,
    private val checkTimeLimitUseCase: CheckTimeLimitUseCase,
    private val usageRepository: UsageRepository,
    private val appRepository: AppRepository
) : ViewModel() {

    data class UiState(
        val greeting: String = "",
        val categories: Map<String, List<StreamingApp>> = emptyMap(),
        val launchError: String? = null,
        val timesUpApp: Pair<String, String>? = null,
        val isLoading: Boolean = true
    )

    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    init {
        updateGreeting()
        viewModelScope.launch {
            appRepository.syncInstalledApps()
        }
        loadApps()
    }

    private fun loadApps() {
        viewModelScope.launch {
            getAllowedAppsUseCase().collect { apps ->
                // Enrich with time limit data
                val enrichedApps = apps.map { app ->
                    val status = checkTimeLimitUseCase(app.packageName)
                    app.copy(
                        dailyMinutesRemaining = status.minutesRemaining,
                        dailyLimitMinutes = status.dailyLimitMinutes
                    )
                }

                val grouped = enrichedApps.groupBy { app ->
                    when (app.category) {
                        AppCategory.STREAMING -> "Streaming"
                        AppCategory.EDUCATION -> "Education"
                        AppCategory.GAME -> "Games"
                        AppCategory.OTHER -> "Other"
                    }
                }

                _uiState.update {
                    it.copy(categories = grouped, isLoading = false)
                }
            }
        }
    }

    fun launchApp(packageName: String) {
        viewModelScope.launch {
            _uiState.update { it.copy(launchError = null) }
            when (val result = launchAppUseCase(packageName)) {
                is LaunchAppUseCase.LaunchResult.Success -> { /* app launched */ }
                is LaunchAppUseCase.LaunchResult.TimeLimitReached ->
                    _uiState.update { it.copy(timesUpApp = packageName to result.appName) }
                is LaunchAppUseCase.LaunchResult.OutsideSchedule ->
                    _uiState.update {
                        it.copy(launchError = "Available ${result.allowedStart} - ${result.allowedEnd}")
                    }
                is LaunchAppUseCase.LaunchResult.NotAllowed ->
                    _uiState.update { it.copy(launchError = result.reason) }
                is LaunchAppUseCase.LaunchResult.AppNotInstalled ->
                    _uiState.update { it.copy(launchError = "App not installed") }
            }
        }
    }

    fun clearTimesUp() {
        _uiState.update { it.copy(timesUpApp = null) }
    }

    fun clearError() {
        _uiState.update { it.copy(launchError = null) }
    }

    private fun updateGreeting() {
        val hour = LocalTime.now().hour
        val greeting = when {
            hour < 12 -> "Good morning!"
            hour < 17 -> "Good afternoon!"
            else -> "Good evening!"
        }
        _uiState.update { it.copy(greeting = greeting) }
    }
}
