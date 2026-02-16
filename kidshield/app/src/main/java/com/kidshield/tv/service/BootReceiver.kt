package com.kidshield.tv.service

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import androidx.core.content.ContextCompat
import com.kidshield.tv.MainActivity

class BootReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED) {
            // Launch main activity to re-enter kiosk mode
            val launchIntent = Intent(context, MainActivity::class.java).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            context.startActivity(launchIntent)

            // Start the monitoring service
            val serviceIntent = Intent(context, AppMonitorService::class.java)
            ContextCompat.startForegroundService(context, serviceIntent)
        }
    }
}
