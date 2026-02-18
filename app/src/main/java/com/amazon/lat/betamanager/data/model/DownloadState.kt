package com.amazon.lat.betamanager.data.model

sealed class DownloadState {
    object Idle : DownloadState()
    data class Downloading(val progressPercent: Int) : DownloadState()
    object Installing : DownloadState()
    object Completed : DownloadState()
    data class Failed(val error: String) : DownloadState()
}
