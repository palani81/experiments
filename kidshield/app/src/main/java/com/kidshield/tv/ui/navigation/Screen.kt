package com.kidshield.tv.ui.navigation

sealed class Screen(val route: String) {
    data object KidHome : Screen("kid_home")

    data object TimesUp : Screen("times_up/{packageName}/{appName}") {
        fun createRoute(pkg: String, name: String) =
            "times_up/${java.net.URLEncoder.encode(pkg, "UTF-8")}/${java.net.URLEncoder.encode(name, "UTF-8")}"
    }

    data object PinEntry : Screen("pin_entry?mode={mode}") {
        fun createRoute(mode: String = "verify") = "pin_entry?mode=$mode"
    }

    data object ParentDashboard : Screen("parent_dashboard")
    data object TimeLimits : Screen("time_limits")
    data object AppTimeLimit : Screen("app_time_limit/{packageName}/{appName}") {
        fun createRoute(pkg: String, name: String) =
            "app_time_limit/${java.net.URLEncoder.encode(pkg, "UTF-8")}/${java.net.URLEncoder.encode(name, "UTF-8")}"
    }
    data object AppManagement : Screen("app_management")
    data object ContentSafety : Screen("content_safety")
    data object SetupWizard : Screen("setup_wizard")
}
