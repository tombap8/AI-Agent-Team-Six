package com.example.insuladviser.ui.main

import android.net.Uri
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.runtime.getValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.insuladviser.data.AppSettings
import com.example.insuladviser.data.DataRepository
import com.example.insuladviser.data.LogEntry
import com.example.insuladviser.data.LibreLinkUpClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

// Item representing food chosen in the meal builder
data class MealItem(
    val name: String,
    val carbsPerUnit: Float,
    var quantity: Int
)

class MainScreenViewModel(private val repository: DataRepository) : ViewModel() {
    
    private val client = LibreLinkUpClient()

    // Bottom Navigation Active Tab (0: Advisor, 1: Diet/Nutrition, 2: History, 3: Settings)
    var currentTab by mutableStateOf(0)
    
    // App Settings State Flow
    val settingsState: StateFlow<AppSettings> = repository.settings
    
    // Inject History Logs State Flow
    val logsState: StateFlow<List<LogEntry>> = repository.logs
    
    // Libre readings state flow
    private val _libreReadings = MutableStateFlow<List<Pair<Long, Int>>>(emptyList())
    val libreReadingsState: StateFlow<List<Pair<Long, Int>>> = _libreReadings.asStateFlow()

    // Sync States
    var isSyncing by mutableStateOf(false)
    var syncErrorMessage by mutableStateOf<String?>(null)

    // Transient inputs for the Advisor (Insulin Calculator)
    var inputGlucose by mutableStateOf("")
    var inputCarbs by mutableStateOf("")
    var selectedExerciseIndex by mutableStateOf(0) // 0: None, 1: Walk 30m, 2: Walk 60m, 3: Run 30m, 4: Run 60m
    
    // Temporary selected photo path for meal "before" eating
    var tempPhotoBefore by mutableStateOf("")
    
    // Nutrition BMR/TDEE Calculator Inputs
    var bmrGender by mutableStateOf("남성")
    var bmrAge by mutableStateOf("45")
    var bmrHeight by mutableStateOf("173")
    var bmrWeight by mutableStateOf("68")
    var bmrActivity by mutableStateOf("활동 거의 없음")
    
    // Temporary food cart for the custom diet planner
    val mealItems = mutableStateListOf<MealItem>()
    
    init {
        // Load cached glucose values from CSV
        val cached = repository.readLibreGlucose()
        if (cached.isNotEmpty()) {
            _libreReadings.value = cached
        } else {
            // Generate initial mock data so the app displays a beautiful chart immediately
            generateMockLibreData()
        }
    }

    fun syncLibreData() {
        val settings = settingsState.value
        if (settings.libreEmail.isEmpty() || settings.librePassword.isEmpty()) {
            syncErrorMessage = "이메일과 비밀번호를 설정 화면에 입력해 주세요."
            return
        }

        viewModelScope.launch(Dispatchers.IO) {
            isSyncing = true
            syncErrorMessage = null
            
            val result = client.fetchRecentGlucose(
                settings.libreEmail,
                settings.librePassword,
                settings.libreRegion
            )
            
            launch(Dispatchers.Main) {
                isSyncing = false
                when (result) {
                    is LibreLinkUpClient.FetchResult.Success -> {
                        repository.saveLibreGlucose(result.readings)
                        _libreReadings.value = result.readings
                        
                        val updated = settings.copy(
                            libreConnected = true,
                            libreLastSyncTime = System.currentTimeMillis(),
                            libreAvgGlucose = result.avgGlucose,
                            libreHbA1c = result.estHbA1c
                        )
                        repository.saveSettings(updated)
                    }
                    is LibreLinkUpClient.FetchResult.Error -> {
                        syncErrorMessage = result.message
                    }
                }
            }
        }
    }

