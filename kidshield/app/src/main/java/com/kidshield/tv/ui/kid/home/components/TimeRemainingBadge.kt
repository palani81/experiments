package com.kidshield.tv.ui.kid.home.components

import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.tv.material3.ClickableSurfaceDefaults
import androidx.tv.material3.Surface
import androidx.tv.material3.Text
import com.kidshield.tv.ui.theme.TvTextStyles

@Composable
fun TimeRemainingBadge(minutesRemaining: Int, color: Color) {
    Surface(
        shape = ClickableSurfaceDefaults.shape(shape = RoundedCornerShape(8.dp)),
        colors = ClickableSurfaceDefaults.colors(
            containerColor = color.copy(alpha = 0.2f)
        ),
        modifier = Modifier.padding(top = 4.dp),
        onClick = {}
    ) {
        Text(
            text = when {
                minutesRemaining >= 60 -> "${minutesRemaining / 60}h ${minutesRemaining % 60}m"
                else -> "${minutesRemaining}m left"
            },
            style = TvTextStyles.labelSmall,
            color = color,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp)
        )
    }
}
