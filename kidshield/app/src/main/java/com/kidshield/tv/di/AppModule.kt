package com.kidshield.tv.di

import android.content.Context
import android.content.SharedPreferences
import android.content.pm.PackageManager
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.preferencesDataStore
import androidx.room.Room
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import com.kidshield.tv.data.local.db.KidShieldDatabase
import com.kidshield.tv.data.local.db.dao.AppConfigDao
import com.kidshield.tv.data.local.db.dao.TimeLimitDao
import com.kidshield.tv.data.local.db.dao.UsageLogDao
import com.kidshield.tv.data.local.preferences.PinManager
import com.kidshield.tv.data.repository.AppRepository
import com.kidshield.tv.data.repository.AppRepositoryImpl
import com.kidshield.tv.data.repository.SettingsRepository
import com.kidshield.tv.data.repository.SettingsRepositoryImpl
import com.kidshield.tv.data.repository.UsageRepository
import com.kidshield.tv.data.repository.UsageRepositoryImpl
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "kidshield_settings")

@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext ctx: Context): KidShieldDatabase =
        Room.databaseBuilder(ctx, KidShieldDatabase::class.java, "kidshield.db")
            .fallbackToDestructiveMigration()
            .build()

    @Provides
    fun provideAppConfigDao(db: KidShieldDatabase): AppConfigDao = db.appConfigDao()

    @Provides
    fun provideTimeLimitDao(db: KidShieldDatabase): TimeLimitDao = db.timeLimitDao()

    @Provides
    fun provideUsageLogDao(db: KidShieldDatabase): UsageLogDao = db.usageLogDao()

    @Provides
    @Singleton
    fun provideEncryptedPrefs(@ApplicationContext ctx: Context): SharedPreferences {
        val masterKey = MasterKey.Builder(ctx)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        return EncryptedSharedPreferences.create(
            ctx,
            "kidshield_secure_prefs",
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }

    @Provides
    @Singleton
    fun providePinManager(prefs: SharedPreferences): PinManager = PinManager(prefs)

    @Provides
    @Singleton
    fun providePackageManager(@ApplicationContext ctx: Context): PackageManager =
        ctx.packageManager

    @Provides
    @Singleton
    fun provideAppRepository(
        appConfigDao: AppConfigDao,
        packageManager: PackageManager
    ): AppRepository = AppRepositoryImpl(appConfigDao, packageManager)

    @Provides
    @Singleton
    fun provideUsageRepository(usageLogDao: UsageLogDao): UsageRepository =
        UsageRepositoryImpl(usageLogDao)

    @Provides
    @Singleton
    fun provideDataStore(@ApplicationContext ctx: Context): DataStore<Preferences> =
        ctx.dataStore

    @Provides
    @Singleton
    fun provideSettingsRepository(dataStore: DataStore<Preferences>): SettingsRepository =
        SettingsRepositoryImpl(dataStore)
}
