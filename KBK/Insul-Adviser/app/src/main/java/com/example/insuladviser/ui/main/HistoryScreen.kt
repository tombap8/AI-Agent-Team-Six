package com.example.insuladviser.ui.main

import android.graphics.BitmapFactory
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.insuladviser.data.AppSettings
import com.example.insuladviser.data.LogEntry
import com.example.insuladviser.theme.*
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlin.math.roundToInt

@Composable
fun HistoryScreen(
    viewModel: MainScreenViewModel,
    modifier: Modifier = Modifier
) {
    val logs by viewModel.logsState.collectAsState()
    val settings by viewModel.settingsState.collectAsState()
    var showDeleteConfirm by remember { mutableStateOf(false) }

    // Formatter for timestamp
    val dateFormatter = remember { SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.getDefault()) }

    // Stats calculations
    val totalEntries = logs.size
    val avgGlucose = if (totalEntries > 0) logs.map { it.currentGlucose }.average().toInt() else 0
    val totalInsulin = if (totalEntries > 0) logs.sumOf { it.finalDose.toDouble() }.toFloat() else 0f
    val totalCarbs = if (totalEntries > 0) logs.sumOf { it.carbs.toDouble() }.toFloat() else 0f

    // Track which item is expanded to show post-meal ICR tuning details
    var expandedTimestamp by remember { mutableStateOf<Long?>(null) }

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(bottom = 16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Timeline Header with Averages
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = SlateCardBg),
            shape = RoundedCornerShape(20.dp)
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "투약 기록 통계 요약",
                        color = TextWhite,
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Bold
                    )
                    if (logs.isNotEmpty()) {
                        Text(
                            text = "기록 비우기",
                            color = GlucoseHigh,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.clickable { showDeleteConfirm = true }
                        )
                    }
                }

                HorizontalDivider(color = SlateBorder)

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    // Average BG
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(text = "기록 평균 혈당", color = TextGray, fontSize = 11.sp)
                        Text(
                            text = if (totalEntries > 0) "$avgGlucose mg/dL" else "--",
                            color = if (totalEntries > 0 && avgGlucose > 180) GlucoseHigh else if (totalEntries > 0 && avgGlucose < 70) GlucoseLow else TextWhite,
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                    // Divider
                    Box(modifier = Modifier.width(1.dp).height(30.dp).background(SlateBorder))
                    // Total Insulin
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(text = "총 인슐린 투여", color = TextGray, fontSize = 11.sp)
                        Text(
                            text = if (totalEntries > 0) "${String.format(Locale.US, "%.1f", totalInsulin)} U" else "--",
                            color = AccentOrange,
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                    // Divider
                    Box(modifier = Modifier.width(1.dp).height(30.dp).background(SlateBorder))
                    // Total Carbs
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(text = "총 탄수화물 섭취", color = TextGray, fontSize = 11.sp)
                        Text(
                            text = if (totalEntries > 0) "${totalCarbs.toInt()} g" else "--",
                            color = PrimaryTealLight,
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        }

        // Timeline log items
        if (logs.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                contentAlignment = Alignment.Center
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Info,
                        contentDescription = null,
                        tint = TextMuted,
                        modifier = Modifier.size(36.dp)
                    )
                    Text(
                        text = "저장된 투약 로그가 없습니다.\n인슐린 계산기에서 투약을 기록해 보세요.",
                        color = TextGray,
                        fontSize = 13.sp,
                        textAlign = TextAlign.Center,
                        lineHeight = 18.sp
                    )
                }
            }
        } else {
            LazyColumn(
                verticalArrangement = Arrangement.spacedBy(10.dp),
                modifier = Modifier.weight(1f)
            ) {
                items(logs) { log ->
                    LogItemCard(
                        log = log, 
                        dateFormatter = dateFormatter,
                        isExpanded = expandedTimestamp == log.timestamp,
                        onExpandClick = {
                            expandedTimestamp = if (expandedTimestamp == log.timestamp) null else log.timestamp
                        },
                        settings = settings,
                        viewModel = viewModel
                    )
                }
            }
        }
    }

    // Delete Confirmation Dialog
    if (showDeleteConfirm) {
        AlertDialog(
            onDismissRequest = { showDeleteConfirm = false },
            title = { Text("투약 기록 초기화", color = TextWhite) },
            text = { Text("정말로 저장된 모든 투약 로그를 영구 삭제하시겠습니까?\n삭제된 데이터는 복구할 수 없습니다.", color = TextGray) },
            confirmButton = {
                TextButton(
                    onClick = {
                        viewModel.clearLogs()
                        showDeleteConfirm = false
                    }
                ) {
                    Text("예, 삭제합니다", color = GlucoseHigh, fontWeight = FontWeight.Bold)
                }
            },
            dismissButton = {
                TextButton(onClick = { showDeleteConfirm = false }) {
                    Text("취소", color = TextWhite)
                }
            },
            containerColor = SlateCardBg,
            shape = RoundedCornerShape(16.dp)
        )
    }
}

