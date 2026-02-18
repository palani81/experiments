package com.amazon.lat.betamanager.ui.activity

import android.os.Bundle
import androidx.fragment.app.FragmentActivity
import com.amazon.lat.betamanager.R
import com.amazon.lat.betamanager.ui.fragment.SettingsFragment

class SettingsActivity : FragmentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)

        if (savedInstanceState == null) {
            supportFragmentManager.beginTransaction()
                .replace(R.id.settings_container, SettingsFragment())
                .commit()
        }
    }
}
