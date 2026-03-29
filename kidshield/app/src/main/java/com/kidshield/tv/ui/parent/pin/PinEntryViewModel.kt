package com.kidshield.tv.ui.parent.pin

import androidx.lifecycle.SavedStateHandle
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
    private val pinManager: PinManager,
    savedStateHandle: SavedStateHandle
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

    private val mode: String = savedStateHandle.get<String>("mode") ?: "verify"
    private val _uiState = MutableStateFlow(
        UiState(isSetupMode = mode == "create" || !pinManager.isPinSet)
    )
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    init {
        // Log for debugging
        android.util.Log.d("PinEntryViewModel", "Initialized with mode=$mode, isPinSet=${pinManager.isPinSet}, isSetupMode=${_uiState.value.isSetupMode}")
    }

    fun onDigitEntered(digit: Int) {
        android.util.Log.d("PinEntryViewModel", "Digit entered: $digit, current PIN: ${_uiState.value.enteredPin}")
        _uiState.update {
            if (it.enteredPin.length < it.maxPinLength) {
                val newPin = it.enteredPin + digit
                android.util.Log.d("PinEntryViewModel", "New PIN: $newPin")
                it.copy(enteredPin = newPin, error = null)
            } else {
                android.util.Log.d("PinEntryViewModel", "PIN already at max length")
                it
            }
        }
    }

    fun onBackspace() {
        _uiState.update {
            it.copy(enteredPin = it.enteredPin.dropLast(1), error = null)
        }
    }

    fun onConfirm() {
        val state = _uiState.value
        android.util.Log.d("PinEntryViewModel", "Confirm pressed, PIN: ${state.enteredPin}, length: ${state.enteredPin.length}")
        
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
