package com.amazon.lat.betamanager.data.model

data class NotificationPreference(
    val notifyOnUpdate: Boolean = true,
    val notifyOnNewInvite: Boolean = true
)
