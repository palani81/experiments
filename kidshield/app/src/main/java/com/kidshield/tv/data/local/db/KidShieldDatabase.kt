package com.kidshield.tv.data.local.db

import androidx.room.Database
import androidx.room.RoomDatabase
import com.kidshield.tv.data.local.db.dao.AppConfigDao
import com.kidshield.tv.data.local.db.dao.TimeLimitDao
import com.kidshield.tv.data.local.db.dao.UsageLogDao
import com.kidshield.tv.data.model.AppConfigEntity
import com.kidshield.tv.data.model.TimeLimitEntity
import com.kidshield.tv.data.model.UsageLogEntity

@Database(
    entities = [AppConfigEntity::class, TimeLimitEntity::class, UsageLogEntity::class],
    version = 1,
    exportSchema = true
)
abstract class KidShieldDatabase : RoomDatabase() {
    abstract fun appConfigDao(): AppConfigDao
    abstract fun timeLimitDao(): TimeLimitDao
    abstract fun usageLogDao(): UsageLogDao
}
