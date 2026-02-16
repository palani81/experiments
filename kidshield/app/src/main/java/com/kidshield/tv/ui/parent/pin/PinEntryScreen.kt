package com.kidshield.tv.ui.parent.pin

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Lock
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.tv.material3.Icon
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Text
import com.kidshield.tv.ui.common.PinKeypad
import com.kidshield.tv.ui.theme.KidShieldBlue
import com.kidshield.tv.ui.theme.TvTextStyles

@Composable
fun PinEntryScreen(
    viewModel: PinEntryViewModel = hiltViewModel(),
    onSuccess: () -> Unit,
    onCancel: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    LaunchedEffect(uiState.isAuthenticated) {
        if (uiState.isAuthenticated) onSuccess()
    }

    Column(
        modifier = Modifier.fillMaxSize().padding(horizontal = 48.dp, vertical = 16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            Icons.Default.Lock,
            contentDescription = null,
            modifier = Modifier.size(40.dp),
            tint = KidShieldBlue
        )

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = when {
                uiState.isSetupMode && uiState.isConfirmStep -> "Confirm your PIN"
                uiState.isSetupMode -> "Create a Parent PIN"
                else -> "Enter Parent PIN"
            },
            style = TvTextStyles.headlineMedium
        )

        Spacer(modifier = Modifier.height(12.dp))

        // PIN dots
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            repeat(uiState.maxPinLength) { index ->
                Box(
                    modifier = Modifier
                        .size(16.dp)
                        .clip(CircleShape)
                        .background(
                            when {
                                uiState.error != null && index < uiState.enteredPin.length ->
                                    MaterialTheme.colorScheme.error
                                index < uiState.enteredPin.length ->
                                    MaterialTheme.colorScheme.primary
                                else ->
                                    MaterialTheme.colorScheme.surfaceVariant
                            }
                        )
                )
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        if (uiState.error != null) {
            Text(
                text = uiState.error!!,
                style = TvTextStyles.bodyLarge,
                color = MaterialTheme.colorScheme.error
            )
            Spacer(modifier = Modifier.height(8.dp))
        }

        PinKeypad(
            onDigit = { viewModel.onDigitEntered(it) },
            onBackspace = { viewModel.onBackspace() },
            onConfirm = { viewModel.onConfirm() }
        )
    }
}
