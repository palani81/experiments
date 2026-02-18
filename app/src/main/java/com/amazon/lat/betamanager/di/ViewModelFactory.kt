package com.amazon.lat.betamanager.di

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.amazon.lat.betamanager.data.api.AuthManager
import com.amazon.lat.betamanager.data.repository.BetaAppRepository
import com.amazon.lat.betamanager.viewmodel.AppDetailViewModel
import com.amazon.lat.betamanager.viewmodel.MainViewModel
import com.amazon.lat.betamanager.viewmodel.SettingsViewModel

class ViewModelFactory(
    private val repository: BetaAppRepository,
    private val authManager: AuthManager
) : ViewModelProvider.Factory {

    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        return when {
            modelClass.isAssignableFrom(MainViewModel::class.java) ->
                MainViewModel(repository) as T
            modelClass.isAssignableFrom(AppDetailViewModel::class.java) ->
                AppDetailViewModel(repository) as T
            modelClass.isAssignableFrom(SettingsViewModel::class.java) ->
                SettingsViewModel(repository, authManager) as T
            else -> throw IllegalArgumentException("Unknown ViewModel class: ${modelClass.name}")
        }
    }
}
