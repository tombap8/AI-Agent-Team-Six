package com.example.insuladviser.data

import android.content.Context
import android.net.Uri
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.io.File
import java.io.FileOutputStream
import java.io.IOException

// Settings data class for user targets and coefficients
data class AppSettings(
    val targetGlucose: Int = 120,
    val icr: Float = 10f,
    val isf: Float = 50f,
    val roundingMode: String = "0.5", // "NONE", "0.5", "1.0"
    val walking30Reduction: Float = 0.15f,
    val walking60Reduction: Float = 0.25f,
    val running30Reduction: Float = 0.35f,
    val running60Reduction: Float = 0.50f,
    
    // LibreLinkUp settings
    val libreEmail: String = "",
    val librePassword: String = "",
    val libreRegion: String = "ap", // "ap", "us", "eu", "de", "fr", "jp", "ae"
    val libreConnected: Boolean = false,
    val libreLastSyncTime: Long = 0L,
    val libreHbA1c: Float = 7.6f,       // base target or computed
    val libreAvgGlucose: Float = 176f   // base target or computed
)

// Log entry for an individual insulin dose record, now with food pictures
data class LogEntry(
    val timestamp: Long,
    val currentGlucose: Int,
    val carbs: Float,
    val exerciseName: String,
    val exerciseDuration: Int,
    val foodDose: Float,
    val correctionDose: Float,
    val exerciseReduction: Float,
    val finalDose: Float,
    val photoBefore: String = "", // Path to meal photo before eating
    val photoAfter: String = ""   // Path to meal photo after eating (empty plate)
) {
    fun toCsvLine(): String = "$timestamp,$currentGlucose,$carbs,$exerciseName,$exerciseDuration,$foodDose,$correctionDose,$exerciseReduction,$finalDose,$photoBefore,$photoAfter"

    companion object {
        fun fromCsvLine(line: String): LogEntry? {
            val parts = line.split(",")
            if (parts.size < 9) return null
            return try {
                LogEntry(
                    timestamp = parts[0].toLong(),
                    currentGlucose = parts[1].toInt(),
                    carbs = parts[2].toFloat(),
                    exerciseName = parts[3],
                    exerciseDuration = parts[4].toInt(),
                    foodDose = parts[5].toFloat(),
                    correctionDose = parts[6].toFloat(),
                    exerciseReduction = parts[7].toFloat(),
                    finalDose = parts[8].toFloat(),
                    photoBefore = if (parts.size > 9) parts[9] else "",
                    photoAfter = if (parts.size > 10) parts[10] else ""
                )
            } catch (e: Exception) {
                null
            }
        }
    }
}

interface DataRepository {
    val settings: StateFlow<AppSettings>
    val logs: StateFlow<List<LogEntry>>
    
    fun saveSettings(newSettings: AppSettings)
    fun addLog(log: LogEntry)
    fun clearLogs()
    fun saveImage(uri: Uri, prefix: String): String
    fun updateLogAfterPhoto(timestamp: Long, photoPath: String)
    fun saveLibreGlucose(readings: List<Pair<Long, Int>>)
    fun readLibreGlucose(): List<Pair<Long, Int>>
}

class DefaultDataRepository(private val context: Context) : DataRepository {
    private val prefs = context.getSharedPreferences("insul_adviser_prefs", Context.MODE_PRIVATE)
    private val logFile = File(context.filesDir, "logs.csv")
    private val libreFile = File(context.filesDir, "libre_glucose.csv")
    
    private val _settings = MutableStateFlow(readSettingsFromPrefs())
    override val settings: StateFlow<AppSettings> = _settings.asStateFlow()
    
    private val _logs = MutableStateFlow(readLogsFromFile())
    override val logs: StateFlow<List<LogEntry>> = _logs.asStateFlow()

    private fun readSettingsFromPrefs(): AppSettings {
        return AppSettings(
            targetGlucose = prefs.getInt("targetGlucose", 120),
            icr = prefs.getFloat("icr", 10f),
            isf = prefs.getFloat("isf", 50f),
            roundingMode = prefs.getString("roundingMode", "0.5") ?: "0.5",
            walking30Reduction = prefs.getFloat("walking30Reduction", 0.15f),
            walking60Reduction = prefs.getFloat("walking60Reduction", 0.25f),
            running30Reduction = prefs.getFloat("running30Reduction", 0.35f),
            running60Reduction = prefs.getFloat("running60Reduction", 0.50f),
            libreEmail = prefs.getString("libreEmail", "") ?: "",
            librePassword = prefs.getString("librePassword", "") ?: "",
            libreRegion = prefs.getString("libreRegion", "ap") ?: "ap",
            libreConnected = prefs.getBoolean("libreConnected", false),
            libreLastSyncTime = prefs.getLong("libreLastSyncTime", 0L),
            libreHbA1c = prefs.getFloat("libreHbA1c", 7.6f),
            libreAvgGlucose = prefs.getFloat("libreAvgGlucose", 176f)
        )
    }

