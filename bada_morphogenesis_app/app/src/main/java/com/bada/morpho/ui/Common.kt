package com.bada.morpho.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

object MorphoColors {
    val Bg = Color(0xFF05080C)
    val Surface = Color(0xFF0D1219)
    val Green = Color(0xFF46C8A0)
    val Gold = Color(0xFFC8A44A)
    val Violet = Color(0xFF8E6BD0)
    val Text = Color(0xFFE6EAF0)
    val TextDim = Color(0xFF8A93A0)
    val Warn = Color(0xFFE0A24A)
    val Danger = Color(0xFFE0604A)
}

@Composable
fun DisclaimerBanner(text: String) {
    Card(
        modifier = Modifier.fillMaxWidth().padding(8.dp),
        shape = RoundedCornerShape(10.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF1A130A))
    ) {
        Text("⚠ $text", color = MorphoColors.Warn, fontSize = 12.sp, modifier = Modifier.padding(12.dp))
    }
}

@Composable
fun ScreenHeader(title: String, accent: Color, onBack: () -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(start = 6.dp, top = 14.dp, end = 12.dp, bottom = 4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        TextButton(onClick = onBack) { Text("‹ 戻る", color = MorphoColors.TextDim, fontSize = 14.sp) }
        Text(title, color = accent, fontWeight = FontWeight.Bold, fontSize = 20.sp, modifier = Modifier.padding(start = 4.dp))
    }
}

@Composable
fun SectionCard(title: String, accent: Color, content: @Composable () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth().padding(8.dp),
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(containerColor = MorphoColors.Surface)
    ) {
        Column(modifier = Modifier.fillMaxWidth().padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(title, color = accent, fontWeight = FontWeight.Bold, fontSize = 16.sp)
            content()
        }
    }
}
