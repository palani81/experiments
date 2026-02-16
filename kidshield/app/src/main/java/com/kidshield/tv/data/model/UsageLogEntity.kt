package com.kidshield.tv.data.model

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "usage_logs",
    indices = [Index(value = ["packageName", "date"])]
)
data class UsageLogEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val packageName: String,
    val date: String,
    val totalMinutesUsed: Int = 0,
    val sessionCount: Int = 0,
    val lastSessionStartEpoch: Long = 0,
    val lastSessionEndEpoch: Long? = null
)
