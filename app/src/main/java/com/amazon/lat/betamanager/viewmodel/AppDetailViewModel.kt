package com.amazon.lat.betamanager.viewmodel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.amazon.lat.betamanager.data.model.BetaApp
import com.amazon.lat.betamanager.data.model.DownloadState
import com.amazon.lat.betamanager.data.model.IapItem
import com.amazon.lat.betamanager.data.repository.BetaAppRepository
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.launch

class AppDetailViewModel(private val repository: BetaAppRepository) : ViewModel() {

    private val _app = MutableLiveData<BetaApp>()
    val app: LiveData<BetaApp> = _app

    private val _downloadState = MutableLiveData<DownloadState>(DownloadState.Idle)
    val downloadState: LiveData<DownloadState> = _downloadState

    private val _iapItems = MutableLiveData<List<IapItem>>()
    val iapItems: LiveData<List<IapItem>> = _iapItems

    private val _iapResetSuccess = MutableLiveData<Boolean?>()
    val iapResetSuccess: LiveData<Boolean?> = _iapResetSuccess

    private val _error = MutableLiveData<String?>()
    val error: LiveData<String?> = _error

    fun loadApp(appId: String) {
        viewModelScope.launch {
            try {
                _app.value = repository.getAppDetails(appId)
                _iapItems.value = repository.getIapItems(appId)
            } catch (e: Exception) {
                _error.value = e.message ?: "Failed to load app details"
            }
        }
    }

    fun installApp(appId: String) {
        viewModelScope.launch {
            repository.downloadApp(appId)
                .catch { e ->
                    _downloadState.value = DownloadState.Failed(e.message ?: "Download failed")
                }
                .collect { state ->
                    _downloadState.value = state
                    if (state is DownloadState.Completed) {
                        // Refresh app details after install
                        _app.value = repository.getAppDetails(appId)
                        // Reset download state so UI returns to normal
                        _downloadState.value = DownloadState.Idle
                    }
                }
        }
    }

    fun updateApp(appId: String) {
        // Same flow as install — the service handles the update
        installApp(appId)
    }

    fun uninstallApp(appId: String) {
        viewModelScope.launch {
            try {
                val success = repository.uninstallApp(appId)
                if (success) {
                    _app.value = repository.getAppDetails(appId)
                }
            } catch (e: Exception) {
                _error.value = e.message ?: "Uninstall failed"
            }
        }
    }

    fun resetIaps(appId: String) {
        viewModelScope.launch {
            _iapResetSuccess.value = null
            try {
                val success = repository.resetIaps(appId)
                _iapResetSuccess.value = success
                if (success) {
                    // Refresh IAP items after reset
                    _iapItems.value = repository.getIapItems(appId)
                }
            } catch (e: Exception) {
                _iapResetSuccess.value = false
                _error.value = e.message ?: "IAP reset failed"
            }
        }
    }

    fun clearIapResetStatus() {
        _iapResetSuccess.value = null
    }
}
