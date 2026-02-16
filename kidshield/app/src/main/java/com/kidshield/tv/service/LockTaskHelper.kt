package com.kidshield.tv.service

import android.app.Activity
import android.app.admin.DevicePolicyManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class LockTaskHelper @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val dpm: DevicePolicyManager =
        context.getSystemService(Context.DEVICE_POLICY_SERVICE) as DevicePolicyManager
    private val adminComponent = KidShieldDeviceAdminReceiver.getComponentName(context)

    val isDeviceOwner: Boolean
        get() = dpm.isDeviceOwnerApp(context.packageName)

    val isAdminActive: Boolean
        get() = dpm.isAdminActive(adminComponent)

    /**
     * Allowlist packages that can run in lock task mode.
     * Only works if the app is Device Owner.
     */
    fun setAllowedLockTaskPackages(packages: List<String>) {
        if (!isDeviceOwner) return
        val allPackages = (packages + context.packageName).distinct().toTypedArray()
        dpm.setLockTaskPackages(adminComponent, allPackages)
    }

    /**
     * Configure lock task features when in Device Owner mode.
     * Disables status bar, recent apps, notifications, home button.
     */
    fun configureLockTaskFeatures() {
        if (!isDeviceOwner) return
        dpm.setLockTaskFeatures(
            adminComponent,
            DevicePolicyManager.LOCK_TASK_FEATURE_NONE
        )
    }

    /**
     * Start lock task mode from the given activity.
     * In Device Owner mode this happens silently.
     * Otherwise the system shows a screen pinning confirmation.
     */
    fun startLockTask(activity: Activity) {
        try {
            activity.startLockTask()
        } catch (e: Exception) {
            // Lock task may not be available, fail gracefully
        }
    }

    fun stopLockTask(activity: Activity) {
        try {
            activity.stopLockTask()
        } catch (_: Exception) {
            // May not be in lock task mode
        }
    }

    /**
     * Suspend a package (prevent it from launching). Device Owner only.
     */
    fun suspendPackage(packageName: String) {
        if (!isDeviceOwner) return
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            dpm.setPackagesSuspended(adminComponent, arrayOf(packageName), true)
        }
    }

    fun unsuspendPackage(packageName: String) {
        if (!isDeviceOwner) return
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            dpm.setPackagesSuspended(adminComponent, arrayOf(packageName), false)
        }
    }

    fun unsuspendAll(packages: List<String>) {
        if (!isDeviceOwner) return
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            dpm.setPackagesSuspended(adminComponent, packages.toTypedArray(), false)
        }
    }

    /**
     * Check if KidShield is the default Home/Launcher app.
     * This is the non-Device-Owner way to intercept the Home button.
     */
    val isDefaultLauncher: Boolean
        get() {
            val intent = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME)
            val resolveInfo = context.packageManager.resolveActivity(
                intent, PackageManager.MATCH_DEFAULT_ONLY
            )
            return resolveInfo?.activityInfo?.packageName == context.packageName
        }
}