@Composable
fun LogItemCard(
    log: LogEntry, 
    dateFormatter: SimpleDateFormat,
    isExpanded: Boolean,
    onExpandClick: () -> Unit,
    settings: AppSettings,
    viewModel: MainScreenViewModel
) {
    val context = LocalContext.current
    val dateStr = remember(log.timestamp) { dateFormatter.format(Date(log.timestamp)) }

    // launcher to select after-meal photo
    val afterPhotoPickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.PickVisualMedia(),
        onResult = { uri ->
            if (uri != null) {
                val localPath = viewModel.saveImage(uri, "after")
                viewModel.updateLogAfterPhoto(log.timestamp, localPath)
                Toast.makeText(context, "식후 사진이 등록되었습니다.", Toast.LENGTH_SHORT).show()
            }
        }
    )

    // Color code based on glucose level
    val bgIndicatorColor = when {
        log.currentGlucose < 70 -> GlucoseLow
        log.currentGlucose <= 140 -> GlucoseStable
        log.currentGlucose <= 180 -> GlucoseWarning
        else -> GlucoseHigh
    }

    val glucoseTagText = when {
        log.currentGlucose < 70 -> "저혈당"
        log.currentGlucose <= 140 -> "안정"
        log.currentGlucose <= 180 -> "높음"
        else -> "고혈당"
    }

    Card(
        colors = CardDefaults.cardColors(containerColor = SlateCardBg.copy(alpha = 0.6f)),
        shape = RoundedCornerShape(16.dp),
        modifier = Modifier
            .fillMaxWidth()
            .border(0.5.dp, SlateBorder, RoundedCornerShape(16.dp))
            .clickable { onExpandClick() }
    ) {
        Column(
            modifier = Modifier.padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Timestamp and Glucose level
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(text = dateStr, color = TextMuted, fontSize = 12.sp)

                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(4.dp))
                            .background(bgIndicatorColor.copy(alpha = 0.15f))
                            .padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Text(
                            text = glucoseTagText,
                            color = bgIndicatorColor,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }

                    Text(
                        text = "${log.currentGlucose} mg/dL",
                        color = TextWhite,
                        fontWeight = FontWeight.Bold,
                        fontSize = 14.sp
                    )
                }
            }

            HorizontalDivider(color = SlateBorder.copy(alpha = 0.5f))

            // Pre-meal / Post-meal food photo slot row
            if (log.photoBefore.isNotEmpty() || log.photoAfter.isNotEmpty()) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 4.dp),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    // Before photo thumbnail
                    if (log.photoBefore.isNotEmpty()) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(text = "식사 전", color = TextMuted, fontSize = 9.sp, modifier = Modifier.padding(bottom = 2.dp))
                            val bitmap = remember(log.photoBefore) {
                                try { BitmapFactory.decodeFile(log.photoBefore)?.asImageBitmap() } catch (e: Exception) { null }
                            }
                            if (bitmap != null) {
                                Image(
                                    bitmap = bitmap,
                                    contentDescription = "식전 사진",
                                    modifier = Modifier
                                        .size(64.dp)
                                        .clip(RoundedCornerShape(8.dp))
                                        .border(0.5.dp, SlateBorder, RoundedCornerShape(8.dp)),
                                    contentScale = ContentScale.Crop
                                )
                            }
                        }
                    }
                    
                    // After photo thumbnail or selector
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(text = "식사 후", color = TextMuted, fontSize = 9.sp, modifier = Modifier.padding(bottom = 2.dp))
                        if (log.photoAfter.isNotEmpty()) {
                            val bitmap = remember(log.photoAfter) {
                                try { BitmapFactory.decodeFile(log.photoAfter)?.asImageBitmap() } catch (e: Exception) { null }
                            }
                            if (bitmap != null) {
                                Image(
                                    bitmap = bitmap,
                                    contentDescription = "식후 사진",
                                    modifier = Modifier
                                        .size(64.dp)
                                        .clip(RoundedCornerShape(8.dp))
                                        .border(0.5.dp, SlateBorder, RoundedCornerShape(8.dp)),
                                    contentScale = ContentScale.Crop
                                )
                            }
                        } else {
                            Box(
                                modifier = Modifier
                                    .size(64.dp)
                                    .clip(RoundedCornerShape(8.dp))
                                    .background(SlateDarkBg)
                                    .border(0.5.dp, SlateBorder, RoundedCornerShape(8.dp))
                                    .clickable {
                                        afterPhotoPickerLauncher.launch(
                                            PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)
                                        )
                                    },
                                contentAlignment = Alignment.Center
                            ) {
                                Text("+ 식후", color = PrimaryTealLight, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }
            } else {
                // If neither photo is uploaded, allow upload of after photo easily
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "등록된 사진이 없습니다.",
                        color = TextMuted,
                        fontSize = 11.sp
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "+ 식후 사진 추가",
                        color = PrimaryTealLight,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.clickable {
                            afterPhotoPickerLauncher.launch(
                                PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)
                            )
                        }
                    )
                }
            }

            // Dose parameters summary
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        Text(text = "식사 탄수화물: ${log.carbs.toInt()}g", color = TextGray, fontSize = 12.sp)
                        if (log.exerciseDuration > 0) {
                            Text(text = "식후 운동: ${log.exerciseName}", color = PrimaryTealLight, fontSize = 12.sp)
                        }
                    }
                    Text(
                        text = "식사: ${String.format(Locale.US, "%.1f", log.foodDose)}U | 교정: ${String.format(Locale.US, "%.1f", log.correctionDose)}U" +
                                if (log.exerciseReduction > 0f) " | 운동감소: -${String.format(Locale.US, "%.1f", log.exerciseReduction)}U" else "",
                        color = TextMuted,
                        fontSize = 11.sp
                    )
                }

                // Final dose bubble
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(8.dp))
                        .background(AccentOrange.copy(alpha = 0.15f))
                        .border(0.5.dp, AccentOrange, RoundedCornerShape(8.dp))
                        .padding(horizontal = 8.dp, vertical = 4.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "${String.format(Locale.US, "%.1f", log.finalDose)} U",
                        color = AccentOrange,
                        fontWeight = FontWeight.Bold,
                        fontSize = 14.sp
                    )
                }
            }

            // Expanded Section: Post-meal 2h glucose & ICR tuning feedback
            if (isExpanded) {
                var postMealBgStr by remember(log.timestamp) { mutableStateOf("") }
                val postBg = postMealBgStr.toIntOrNull()

                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 10.dp)
                        .clip(RoundedCornerShape(12.dp))
                        .background(SlateDarkBg)
                        .padding(12.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text(
                        text = "식후 피드백 및 탄수화물 계수(ICR) 튜너",
                        color = TextWhite,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Bold
                    )

                    OutlinedTextField(
                        value = postMealBgStr,
                        onValueChange = { postMealBgStr = it },
                        label = { Text("식후 2시간 실제 혈당 (mg/dL)") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        shape = RoundedCornerShape(8.dp),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedTextColor = TextWhite,
                            unfocusedTextColor = TextWhite,
                            focusedBorderColor = PrimaryTeal,
                            unfocusedBorderColor = SlateBorder
                        ),
                        modifier = Modifier.fillMaxWidth()
                    )

                    if (postBg != null) {
                        // Math logic for new suggested ICR based on target post-meal BG
                        val targetPostBg = 180f // Standard post-meal target ceiling
                        val isf = settings.isf

                        if (postBg > 200) {
                            // Underdosed! (Blood glucose is higher than the 180-200 mg/dL target)
                            val excessBg = postBg - targetPostBg
                            val shortageInsulin = excessBg / isf
                            val idealMealDose = log.foodDose + shortageInsulin
                            // E.g. New ICR = Carbs / idealMealDose (decrease ICR to make insulin stronger)
                            val suggestedIcr = if (idealMealDose > 0.1f) log.carbs / idealMealDose else settings.icr
                            val roundedSuggestedIcr = (suggestedIcr * 10f).roundToInt() / 10f

                            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                Text(
                                    text = "⚠️ 인슐린 투여량이 부족했습니다.",
                                    color = GlucoseHigh,
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.Bold
                                )
                                Text(
                                    text = "식후 혈당이 목표 수치보다 높아 인슐린이 부족했음을 의미합니다. 탄수화물 계수(ICR) 강도를 더 높일 것을 추천합니다.",
                                    color = TextGray,
                                    fontSize = 11.sp,
                                    lineHeight = 15.sp
                                )
                                Spacer(modifier = Modifier.height(4.dp))
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text(
                                        text = "권장 ICR: ${settings.icr} -> ${roundedSuggestedIcr} g/U",
                                        color = TextWhite,
                                        fontSize = 12.sp,
                                        fontWeight = FontWeight.Bold
                                    )
                                    Button(
                                        onClick = {
                                            val newSettings = settings.copy(icr = roundedSuggestedIcr)
                                            viewModel.saveSettings(newSettings)
                                            Toast.makeText(context, "새로운 탄수화물 계수(${roundedSuggestedIcr})가 저장되었습니다.", Toast.LENGTH_SHORT).show()
                                        },
                                        colors = ButtonDefaults.buttonColors(containerColor = PrimaryTeal),
                                        contentPadding = PaddingValues(horizontal = 10.dp, vertical = 2.dp),
                                        shape = RoundedCornerShape(6.dp),
                                        modifier = Modifier.height(30.dp)
                                    ) {
                                        Text("설정 적용", fontSize = 10.sp, fontWeight = FontWeight.Bold)
                                    }
                                }
                            }
                        } else if (postBg < 70) {
                            // Overdosed! (Hypoglycemia alert)
                            val deficitBg = targetPostBg - postBg
                            val excessInsulin = deficitBg / isf
                            val idealMealDose = (log.foodDose - excessInsulin).coerceAtLeast(0.5f)
                            val suggestedIcr = log.carbs / idealMealDose
                            val roundedSuggestedIcr = (suggestedIcr * 10f).roundToInt() / 10f

                            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                Text(
                                    text = "🚨 인슐린이 과다 투여되었습니다 (저혈당 위험).",
                                    color = GlucoseLow,
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.Bold
                                )
                                Text(
                                    text = "식후 혈당이 과도하게 하강하였습니다. 탄수화물 계수(ICR)를 증가시켜 인슐린 투여 강도를 완화할 것을 권장합니다.",
                                    color = TextGray,
                                    fontSize = 11.sp,
                                    lineHeight = 15.sp
                                )
                                Spacer(modifier = Modifier.height(4.dp))
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text(
                                        text = "권장 ICR: ${settings.icr} -> ${roundedSuggestedIcr} g/U",
                                        color = TextWhite,
                                        fontSize = 12.sp,
                                        fontWeight = FontWeight.Bold
                                    )
                                    Button(
                                        onClick = {
                                            val newSettings = settings.copy(icr = roundedSuggestedIcr)
                                            viewModel.saveSettings(newSettings)
                                            Toast.makeText(context, "새로운 탄수화물 계수(${roundedSuggestedIcr})가 저장되었습니다.", Toast.LENGTH_SHORT).show()
                                        },
                                        colors = ButtonDefaults.buttonColors(containerColor = PrimaryTeal),
                                        contentPadding = PaddingValues(horizontal = 10.dp, vertical = 2.dp),
                                        shape = RoundedCornerShape(6.dp),
                                        modifier = Modifier.height(30.dp)
                                    ) {
                                        Text("설정 적용", fontSize = 10.sp, fontWeight = FontWeight.Bold)
                                    }
                                }
                            }
                        } else {
                            // Good glycemic control (in target)
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                Text(
                                    text = "🟢 이상적인 혈당 제어 성공!",
                                    color = GlucoseStable,
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.Bold
                                )
                                Text(
                                    text = "탄수화물 계수(${settings.icr})가 적절합니다.",
                                    color = TextGray,
                                    fontSize = 12.sp
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}
