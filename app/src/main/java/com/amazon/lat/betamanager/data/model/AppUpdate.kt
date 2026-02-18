package com.amazon.lat.betamanager.data.model

data class AppUpdate(
    val appId: String,
    val fromVersion: String,
    val toVersion: String,
    val releaseNotes: String,
    val sizeBytes: Long,
    val releaseDate: Long
)
