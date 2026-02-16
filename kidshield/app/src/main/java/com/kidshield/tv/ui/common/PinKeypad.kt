package com.kidshield.tv.ui.common

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Backspace
import androidx.compose.material.icons.filled.Check
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.tv.material3.Border
import androidx.tv.material3.ClickableSurfaceDefaults
import androidx.tv.material3.Icon
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Surface
import androidx.tv.material3.Text
import com.kidshield.tv.ui.theme.TvTextStyles

@Composable
fun PinKeypad(
    onDigit: (Int) -> Unit,
    onBackspace: () -> Unit,
    onConfirm: () -> Unit
) {
    val keys = listOf(
        listOf(1, 2, 3),
        listOf(4, 5, 6),
        listOf(7, 8, 9),
        listOf(-1, 0, -2)
    )

    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        keys.forEach { row ->
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                row.forEach { key ->
                    Surface(
                        onClick = {
                            when (key) {
                                -1 -> onBackspace()
                                -2 -> onConfirm()
                                else -> onDigit(key)
                            }
                        },
                        modifier = Modifier.size(70.dp),
                        shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(12.dp)),
                        scale = ClickableSurfaceDefaults.scale(focusedScale = 1.1f),
                        border = ClickableSurfaceDefaults.border(
                            focusedBorder = Border(
                                border = androidx.compose.foundation.BorderStroke(
                                    2.dp,
                                    MaterialTheme.colorScheme.primary
                                ),
                                shape = RoundedCornerShape(12.dp)
                            )
                        ),
                        colors = ClickableSurfaceDefaults.colors(
                            containerColor = MaterialTheme.colorScheme.surfaceVariant,
                            focusedContainerColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.2f)
                        )
                    ) {
                        Box(
                            contentAlignment = Alignment.Center,
                            modifier = Modifier.fillMaxSize()
                        ) {
                            when (key) {
                                -1 -> Icon(
                                    Icons.AutoMirrored.Filled.Backspace,
                                    contentDescription = "Delete"
                                )
                                -2 -> Icon(
                                    Icons.Default.Check,
                                    contentDescription = "Confirm",
                                    tint = MaterialTheme.colorScheme.primary
                                )
                                else -> Text(
                                    text = key.toString(),
                                    style = TvTextStyles.headlineMedium
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}
