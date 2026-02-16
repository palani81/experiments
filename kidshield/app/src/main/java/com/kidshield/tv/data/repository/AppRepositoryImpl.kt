package com.kidshield.tv.data.repository

import android.content.Intent
import android.content.pm.PackageManager
import com.kidshield.tv.data.KnownStreamingApps
import com.kidshield.tv.data.local.db.dao.AppConfigDao
import com.kidshield.tv.data.model.AppConfigEntity
import com.kidshield.tv.domain.model.AgeProfile
import com.kidshield.tv.domain.model.AppCategory
import com.kidshield.tv.domain.model.StreamingApp
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject

class AppRepositoryImpl @Inject constructor(
    private val appConfigDao: AppConfigDao,
    private val packageManager: PackageManager
) : AppRepository {

    override fun getAllowedApps(): Flow<List<StreamingApp>> {
        return appConfigDao.getAllowedApps().map { entities ->
            entities.map { it.toDomain() }
        }
    }

    override fun getAllApps(): Flow<List<StreamingApp>> {
        return appConfigDao.getAllApps().map { entities ->
            entities.map { it.toDomain() }
        }
    }

    override suspend fun setAppAllowed(packageName: String, allowed: Boolean) {
        appConfigDao.setAllowed(packageName, allowed)
    }

    override suspend fun syncInstalledApps() {
        val intent = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LEANBACK_LAUNCHER)
        @Suppress("DEPRECATION")
        val resolvedApps = packageManager.queryIntentActivities(intent, 0)

        val ownPackage = "com.kidshield.tv"
        val entitiesToUpsert = resolvedApps.mapNotNull { resolveInfo ->
            val pkg = resolveInfo.activityInfo.packageName
            // Skip our own app
            if (pkg == ownPackage) return@mapNotNull null

            val known = KnownStreamingApps.findByPackage(pkg)
            val existing = appConfigDao.getAppByPackage(pkg)
            val appLabel = resolveInfo.loadLabel(packageManager).toString()

            AppConfigEntity(
                packageName = pkg,
                displayName = known?.displayName ?: existing?.displayName ?: appLabel,
                isAllowed = existing?.isAllowed ?: false,
                category = known?.category?.name ?: existing?.category ?: AppCategory.OTHER.name,
                ageProfile = known?.defaultAgeProfile?.name ?: existing?.ageProfile ?: AgeProfile.ALL.name,
                sortOrder = existing?.sortOrder ?: 0,
                isKidsVariant = known?.isKidsVariant ?: existing?.isKidsVariant ?: false
            )
        }

        appConfigDao.upsertApps(entitiesToUpsert)
    }

    override suspend fun getApp(packageName: String): StreamingApp? {
        return appConfigDao.getAppByPackage(packageName)?.toDomain()
    }

    private fun AppConfigEntity.toDomain(): StreamingApp {
        val icon = try {
            packageManager.getApplicationIcon(packageName)
        } catch (_: PackageManager.NameNotFoundException) {
            null
        }
        val installed = try {
            packageManager.getPackageInfo(packageName, 0)
            true
        } catch (_: PackageManager.NameNotFoundException) {
            false
        }
        return StreamingApp(
            packageName = packageName,
            displayName = displayName,
            isInstalled = installed,
            isAllowed = isAllowed,
            category = try { AppCategory.valueOf(category) } catch (_: Exception) { AppCategory.OTHER },
            iconDrawable = icon,
            ageProfile = try { AgeProfile.valueOf(ageProfile) } catch (_: Exception) { AgeProfile.ALL },
            isKidsVariant = isKidsVariant,
            dailyMinutesRemaining = null,
            dailyLimitMinutes = null
        )
    }
}
