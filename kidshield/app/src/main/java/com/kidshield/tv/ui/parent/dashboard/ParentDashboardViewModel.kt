package com.kidshield.tv.ui.parent.dashboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.kidshield.tv.data.local.db.dao.TimeLimitDao
import com.kidshield.tv.data.repository.AppRepository
import com.kidshield.tv.data.repository.UsageRepository
import com.kidshield.tv.domain.model.UsageRecord
import com.kidshield.tv.service.LockTaskHelper
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ParentDashboardViewModel @Inject constructor(
    private val appRepository: AppRepository,
    private val usageRepository: UsageRepository,
    private val timeLimitDao: TimeLimitDao,
    private val lockTaskHelper: LockTaskHelper
) : ViewModel() {

    data class UiState(
        val totalMinutesToday: Int = 0,
        val appUsages: List<UsageRecord> = emptyList(),
        val isDeviceOwner: Boolean = false,
        val isAdminActive: Boolean = false
    )

    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    init {
        loadDashboard()
    }

    private fun loadDashboard() {
        viewModelScope.launch {
            combine(
                appRepository.getAllowedApps(),
                usageRepository.getTodayAllUsage(),
                timeLimitDao.getAllTimeLimits()
            ) { apps, usages, limits ->
                val records = apps.map { app ->
                    val usage = usages.find { it.packageName == app.packageName }
                    val limit = limits.find { it.packageName == app.packageName }
                    UsageRecord(
                        packageName = app.packageName,
                        appName = app.displayName,
                        date = java.time.LocalDate.now().toString(),
                        minutesUsed = usage?.totalMinutesUsed ?: 0,
                        limitMinutes = limit?.dailyLimitMinutes
                    )
                }.sortedByDescending { it.minutesUsed }

                UiState(
                    totalMinutesToday = records.sumOf { it.minutesUsed },
                    appUsages = records,
                    isDeviceOwner = lockTaskHelper.isDeviceOwner,
                    isAdminActive = lockTaskHelper.isAdminActive
                )
            }.collect { state ->
                _uiState.value = state
            }
        }
    }
}
