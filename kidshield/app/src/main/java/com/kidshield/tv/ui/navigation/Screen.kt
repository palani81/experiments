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
    data object TimeLimits : Screen("time_limits?fromSetup={fromSetup}") {
        fun createRoute(fromSetup: Boolean = false) = "time_limits?fromSetup=$fromSetup"
    }
    data object AppTimeLimit : Screen("app_time_limit/{packageName}/{appName}") {
        fun createRoute(pkg: String, name: String) =
            "app_time_limit/${java.net.URLEncoder.encode(pkg, "UTF-8")}/${java.net.URLEncoder.encode(name, "UTF-8")}"
    }
    data object AppManagement : Screen("app_management?fromSetup={fromSetup}") {
        fun createRoute(fromSetup: Boolean = false) = "app_management?fromSetup=$fromSetup"
    }
    data object ContentSafety : Screen("content_safety")
    data object SetupWizard : Screen("setup_wizard?step={step}") {
        fun createRoute(step: Int = 0) = "setup_wizard?step=$step"
    }
    data object Subscription : Screen("subscription")
}
