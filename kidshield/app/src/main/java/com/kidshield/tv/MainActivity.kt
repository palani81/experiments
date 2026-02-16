package com.kidshield.tv

import android.content.Intent
import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.core.content.ContextCompat
import androidx.navigation.compose.rememberNavController
import com.kidshield.tv.data.local.preferences.PinManager
import com.kidshield.tv.data.repository.SettingsRepository
import com.kidshield.tv.service.AppMonitorService
import com.kidshield.tv.service.LockTaskHelper
import com.kidshield.tv.ui.navigation.KidShieldNavGraph
import com.kidshield.tv.ui.theme.KidShieldTheme
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    @Inject
    lateinit var lockTaskHelper: LockTaskHelper

    @Inject
    lateinit var settingsRepository: SettingsRepository

    @Inject
    lateinit var pinManager: PinManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Start monitoring service
        try {
            val serviceIntent = Intent(this, AppMonitorService::class.java)
            ContextCompat.startForegroundService(this, serviceIntent)
        } catch (e: Exception) {
            Log.w("KidShield", "Could not start monitor service", e)
        }

        // Configure lock task mode if we are Device Owner (strongest protection)
        if (lockTaskHelper.isDeviceOwner) {
            Log.d("KidShield", "Device Owner active — configuring lock task mode")
            lockTaskHelper.setAllowedLockTaskPackages(getAllowedPackages())
            lockTaskHelper.configureLockTaskFeatures()
        } else {
            // Without Device Owner, we rely on being the default launcher.
            // The HOME intent filter in manifest + user selecting KidShield
            // as "Always" for Home means pressing Home returns here.
            Log.d("KidShield", "No Device Owner — using launcher mode. " +
                "Default launcher: ${lockTaskHelper.isDefaultLauncher}")
        }

        setContent {
            KidShieldTheme {
                val navController = rememberNavController()
                KidShieldNavGraph(
                    navController = navController,
                    lockTaskHelper = lockTaskHelper,
                    settingsRepository = settingsRepository,
                    pinManager = pinManager
                )
            }
        }
    }

    override fun onResume() {
        super.onResume()
        // If Device Owner, engage lock task (blocks Home/Recent/Status bar)
        if (lockTaskHelper.isDeviceOwner) {
            lockTaskHelper.startLockTask(this)
        }
        // If not Device Owner but we are default launcher, Home button
        // already brings user back here — no extra action needed
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        // Called when Home button is pressed and we are the default launcher.
        // The app is already in front — nothing to do.
    }

    @Deprecated("Use OnBackPressedDispatcher", ReplaceWith(""))
    override fun onBackPressed() {
        // Prevent back button from exiting the app
        // Do nothing - kids can't exit
    }

    /**
     * Packages allowed to run while in lock task mode (Device Owner only).
     * Dynamically discovers all installed leanback apps so the allowlist
     * stays in sync with what's actually on the device.
     */
    private fun getAllowedPackages(): List<String> {
        val intent = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LEANBACK_LAUNCHER)
        @Suppress("DEPRECATION")
        val installed = packageManager.queryIntentActivities(intent, 0)
            .map { it.activityInfo.packageName }

        return (installed + listOf(
            packageName,
            "com.android.vending",       // Google Play Store
            "com.amazon.venezia"          // Amazon Appstore (Fire TV)
        )).distinct()
    }
}
