package com.kidshield.tv.service

import android.app.admin.DeviceAdminReceiver
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.util.Log

class KidShieldDeviceAdminReceiver : DeviceAdminReceiver() {

    companion object {
        private const val TAG = "KidShieldAdmin"

        fun getComponentName(context: Context): ComponentName =
            ComponentName(context, KidShieldDeviceAdminReceiver::class.java)
    }

    override fun onEnabled(context: Context, intent: Intent) {
        super.onEnabled(context, intent)
        Log.d(TAG, "Device admin enabled")
    }

    override fun onDisabled(context: Context, intent: Intent) {
        super.onDisabled(context, intent)
        Log.d(TAG, "Device admin disabled")
    }

    override fun onLockTaskModeEntering(context: Context, intent: Intent, pkg: String) {
        Log.d(TAG, "Lock task mode entering for $pkg")
    }

    override fun onLockTaskModeExiting(context: Context, intent: Intent) {
        Log.d(TAG, "Lock task mode exiting")
    }
}
