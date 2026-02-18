package com.amazon.lat.betamanager.ui.presenter

import android.view.ViewGroup
import android.widget.ImageView
import androidx.core.content.ContextCompat
import androidx.leanback.widget.ImageCardView
import androidx.leanback.widget.Presenter
import com.amazon.lat.betamanager.R

class SettingsIconPresenter : Presenter() {

    override fun onCreateViewHolder(parent: ViewGroup): ViewHolder {
        val cardView = ImageCardView(parent.context).apply {
            isFocusable = true
            isFocusableInTouchMode = true
            setMainImageDimensions(160, 160)
            setBackgroundColor(ContextCompat.getColor(context, R.color.background_card))
            setInfoAreaBackgroundColor(ContextCompat.getColor(context, R.color.background_card))
        }
        return ViewHolder(cardView)
    }

    override fun onBindViewHolder(viewHolder: ViewHolder, item: Any) {
        val cardView = viewHolder.view as ImageCardView
        cardView.titleText = item as String
        cardView.contentText = "Notifications & Account"
        cardView.mainImageView.apply {
            setImageDrawable(ContextCompat.getDrawable(context, R.drawable.ic_settings))
            scaleType = ImageView.ScaleType.CENTER_INSIDE
            setPadding(32, 32, 32, 32)
        }

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
        cardView.mainImage = null
    }
}
