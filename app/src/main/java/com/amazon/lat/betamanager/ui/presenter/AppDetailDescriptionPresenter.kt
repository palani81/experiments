package com.amazon.lat.betamanager.ui.presenter

import androidx.leanback.widget.AbstractDetailsDescriptionPresenter
import com.amazon.lat.betamanager.data.model.AppStatus
import com.amazon.lat.betamanager.data.model.BetaApp
import com.amazon.lat.betamanager.util.toFormattedSize
import com.amazon.lat.betamanager.util.toRelativeTimeString

class AppDetailDescriptionPresenter : AbstractDetailsDescriptionPresenter() {

    override fun onBindDescription(viewHolder: ViewHolder, item: Any) {
        val app = item as BetaApp

        viewHolder.title.text = app.title

        val versionInfo = when (app.status) {
            AppStatus.UPDATE_AVAILABLE ->
                "${app.currentVersion} → ${app.availableVersion}"
            AppStatus.INSTALLED ->
                "v${app.currentVersion}"
            AppStatus.NOT_INSTALLED ->
                "v${app.availableVersion}"
        }
        viewHolder.subtitle.text = "${app.developer}  •  $versionInfo  •  ${app.sizeBytes.toFormattedSize()}"

        val body = buildString {
            appendLine(app.description)
            appendLine()
            appendLine("Category: ${app.category}")
            appendLine("Last updated: ${app.lastUpdated.toRelativeTimeString()}")
            if (app.changelog.isNotBlank()) {
                appendLine()
                appendLine("What's New:")
                appendLine(app.changelog)
            }
        }
        viewHolder.body.text = body
    }
}
