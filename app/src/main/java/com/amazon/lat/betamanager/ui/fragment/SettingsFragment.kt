package com.amazon.lat.betamanager.ui.fragment

import android.os.Bundle
import androidx.leanback.preference.LeanbackPreferenceFragmentCompat
import androidx.lifecycle.ViewModelProvider
import androidx.preference.Preference
import androidx.preference.SwitchPreference
import com.amazon.lat.betamanager.BuildConfig
import com.amazon.lat.betamanager.R
import com.amazon.lat.betamanager.di.ServiceLocator
import com.amazon.lat.betamanager.util.Constants
import com.amazon.lat.betamanager.viewmodel.SettingsViewModel

class SettingsFragment : LeanbackPreferenceFragmentCompat() {

    private lateinit var viewModel: SettingsViewModel

    override fun onCreatePreferences(savedInstanceState: Bundle?, rootKey: String?) {
        setPreferencesFromResource(R.xml.preferences, rootKey)

        viewModel = ViewModelProvider(this, ServiceLocator.viewModelFactory)
            .get(SettingsViewModel::class.java)

        setupPreferenceListeners()
        observeViewModel()
    }

    private fun setupPreferenceListeners() {
        findPreference<SwitchPreference>(Constants.PREF_NOTIFY_UPDATES)?.setOnPreferenceChangeListener { _, newValue ->
            viewModel.updateNotifyOnUpdate(newValue as Boolean)
            true
        }

        findPreference<SwitchPreference>(Constants.PREF_NOTIFY_INVITES)?.setOnPreferenceChangeListener { _, newValue ->
            viewModel.updateNotifyOnInvite(newValue as Boolean)
            true
        }
    }

    private fun observeViewModel() {
        viewModel.userProfile.observe(this) { profile ->
            findPreference<Preference>(Constants.PREF_ACCOUNT_NAME)?.summary = profile.name
        }

        viewModel.notificationPrefs.observe(this) { prefs ->
            findPreference<SwitchPreference>(Constants.PREF_NOTIFY_UPDATES)?.isChecked = prefs.notifyOnUpdate
            findPreference<SwitchPreference>(Constants.PREF_NOTIFY_INVITES)?.isChecked = prefs.notifyOnNewInvite
        }

        // Set app version
        findPreference<Preference>(Constants.PREF_APP_VERSION)?.summary = BuildConfig.VERSION_NAME
    }
}
