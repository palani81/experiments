package com.amazon.lat.betamanager.ui.fragment

import android.content.Intent
import android.os.Bundle
import android.view.View
import androidx.core.content.ContextCompat
import androidx.leanback.app.BrowseSupportFragment
import androidx.leanback.widget.*
import androidx.lifecycle.ViewModelProvider
import com.amazon.lat.betamanager.R
import com.amazon.lat.betamanager.data.model.BetaApp
import com.amazon.lat.betamanager.di.ServiceLocator
import com.amazon.lat.betamanager.ui.activity.DetailActivity
import com.amazon.lat.betamanager.ui.activity.SettingsActivity
import com.amazon.lat.betamanager.ui.presenter.AppCardPresenter
import com.amazon.lat.betamanager.ui.presenter.SettingsIconPresenter
import com.amazon.lat.betamanager.util.Constants
import com.amazon.lat.betamanager.viewmodel.MainViewModel

class MainFragment : BrowseSupportFragment() {

    private lateinit var viewModel: MainViewModel
    private lateinit var rowsAdapter: ArrayObjectAdapter

    private val updatesAdapter = ArrayObjectAdapter(AppCardPresenter())
    private val installedAdapter = ArrayObjectAdapter(AppCardPresenter())
    private val availableAdapter = ArrayObjectAdapter(AppCardPresenter())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setupUI()
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        viewModel = ViewModelProvider(this, ServiceLocator.viewModelFactory)
            .get(MainViewModel::class.java)

        setupRows()
        setupListeners()
        observeViewModel()
    }

    private fun setupUI() {
        title = getString(R.string.app_title)
        headersState = HEADERS_ENABLED
        isHeadersTransitionOnBackEnabled = true

        // Fire TV dark theme colors
        brandColor = ContextCompat.getColor(requireContext(), R.color.fastlane_background)

        // Disable the search orb — not needed for this app
        searchAffordanceColor = 0
    }

    override fun onStart() {
        super.onStart()
        // Hide the search orb view to prevent overlap with header text
        view?.findViewById<View>(androidx.leanback.R.id.title_orb)?.visibility = View.GONE
    }

    private fun setupRows() {
        rowsAdapter = ArrayObjectAdapter(ListRowPresenter())

        // Row 1: Updates Available — apps with a newer beta version ready
        val updatesHeader = HeaderItem(Constants.ROW_UPDATES, getString(R.string.row_updates_available))
        rowsAdapter.add(ListRow(updatesHeader, updatesAdapter))

        // Row 2: Installed Beta Apps — apps installed and up-to-date (no pending update)
        val installedHeader = HeaderItem(Constants.ROW_INSTALLED, getString(R.string.row_installed_apps))
        rowsAdapter.add(ListRow(installedHeader, installedAdapter))

        // Row 3: Available to Test — invited but not yet installed on device
        val availableHeader = HeaderItem(Constants.ROW_AVAILABLE, getString(R.string.row_available_apps))
        rowsAdapter.add(ListRow(availableHeader, availableAdapter))

        // Row 4: Settings
        val settingsHeader = HeaderItem(Constants.ROW_SETTINGS, getString(R.string.settings_title))
        val settingsAdapter = ArrayObjectAdapter(SettingsIconPresenter())
        settingsAdapter.add(getString(R.string.settings_title))
        rowsAdapter.add(ListRow(settingsHeader, settingsAdapter))

        adapter = rowsAdapter
    }

    private fun setupListeners() {
        onItemViewClickedListener = OnItemViewClickedListener { _, item, _, _ ->
            when (item) {
                is BetaApp -> {
                    val intent = Intent(requireContext(), DetailActivity::class.java).apply {
                        putExtra(Constants.EXTRA_APP_ID, item.id)
                    }
                    startActivity(intent)
                }
                is String -> {
                    // Settings row click
                    startActivity(Intent(requireContext(), SettingsActivity::class.java))
                }
            }
        }
    }

    private fun observeViewModel() {
        viewModel.updatesAvailable.observe(viewLifecycleOwner) { apps ->
            updatesAdapter.clear()
            updatesAdapter.addAll(0, apps)
        }

        viewModel.installedApps.observe(viewLifecycleOwner) { apps ->
            installedAdapter.clear()
            installedAdapter.addAll(0, apps)
        }

        viewModel.availableApps.observe(viewLifecycleOwner) { apps ->
            availableAdapter.clear()
            availableAdapter.addAll(0, apps)
        }
    }

    override fun onResume() {
        super.onResume()
        viewModel.refresh()
    }
}
