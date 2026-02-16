package com.kidshield.tv.data.model

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.PrimaryKey

@Entity(
    tableName = "time_limits",
    foreignKeys = [ForeignKey(
        entity = AppConfigEntity::class,
        parentColumns = ["packageName"],
        childColumns = ["packageName"],
        onDelete = ForeignKey.CASCADE
    )]
)
data class TimeLimitEntity(
    @PrimaryKey
    val packageName: String,
    val dailyLimitMinutes: Int = 60,
    val perSessionLimitMinutes: Int? = null,
    val allowedStartTime: String? = null,
    val allowedEndTime: String? = null,
    val allowedDaysOfWeek: String = "1,2,3,4,5,6,7"
)
