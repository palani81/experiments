package com.amazon.lat.betamanager.viewmodel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.amazon.lat.betamanager.data.api.AuthManager
import com.amazon.lat.betamanager.data.model.NotificationPreference
import com.amazon.lat.betamanager.data.model.UserProfile
import com.amazon.lat.betamanager.data.repository.BetaAppRepository
import kotlinx.coroutines.launch

class SettingsViewModel(
    private val repository: BetaAppRepository,
    private val authManager: AuthManager
) : ViewModel() {

    private val _userProfile = MutableLiveData<UserProfile>()
    val userProfile: LiveData<UserProfile> = _userProfile

    private val _notificationPrefs = MutableLiveData<NotificationPreference>()
    val notificationPrefs: LiveData<NotificationPreference> = _notificationPrefs

    init {
        loadSettings()
    }

    private fun loadSettings() {
        viewModelScope.launch {
            try {
                _userProfile.value = authManager.getUserProfile()
                _notificationPrefs.value = repository.getNotificationPreferences()
            } catch (e: Exception) {
                // Silently handle — settings screen will show defaults
            }
        }
    }

    fun updateNotifyOnUpdate(enabled: Boolean) {
        viewModelScope.launch {
            val current = _notificationPrefs.value ?: NotificationPreference()
            val updated = current.copy(notifyOnUpdate = enabled)
            repository.updateNotificationPreferences(updated)
            _notificationPrefs.value = updated
        }
    }

    fun updateNotifyOnInvite(enabled: Boolean) {
        viewModelScope.launch {
            val current = _notificationPrefs.value ?: NotificationPreference()
            val updated = current.copy(notifyOnNewInvite = enabled)
            repository.updateNotificationPreferences(updated)
            _notificationPrefs.value = updated
        }
    }
}
