package com.example.insuladviser.ui.main

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.List
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation3.runtime.NavKey
import com.example.insuladviser.data.DefaultDataRepository
import com.example.insuladviser.theme.SlateBorder
import com.example.insuladviser.theme.SlateCardBg

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(
    onItemClick: (NavKey) -> Unit,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current.applicationContext
    val viewModel: MainScreenViewModel = viewModel {
        MainScreenViewModel(DefaultDataRepository(context))
    }
    Scaffold(
        modifier = modifier,
        bottomBar = {
            NavigationBar(
                containerColor = SlateCardBg,
                tonalElevation = 8.dp
            ) {
                NavigationBarItem(
                    selected = viewModel.currentTab == 0,
                    onClick = { viewModel.currentTab = 0 },
                    icon = { Icon(imageVector = Icons.Default.Home, contentDescription = "어드바이저") },
                    label = { Text("어드바이저", fontSize = 11.sp) },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = MaterialTheme.colorScheme.primary,
                        unselectedIconColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                        selectedTextColor = MaterialTheme.colorScheme.primary,
                        unselectedTextColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                        indicatorColor = SlateBorder
                    )
                )
                NavigationBarItem(
                    selected = viewModel.currentTab == 1,
                    onClick = { viewModel.currentTab = 1 },
                    icon = { Icon(imageVector = Icons.Default.Search, contentDescription = "식단사전") },
                    label = { Text("식단사전", fontSize = 11.sp) },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = MaterialTheme.colorScheme.primary,
                        unselectedIconColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                        selectedTextColor = MaterialTheme.colorScheme.primary,
                        unselectedTextColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                        indicatorColor = SlateBorder
                    )
                )
                NavigationBarItem(
                    selected = viewModel.currentTab == 2,
                    onClick = { viewModel.currentTab = 2 },
                    icon = { Icon(imageVector = Icons.Default.List, contentDescription = "기록") },
                    label = { Text("투약기록", fontSize = 11.sp) },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = MaterialTheme.colorScheme.primary,
                        unselectedIconColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                        selectedTextColor = MaterialTheme.colorScheme.primary,
                        unselectedTextColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                        indicatorColor = SlateBorder
                    )
                )
                NavigationBarItem(
                    selected = viewModel.currentTab == 3,
                    onClick = { viewModel.currentTab = 3 },
                    icon = { Icon(imageVector = Icons.Default.Settings, contentDescription = "설정") },
                    label = { Text("설정", fontSize = 11.sp) },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = MaterialTheme.colorScheme.primary,
                        unselectedIconColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                        selectedTextColor = MaterialTheme.colorScheme.primary,
                        unselectedTextColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                        indicatorColor = SlateBorder
                    )
                )
            }
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .safeDrawingPadding()
                .padding(horizontal = 16.dp, vertical = 8.dp)
        ) {
            when (viewModel.currentTab) {
                0 -> AdvisorScreen(viewModel = viewModel)
                1 -> NutritionScreen(viewModel = viewModel)
                2 -> HistoryScreen(viewModel = viewModel)
                3 -> SettingsScreen(viewModel = viewModel)
            }
        }
    }
}
