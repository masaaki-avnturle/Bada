package com.bada.morpho

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.bada.morpho.ui.MorphoColors
import com.bada.morpho.ui.screens.CatastropheScreen
import com.bada.morpho.ui.screens.DrugManufactureScreen
import com.bada.morpho.ui.screens.HomeScreen
import com.bada.morpho.ui.screens.LineageScreen
import com.bada.morpho.ui.screens.MorphoFieldScreen

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { MorphoApp() }
    }
}

@Composable
fun MorphoApp() {
    val scheme = darkColorScheme(
        primary = MorphoColors.Green,
        background = MorphoColors.Bg,
        surface = MorphoColors.Surface,
        onBackground = MorphoColors.Text,
        onSurface = MorphoColors.Text
    )
    MaterialTheme(colorScheme = scheme) {
        Surface(modifier = Modifier.fillMaxSize(), color = MorphoColors.Bg) {
            val nav = rememberNavController()
            NavHost(navController = nav, startDestination = "home") {
                composable("home") { HomeScreen(nav) }
                composable("field") { MorphoFieldScreen(nav) }
                composable("catastrophe") { CatastropheScreen(nav) }
                composable("lineage") { LineageScreen(nav) }
                composable("drug") { DrugManufactureScreen(nav) }
            }
        }
    }
}
