package com.kidshield.tv.ui.parent.timelimits

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.kidshield.tv.data.local.db.dao.TimeLimitDao
import com.kidshield.tv.data.model.TimeLimitEntity
import com.kidshield.tv.data.repository.AppRepository
import com.kidshield.tv.domain.model.StreamingApp
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class TimeLimitsViewModel @Inject constructor(
    private val appRepository: AppRepository,
    private val timeLimitDao: TimeLimitDao
) : ViewModel() {

    data class AppTimeLimitUi(
        val packageName: String,
        val appName: String,
        val dailyLimitMinutes: Int,
        val allowedStartTime: String?,
        val allowedEndTime: String?,
        val allowedDaysOfWeek: String
    )

    data class UiState(
        val apps: List<AppTimeLimitUi> = emptyList()
    )

    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    init {
        loadTimeLimits()
    }

    private fun loadTimeLimits() {
        viewModelScope.launch {
            combine(
                appRepository.getAllowedApps(),
                timeLimitDao.getAllTimeLimits()
            ) { apps, limits ->
                apps.map { app ->
                    val limit = limits.find { it.packageName == app.packageName }
                    AppTimeLimitUi(
                        packageName = app.packageName,
                        appName = app.displayName,
                        dailyLimitMinutes = limit?.dailyLimitMinutes ?: 60,
                        allowedStartTime = limit?.allowedStartTime,
                        allowedEndTime = limit?.allowedEndTime,
                        allowedDaysOfWeek = limit?.allowedDaysOfWeek ?: "1,2,3,4,5,6,7"
                    )
                }
            }.collect { appLimits ->
                _uiState.update { it.copy(apps = appLimits) }
            }
        }
    }

    fun updateDailyLimit(packageName: String, minutes: Int) {
        viewModelScope.launch {
            val existing = timeLimitDao.getTimeLimitForAppOnce(packageName)
            timeLimitDao.upsertTimeLimit(
                (existing ?: TimeLimitEntity(packageName = packageName)).copy(
                    dailyLimitMinutes = minutes
                )
            )
        }
    }

    fun updateSchedule(packageName: String, startTime: String?, endTime: String?) {
        viewModelScope.launch {
            val existing = timeLimitDao.getTimeLimitForAppOnce(packageName)
            timeLimitDao.upsertTimeLimit(
                (existing ?: TimeLimitEntity(packageName = packageName)).copy(
                    allowedStartTime = startTime,
                    allowedEndTime = endTime
                )
            )
        }
    }

    fun updateAllowedDays(packageName: String, days: String) {
        viewModelScope.launch {
            val existing = timeLimitDao.getTimeLimitForAppOnce(packageName)
            timeLimitDao.upsertTimeLimit(
                (existing ?: TimeLimitEntity(packageName = packageName)).copy(
                    allowedDaysOfWeek = days
                )
            )
        }
    }
}