    private fun readLogsFromFileRaw(): List<LogEntry> {
        if (!logFile.exists()) return emptyList()
        return try {
            logFile.readLines().mapNotNull { LogEntry.fromCsvLine(it) }
        } catch (e: IOException) {
            emptyList()
        }
    }

    private fun readLogsFromFile(): List<LogEntry> {
        return readLogsFromFileRaw().reversed() // Show newest first
    }

    override fun saveSettings(newSettings: AppSettings) {
        prefs.edit().apply {
            putInt("targetGlucose", newSettings.targetGlucose)
            putFloat("icr", newSettings.icr)
            putFloat("isf", newSettings.isf)
            putString("roundingMode", newSettings.roundingMode)
            putFloat("walking30Reduction", newSettings.walking30Reduction)
            putFloat("walking60Reduction", newSettings.walking60Reduction)
            putFloat("running30Reduction", newSettings.running30Reduction)
            putFloat("running60Reduction", newSettings.running60Reduction)
            putString("libreEmail", newSettings.libreEmail)
            putString("librePassword", newSettings.librePassword)
            putString("libreRegion", newSettings.libreRegion)
            putBoolean("libreConnected", newSettings.libreConnected)
            putLong("libreLastSyncTime", newSettings.libreLastSyncTime)
            putFloat("libreHbA1c", newSettings.libreHbA1c)
            putFloat("libreAvgGlucose", newSettings.libreAvgGlucose)
            apply()
        }
        _settings.value = newSettings
    }

    override fun addLog(log: LogEntry) {
        try {
            logFile.appendText(log.toCsvLine() + "\n")
            _logs.value = readLogsFromFile()
        } catch (e: IOException) {
            // Error writing log
        }
    }

    override fun clearLogs() {
        if (logFile.exists()) {
            logFile.delete()
        }
        _logs.value = emptyList()
    }

    override fun saveImage(uri: Uri, prefix: String): String {
        val fileExtension = ".jpg"
        val fileName = "${prefix}_${System.currentTimeMillis()}$fileExtension"
        val photosDir = File(context.filesDir, "photos")
        if (!photosDir.exists()) {
            photosDir.mkdirs()
        }
        val destinationFile = File(photosDir, fileName)
        return try {
            context.contentResolver.openInputStream(uri)?.use { inputStream ->
                FileOutputStream(destinationFile).use { outputStream ->
                    inputStream.copyTo(outputStream)
                }
            }
            destinationFile.absolutePath
        } catch (e: Exception) {
            ""
        }
    }

    override fun updateLogAfterPhoto(timestamp: Long, photoPath: String) {
        val currentLogs = readLogsFromFileRaw()
        val updatedLogs = currentLogs.map { log ->
            if (log.timestamp == timestamp) {
                log.copy(photoAfter = photoPath)
            } else {
                log
            }
        }
        try {
            logFile.writeText("") // Clear file
            updatedLogs.forEach { log ->
                logFile.appendText(log.toCsvLine() + "\n")
            }
            _logs.value = readLogsFromFile() // Reload Flow
        } catch (e: IOException) {
            // Error updating log
        }
    }

    override fun saveLibreGlucose(readings: List<Pair<Long, Int>>) {
        try {
            val content = readings.joinToString("\n") { "${it.first},${it.second}" }
            libreFile.writeText(content + "\n")
        } catch (e: IOException) {
            // Error saving glucose readings
        }
    }

    override fun readLibreGlucose(): List<Pair<Long, Int>> {
        if (!libreFile.exists()) return emptyList()
        return try {
            libreFile.readLines().mapNotNull { line ->
                val parts = line.split(",")
                if (parts.size == 2) {
                    try {
                        Pair(parts[0].toLong(), parts[1].toInt())
                    } catch (e: Exception) {
                        null
                    }
                } else {
                    null
                }
            }
        } catch (e: IOException) {
            emptyList()
        }
    }
}
