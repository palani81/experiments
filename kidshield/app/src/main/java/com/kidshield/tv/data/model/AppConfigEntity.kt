package com.kidshield.tv.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "app_configs")
data class AppConfigEntity(
    @PrimaryKey
    val packageName: String,
    val displayName: String,
    val isAllowed: Boolean = false,
    val category: String = "STREAMING",
    val ageProfile: String = "ALL",
    val sortOrder: Int = 0,
    val isKidsVariant: Boolean = false,
    val adultPackageName: String? = null
)