    fun generateMockLibreData() {
        val readings = mutableListOf<Pair<Long, Int>>()
        val now = System.currentTimeMillis()
        val fifteenMinutes = 15 * 60 * 1000L
        
        // Generate readings for the last 7 days (4 readings per hour * 24 * 7 = 672 points)
        val totalPoints = 4 * 24 * 7
        for (i in 0 until totalPoints) {
            val time = now - (totalPoints - i) * fifteenMinutes
            
            // Core diurnal sine wave base
            val base = 145.0
            val diurnal = 25.0 * Math.sin(2.0 * Math.PI * (i % 96) / 96.0)
            val noise = (Math.random() - 0.5) * 15.0
            
            // Simulate 3 meal spikes per day (around i % 96 = 32 (Breakfast), 52 (Lunch), 76 (Dinner))
            val dayHourIndex = i % 96
            val mealSpike = when {
                dayHourIndex in 32..44 -> {
                    // Breakfast spike
                    40.0 * Math.sin(Math.PI * (dayHourIndex - 32) / 12.0)
                }
                dayHourIndex in 52..66 -> {
                    // Lunch spike
                    55.0 * Math.sin(Math.PI * (dayHourIndex - 52) / 14.0)
                }
                dayHourIndex in 76..92 -> {
                    // Dinner spike
                    65.0 * Math.sin(Math.PI * (dayHourIndex - 76) / 16.0)
                }
                else -> 0.0
            }
            
            val glucose = (base + diurnal + noise + mealSpike).toInt().coerceIn(50, 320)
            readings.add(Pair(time, glucose))
        }
        
        repository.saveLibreGlucose(readings)
        _libreReadings.value = readings
        
        // Save default mock statistics in AppSettings as well
        val updated = settingsState.value.copy(
            libreConnected = false,
            libreHbA1c = 7.6f,
            libreAvgGlucose = 176f
        )
        repository.saveSettings(updated)
    }

    fun disconnectLibre() {
        val updated = settingsState.value.copy(
            libreEmail = "",
            librePassword = "",
            libreConnected = false,
            libreLastSyncTime = 0L
        )
        repository.saveSettings(updated)
        // Reset to mock data so the app remains interactive in Demo Mode
        generateMockLibreData()
    }

    fun addFoodToMeal(name: String, carbsPerUnit: Float) {
        val existing = mealItems.find { it.name == name }
        if (existing != null) {
            existing.quantity += 1
            // Trigger recomposition by updating the item
            val index = mealItems.indexOf(existing)
            mealItems[index] = existing.copy()
        } else {
            mealItems.add(MealItem(name, carbsPerUnit, 1))
        }
    }
    
    fun removeFoodFromMeal(name: String) {
        val existing = mealItems.find { it.name == name }
        if (existing != null) {
            if (existing.quantity > 1) {
                existing.quantity -= 1
                val index = mealItems.indexOf(existing)
                mealItems[index] = existing.copy()
            } else {
                mealItems.remove(existing)
            }
        }
    }
    
    fun clearMeal() {
        mealItems.clear()
    }
    
    fun sendMealCarbsToCalculator() {
        val totalCarbs = mealItems.sumOf { (it.carbsPerUnit * it.quantity).toDouble() }.toFloat()
        inputCarbs = totalCarbs.toInt().toString()
        currentTab = 0 // Swap screen to advisor
    }
    
    fun saveSettings(newSettings: AppSettings) {
        viewModelScope.launch {
            repository.saveSettings(newSettings)
        }
    }
    
    fun addLog(log: LogEntry) {
        viewModelScope.launch {
            repository.addLog(log)
        }
    }
    
    fun clearLogs() {
        viewModelScope.launch {
            repository.clearLogs()
        }
    }
    
    fun saveImage(uri: Uri, prefix: String): String {
        return repository.saveImage(uri, prefix)
    }
    
    fun updateLogAfterPhoto(timestamp: Long, photoPath: String) {
        viewModelScope.launch {
            repository.updateLogAfterPhoto(timestamp, photoPath)
        }
    }
}
