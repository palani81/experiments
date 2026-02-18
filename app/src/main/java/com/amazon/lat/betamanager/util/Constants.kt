package com.amazon.lat.betamanager.util

object Constants {
    // Intent extras
    const val EXTRA_APP_ID = "extra_app_id"

    // Row IDs for BrowseSupportFragment
    const val ROW_UPDATES = 0L
    const val ROW_INSTALLED = 1L
    const val ROW_AVAILABLE = 2L
    const val ROW_SETTINGS = 3L

    // Detail action IDs
    const val ACTION_INSTALL = 1L
    const val ACTION_UPDATE = 2L
    const val ACTION_UNINSTALL = 3L
    const val ACTION_RESET_IAP = 4L
    const val ACTION_OPEN = 5L

    // Preference keys
    const val PREF_NOTIFY_UPDATES = "pref_notify_updates"
    const val PREF_NOTIFY_INVITES = "pref_notify_invites"
    const val PREF_ACCOUNT_NAME = "pref_account_name"
    const val PREF_APP_VERSION = "pref_app_version"
}
