package com.bada.biofeedback

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.bada.biofeedback.lang.PresetRepository
import com.bada.biofeedback.ui.BadaColors
import com.bada.biofeedback.ui.screens.BrainTopographyScreen
import com.bada.biofeedback.ui.screens.EcgScreen
import com.bada.biofeedback.ui.screens.EegScreen
import com.bada.biofeedback.ui.screens.HomeScreen
import com.bada.biofeedback.ui.screens.ImagingScreen
import com.bada.biofeedback.ui.screens.MedicationScreen
import com.bada.biofeedback.ui.screens.SilentTalkScreen
import com.bada.biofeedback.ui.screens.VitalsScreen

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { BadaApp() }
    }
}

@Composable
fun BadaApp() {
    val scheme = darkColorScheme(
        primary = BadaColors.Cyan,
        background = BadaColors.Bg,
        surface = BadaColors.Surface,
        onBackground = BadaColors.Text,
        onSurface = BadaColors.Text
    )
    MaterialTheme(colorScheme = scheme) {
        Surface(
            modifier = Modifier.fillMaxSize(),
            color = BadaColors.Bg
        ) {
            val nav = rememberNavController()
            NavHost(navController = nav, startDestination = "home") {
                composable("home") { HomeScreen(nav) }
                composable("brain") { BrainTopographyScreen(nav) }
                composable("imaging") { ImagingScreen(nav) }
                composable("eeg") { EegScreen(nav) }
                composable("ecg") { EcgScreen(nav) }
                composable("meds") { MedicationScreen(nav) }
                composable("silent") { SilentTalkScreen(nav) }
                composable("vitals") { VitalsScreen(nav) }
            }
        }
    }
}
