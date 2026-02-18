package com.amazon.lat.betamanager.ui.fragment

import android.graphics.drawable.Drawable
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.core.content.ContextCompat
import androidx.leanback.app.DetailsSupportFragment
import androidx.leanback.widget.*
import androidx.lifecycle.ViewModelProvider
import com.amazon.lat.betamanager.R
import com.amazon.lat.betamanager.data.model.AppStatus
import com.amazon.lat.betamanager.data.model.BetaApp
import com.amazon.lat.betamanager.data.model.DownloadState
import com.amazon.lat.betamanager.di.ServiceLocator
import com.amazon.lat.betamanager.ui.presenter.AppDetailDescriptionPresenter
import com.amazon.lat.betamanager.util.Constants
import com.amazon.lat.betamanager.viewmodel.AppDetailViewModel

class AppDetailFragment : DetailsSupportFragment() {

    private lateinit var viewModel: AppDetailViewModel
    private lateinit var detailsAdapter: ArrayObjectAdapter
    private lateinit var actionsAdapter: SparseArrayObjectAdapter
    private lateinit var detailsRow: DetailsOverviewRow

    private var appId: String = ""

    companion object {
        fun newInstance(appId: String): AppDetailFragment {
            return AppDetailFragment().apply {
                arguments = Bundle().apply {
                    putString(Constants.EXTRA_APP_ID, appId)
                }
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        appId = arguments?.getString(Constants.EXTRA_APP_ID)
            ?: throw IllegalArgumentException("AppDetailFragment requires EXTRA_APP_ID")
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        viewModel = ViewModelProvider(this, ServiceLocator.viewModelFactory)
            .get(AppDetailViewModel::class.java)

        setupDetailsPresenter()
        observeViewModel()
        viewModel.loadApp(appId)
    }

    private fun setupDetailsPresenter() {
        val presenterSelector = ClassPresenterSelector()

        val detailsPresenter = FullWidthDetailsOverviewRowPresenter(AppDetailDescriptionPresenter()).apply {
            backgroundColor = ContextCompat.getColor(requireContext(), R.color.background_secondary)
            actionsBackgroundColor = ContextCompat.getColor(requireContext(), R.color.background_primary)

            setOnActionClickedListener { action ->
                handleAction(action.id)
            }
        }

        presenterSelector.addClassPresenter(DetailsOverviewRow::class.java, detailsPresenter)
        presenterSelector.addClassPresenter(ListRow::class.java, ListRowPresenter())

        detailsAdapter = ArrayObjectAdapter(presenterSelector)
        adapter = detailsAdapter
    }

    private fun bindApp(app: BetaApp) {
        // Create details row with app icon
        detailsRow = DetailsOverviewRow(app)

        // Use vector drawable icon if available (mock mode), otherwise fallback
        val iconDrawable = getAppIconDrawable(app)
        detailsRow.imageDrawable = iconDrawable

        // Set up action buttons based on app status
        actionsAdapter = SparseArrayObjectAdapter()

        when (app.status) {
            AppStatus.NOT_INSTALLED -> {
                actionsAdapter.set(
                    Constants.ACTION_INSTALL.toInt(),
                    Action(Constants.ACTION_INSTALL, getString(R.string.action_install))
                )
            }
            AppStatus.UPDATE_AVAILABLE -> {
                actionsAdapter.set(
                    Constants.ACTION_UPDATE.toInt(),
                    Action(Constants.ACTION_UPDATE, getString(R.string.action_update),
                        "${app.currentVersion} → ${app.availableVersion}")
                )
                actionsAdapter.set(
                    Constants.ACTION_OPEN.toInt(),
                    Action(Constants.ACTION_OPEN, getString(R.string.action_open))
                )
                actionsAdapter.set(
                    Constants.ACTION_UNINSTALL.toInt(),
                    Action(Constants.ACTION_UNINSTALL, getString(R.string.action_uninstall))
                )
                actionsAdapter.set(
                    Constants.ACTION_RESET_IAP.toInt(),
                    Action(Constants.ACTION_RESET_IAP, getString(R.string.action_reset_iap))
                )
            }
            AppStatus.INSTALLED -> {
                actionsAdapter.set(
                    Constants.ACTION_OPEN.toInt(),
                    Action(Constants.ACTION_OPEN, getString(R.string.action_open))
                )
                actionsAdapter.set(
                    Constants.ACTION_UNINSTALL.toInt(),
                    Action(Constants.ACTION_UNINSTALL, getString(R.string.action_uninstall))
                )
                actionsAdapter.set(
                    Constants.ACTION_RESET_IAP.toInt(),
                    Action(Constants.ACTION_RESET_IAP, getString(R.string.action_reset_iap))
                )
            }
        }

        detailsRow.actionsAdapter = actionsAdapter

        detailsAdapter.clear()
        detailsAdapter.add(detailsRow)
    }

    private fun handleAction(actionId: Long) {
        when (actionId) {
            Constants.ACTION_INSTALL -> viewModel.installApp(appId)
            Constants.ACTION_UPDATE -> viewModel.updateApp(appId)
            Constants.ACTION_UNINSTALL -> viewModel.uninstallApp(appId)
            Constants.ACTION_RESET_IAP -> viewModel.resetIaps(appId)
            Constants.ACTION_OPEN -> openApp()
        }
    }

    private fun openApp() {
        val app = viewModel.app.value ?: return
        val intent = requireContext().packageManager.getLaunchIntentForPackage(app.packageName)
        if (intent != null) {
            startActivity(intent)
        } else {
            Toast.makeText(requireContext(), "App not found on device", Toast.LENGTH_SHORT).show()
        }
    }

    private fun observeViewModel() {
        viewModel.app.observe(viewLifecycleOwner) { app ->
            bindApp(app)
        }

        viewModel.downloadState.observe(viewLifecycleOwner) { state ->
            when (state) {
                is DownloadState.Downloading -> {
                    updateActionLabel(Constants.ACTION_INSTALL, "${getString(R.string.status_downloading)} ${state.progressPercent}%")
                    updateActionLabel(Constants.ACTION_UPDATE, "${getString(R.string.status_downloading)} ${state.progressPercent}%")
                }
                is DownloadState.Installing -> {
                    updateActionLabel(Constants.ACTION_INSTALL, getString(R.string.status_installing))
                    updateActionLabel(Constants.ACTION_UPDATE, getString(R.string.status_installing))
                }
                is DownloadState.Completed -> {
                    Toast.makeText(requireContext(),
                        getString(R.string.msg_install_success, viewModel.app.value?.title ?: "App"),
                        Toast.LENGTH_SHORT).show()
                    // App details will be refreshed automatically by ViewModel
                }
                is DownloadState.Failed -> {
                    Toast.makeText(requireContext(), state.error, Toast.LENGTH_LONG).show()
                }
                is DownloadState.Idle -> { /* no-op */ }
            }
        }

        viewModel.iapResetSuccess.observe(viewLifecycleOwner) { success ->
            if (success == null) return@observe
            val appTitle = viewModel.app.value?.title ?: "App"
            if (success) {
                Toast.makeText(requireContext(),
                    getString(R.string.msg_iap_reset_success, appTitle),
                    Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(requireContext(),
                    getString(R.string.msg_error_generic),
                    Toast.LENGTH_SHORT).show()
            }
            viewModel.clearIapResetStatus()
        }
    }

    private fun updateActionLabel(actionId: Long, label: String) {
        val action = actionsAdapter.lookup(actionId.toInt()) as? Action ?: return
        action.label1 = label
        actionsAdapter.notifyArrayItemRangeChanged(0, actionsAdapter.size())
    }

    /**
     * Resolves the app icon drawable from the iconResName field (used in mock mode)
     * or falls back to the default app icon.
     *
     * TODO: When real APIs are integrated, load icon from app.iconUrl using Glide:
     *   Glide.with(requireContext()).load(app.iconUrl).into(target)
     */
    private fun getAppIconDrawable(app: BetaApp): Drawable {
        val context = requireContext()
        val iconResId = app.iconResName?.let {
            context.resources.getIdentifier(it, "drawable", context.packageName)
        } ?: 0

        return if (iconResId != 0) {
            ContextCompat.getDrawable(context, iconResId)!!
        } else {
            ContextCompat.getDrawable(context, R.drawable.default_app_icon)!!
        }
    }
}
