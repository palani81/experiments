package com.amazon.lat.betamanager.ui.presenter

import android.view.ViewGroup
import android.widget.ImageView
import androidx.core.content.ContextCompat
import androidx.leanback.widget.ImageCardView
import androidx.leanback.widget.Presenter
import com.amazon.lat.betamanager.R
import com.amazon.lat.betamanager.data.model.AppStatus
import com.amazon.lat.betamanager.data.model.BetaApp

class AppCardPresenter : Presenter() {

    override fun onCreateViewHolder(parent: ViewGroup): ViewHolder {
        val cardView = ImageCardView(parent.context).apply {
            isFocusable = true
            isFocusableInTouchMode = true

            val cardWidth = parent.context.resources.getDimensionPixelSize(R.dimen.card_width)
            setMainImageDimensions(cardWidth, parent.context.resources.getDimensionPixelSize(R.dimen.card_image_height))

            // Fire TV dark theme card styling
            setBackgroundColor(ContextCompat.getColor(context, R.color.background_card))
            setInfoAreaBackgroundColor(ContextCompat.getColor(context, R.color.background_card))
        }

        return ViewHolder(cardView)
    }

    override fun onBindViewHolder(viewHolder: ViewHolder, item: Any) {
        val app = item as BetaApp
        val cardView = viewHolder.view as ImageCardView

        // Always show title and developer below the icon
        cardView.titleText = app.title
        cardView.contentText = app.developer

        // Use vector drawable icon if available (mock mode), otherwise fallback
        val context = cardView.context
        val iconResId = app.iconResName?.let {
            context.resources.getIdentifier(it, "drawable", context.packageName)
        } ?: 0

        if (iconResId != 0) {
            cardView.mainImageView.apply {
                setImageDrawable(ContextCompat.getDrawable(context, iconResId))
                scaleType = ImageView.ScaleType.CENTER_CROP
            }
        } else {
            cardView.mainImageView.apply {
                setImageDrawable(ContextCompat.getDrawable(context, R.drawable.default_app_icon))
                scaleType = ImageView.ScaleType.CENTER_CROP
            }
        }

        // Update badge for status
        cardView.badgeImage = when (app.status) {
            AppStatus.UPDATE_AVAILABLE ->
                ContextCompat.getDrawable(cardView.context, R.drawable.ic_update_badge)
            else -> null
        }

        // Focus highlight
        cardView.setOnFocusChangeListener { v, hasFocus ->
            val bgColor = if (hasFocus) {
                ContextCompat.getColor(v.context, R.color.background_card_focused)
            } else {
                ContextCompat.getColor(v.context, R.color.background_card)
            }
            (v as ImageCardView).setInfoAreaBackgroundColor(bgColor)
            v.setBackgroundColor(bgColor)
        }
    }

    override fun onUnbindViewHolder(viewHolder: ViewHolder) {
        val cardView = viewHolder.view as ImageCardView
        cardView.badgeImage = null
        cardView.mainImage = null
    }
}
