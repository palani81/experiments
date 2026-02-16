package com.kidshield.tv.ui.parent.pin

import androidx.lifecycle.ViewModel
import com.kidshield.tv.data.local.preferences.PinManager
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import javax.inject.Inject

@HiltViewModel
class PinEntryViewModel @Inject constructor(
    private val pinManager: PinManager
) : ViewModel() {

    data class UiState(
        val enteredPin: String = "",
        val maxPinLength: Int = 6,
        val isSetupMode: Boolean = false,
        val isConfirmStep: Boolean = false,
        val firstPin: String = "",
        val error: String? = null,
        val isAuthenticated: Boolean = false,
        val attemptsRemaining: Int = 5
    )

    private val _uiState = MutableStateFlow(UiState(isSetupMode = !pinManager.isPinSet))
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    fun onDigitEntered(digit: Int) {
        _uiState.update {
            if (it.enteredPin.length < it.maxPinLength)
                it.copy(enteredPin = it.enteredPin + digit, error = null)
            else it
        }
    }

    fun onBackspace() {
        _uiState.update {
            it.copy(enteredPin = it.enteredPin.dropLast(1), error = null)
        }
    }

    fun onConfirm() {
        val state = _uiState.value
        if (state.enteredPin.length < 4) {
            _uiState.update { it.copy(error = "PIN must be at least 4 digits") }
            return
        }

        if (state.attemptsRemaining <= 0) {
            _uiState.update { it.copy(error = "Too many attempts. Try again later.") }
            return
        }

        if (state.isSetupMode) {
            handleSetup(state)
        } else {
            handleVerification(state)
        }
    }

    private fun handleSetup(state: UiState) {
        if (!state.isConfirmStep) {
            _uiState.update {
                it.copy(
                    firstPin = state.enteredPin,
                    enteredPin = "",
                    isConfirmStep = true,
                    error = null
                )
            }
        } else {
            if (state.enteredPin == state.firstPin) {
                pinManager.setPin(state.enteredPin)
                _uiState.update { it.copy(isAuthenticated = true) }
            } else {
                _uiState.update {
                    it.copy(
                        enteredPin = "",
                        isConfirmStep = false,
                        firstPin = "",
                        error = "PINs don't match. Try again."
                    )
                }
            }
        }
    }

    private fun handleVerification(state: UiState) {
        if (pinManager.verifyPin(state.enteredPin)) {
            _uiState.update { it.copy(isAuthenticated = true) }
        } else {
            val remaining = state.attemptsRemaining - 1
            _uiState.update {
                it.copy(
                    enteredPin = "",
                    attemptsRemaining = remaining,
                    error = if (remaining > 0) "Wrong PIN. $remaining attempts left."
                    else "Too many attempts. Try again later."
                )
            }
        }
    }
}
