package com.kidshield.tv.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.kidshield.tv.service.LockTaskHelper
import com.kidshield.tv.ui.kid.home.KidHomeScreen
import com.kidshield.tv.ui.kid.timesup.TimesUpScreen
import com.kidshield.tv.ui.parent.appmanagement.AppManagementScreen
import com.kidshield.tv.ui.parent.contentsafety.ContentSafetyScreen
import com.kidshield.tv.ui.parent.dashboard.ParentDashboardScreen
import com.kidshield.tv.ui.parent.pin.PinEntryScreen
import com.kidshield.tv.ui.parent.setupwizard.SetupWizardScreen
import com.kidshield.tv.ui.parent.timelimits.AppTimeLimitScreen
import com.kidshield.tv.ui.parent.timelimits.TimeLimitsScreen

@Composable
fun KidShieldNavGraph(
    navController: NavHostController,
    lockTaskHelper: LockTaskHelper
) {
    NavHost(navController = navController, startDestination = Screen.KidHome.route) {

        composable(Screen.KidHome.route) {
            KidHomeScreen(
                onParentAccess = {
                    navController.navigate(Screen.PinEntry.createRoute("verify"))
                },
                onTimesUp = { pkg, name ->
                    navController.navigate(Screen.TimesUp.createRoute(pkg, name))
                }
            )
        }

        composable(
            Screen.TimesUp.route,
            arguments = listOf(
                navArgument("packageName") { type = NavType.StringType },
                navArgument("appName") { type = NavType.StringType }
            )
        ) { backStackEntry ->
            TimesUpScreen(
                appName = java.net.URLDecoder.decode(
                    backStackEntry.arguments?.getString("appName") ?: "",
                    "UTF-8"
                ),
                onDismiss = {
                    navController.popBackStack(Screen.KidHome.route, inclusive = false)
                }
            )
        }

        composable(
            Screen.PinEntry.route,
            arguments = listOf(
                navArgument("mode") {
                    type = NavType.StringType
                    defaultValue = "verify"
                }
            )
        ) {
            PinEntryScreen(
                onSuccess = {
                    navController.navigate(Screen.ParentDashboard.route) {
                        popUpTo(Screen.PinEntry.route) { inclusive = true }
                    }
                },
                onCancel = { navController.popBackStack() }
            )
        }

        composable(Screen.ParentDashboard.route) {
            ParentDashboardScreen(
                lockTaskHelper = lockTaskHelper,
                onNavigateToTimeLimits = { navController.navigate(Screen.TimeLimits.route) },
                onNavigateToAppTimeLimit = { pkg, name ->
                    navController.navigate(Screen.AppTimeLimit.createRoute(pkg, name))
                },
                onNavigateToAppManagement = { navController.navigate(Screen.AppManagement.route) },
                onNavigateToContentSafety = { navController.navigate(Screen.ContentSafety.route) },
                onNavigateToSetupWizard = { navController.navigate(Screen.SetupWizard.route) },
                onBackToKids = {
                    navController.popBackStack(Screen.KidHome.route, inclusive = false)
                }
            )
        }

        composable(Screen.TimeLimits.route) {
            TimeLimitsScreen(
                onBack = { navController.popBackStack() }
            )
        }

        composable(
            Screen.AppTimeLimit.route,
            arguments = listOf(
                navArgument("packageName") { type = NavType.StringType },
                navArgument("appName") { type = NavType.StringType }
            )
        ) { backStackEntry ->
            AppTimeLimitScreen(
                packageName = java.net.URLDecoder.decode(
                    backStackEntry.arguments?.getString("packageName") ?: "",
                    "UTF-8"
                ),
                appName = java.net.URLDecoder.decode(
                    backStackEntry.arguments?.getString("appName") ?: "",
                    "UTF-8"
                ),
                onBack = { navController.popBackStack() }
            )
        }

        composable(Screen.AppManagement.route) {
            AppManagementScreen(
                onBack = { navController.popBackStack() }
            )
        }

        composable(Screen.ContentSafety.route) {
            ContentSafetyScreen(
                onBack = { navController.popBackStack() },
                onNavigateToSetupWizard = { navController.navigate(Screen.SetupWizard.route) }
            )
        }

        composable(Screen.SetupWizard.route) {
            SetupWizardScreen(
                onBack = { navController.popBackStack() }
            )
        }
    }
}
