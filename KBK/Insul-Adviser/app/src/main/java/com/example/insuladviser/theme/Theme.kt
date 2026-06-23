package com.example.insuladviser.theme

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.graphics.Color

private val DarkColorScheme = darkColorScheme(
    primary = PrimaryTeal,
    onPrimary = TextWhite,
    secondary = AccentOrange,
    onSecondary = SlateDarkBg,
    tertiary = PrimaryTealLight,
    background = SlateDarkBg,
    surface = SlateCardBg,
    onBackground = TextWhite,
    onSurface = TextWhite,
    outline = SlateBorder
)

private val LightColorScheme = lightColorScheme(
    primary = PrimaryTeal,
    onPrimary = TextWhite,
    secondary = AccentOrange,
    onSecondary = TextWhite,
    tertiary = PrimaryTealLight,
    background = Color(0xFFF8FAFC), // Slate 50
    surface = Color.White,
    onBackground = Color(0xFF0F172A),
    onSurface = Color(0xFF0F172A),
    outline = Color(0xFFE2E8F0)
)

@Composable
fun InsulAdviserTheme(
  darkTheme: Boolean = true, // Force dark theme by default for premium feel
  dynamicColor: Boolean = false, // Disable dynamic system colors to preserve premium branding
  content: @Composable () -> Unit,
) {
  val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme

  MaterialTheme(colorScheme = colorScheme, typography = Typography, content = content)
}
