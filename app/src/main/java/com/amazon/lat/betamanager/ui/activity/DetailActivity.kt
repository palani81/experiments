package com.amazon.lat.betamanager.ui.activity

import android.os.Bundle
import androidx.fragment.app.FragmentActivity
import com.amazon.lat.betamanager.R
import com.amazon.lat.betamanager.ui.fragment.AppDetailFragment
import com.amazon.lat.betamanager.util.Constants

class DetailActivity : FragmentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_detail)

        if (savedInstanceState == null) {
            val appId = intent.getStringExtra(Constants.EXTRA_APP_ID)
                ?: throw IllegalArgumentException("DetailActivity requires EXTRA_APP_ID")

            supportFragmentManager.beginTransaction()
                .replace(R.id.detail_container, AppDetailFragment.newInstance(appId))
                .commit()
        }
    }
}
