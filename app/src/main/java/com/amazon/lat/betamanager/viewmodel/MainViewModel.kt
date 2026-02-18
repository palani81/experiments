package com.amazon.lat.betamanager.viewmodel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.amazon.lat.betamanager.data.model.BetaApp
import com.amazon.lat.betamanager.data.repository.BetaAppRepository
import kotlinx.coroutines.launch

class MainViewModel(private val repository: BetaAppRepository) : ViewModel() {

    private val _updatesAvailable = MutableLiveData<List<BetaApp>>()
    val updatesAvailable: LiveData<List<BetaApp>> = _updatesAvailable

    private val _installedApps = MutableLiveData<List<BetaApp>>()
    val installedApps: LiveData<List<BetaApp>> = _installedApps

    private val _availableApps = MutableLiveData<List<BetaApp>>()
    val availableApps: LiveData<List<BetaApp>> = _availableApps

    private val _isLoading = MutableLiveData<Boolean>()
    val isLoading: LiveData<Boolean> = _isLoading

    private val _error = MutableLiveData<String?>()
    val error: LiveData<String?> = _error

    init {
        loadApps()
    }

    fun loadApps() {
        viewModelScope.launch {
            _isLoading.value = true
            _error.value = null
            try {
                repository.getBetaApps(forceRefresh = true)
                _updatesAvailable.value = repository.getUpdatesAvailable()
                _installedApps.value = repository.getInstalledApps()
                _availableApps.value = repository.getAvailableApps()
            } catch (e: Exception) {
                _error.value = e.message ?: "Failed to load apps"
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun refresh() {
        loadApps()
    }
}
