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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.insuladviser.data.LogEntry
import com.example.insuladviser.theme.*
import java.util.Locale
import kotlin.math.roundToInt
import androidx.compose.foundation.Canvas
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.geometry.Offset

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AdvisorScreen(
    viewModel: MainScreenViewModel,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val settings by viewModel.settingsState.collectAsState()
    val readings by viewModel.libreReadingsState.collectAsState()
    val scrollState = rememberScrollState()

    // Activity launcher for selecting pre-meal photo
    val photoPickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.PickVisualMedia(),
        onResult = { uri ->
            if (uri != null) {
                val localPath = viewModel.saveImage(uri, "before")
                viewModel.tempPhotoBefore = localPath
            }
        }
    )

    // Exercise options mapped directly to current settings percentages
    val exerciseOptions = listOf(
        "운동 계획 없음 (0% 감량)" to 0.00f,
        "식후 30분 걷기 (${(settings.walking30Reduction * 100).toInt()}% 감량)" to settings.walking30Reduction,
        "식후 1시간 걷기 (${(settings.walking60Reduction * 100).toInt()}% 감량)" to settings.walking60Reduction,
        "식후 30분 달리기 (${(settings.running30Reduction * 100).toInt()}% 감량)" to settings.running30Reduction,
        "식후 1시간 달리기 (${(settings.running60Reduction * 100).toInt()}% 감량)" to settings.running60Reduction
    )

    // Calculation logic
    val currentGlucose = viewModel.inputGlucose.toIntOrNull()
    val carbs = viewModel.inputCarbs.toFloatOrNull() ?: 0f

    val foodDose = if (settings.icr > 0f) carbs / settings.icr else 0f
    val correctionDose = if (currentGlucose != null && settings.isf > 0f) {
        (currentGlucose - settings.targetGlucose).toFloat() / settings.isf
    } else {
        0f
    }

    val preExerciseTotal = foodDose + correctionDose
    val reductionRate = exerciseOptions.getOrNull(viewModel.selectedExerciseIndex)?.second ?: 0f
    val exerciseReduction = if (preExerciseTotal > 0f) preExerciseTotal * reductionRate else 0f

    val rawFinalDose = if (preExerciseTotal - exerciseReduction > 0f) preExerciseTotal - exerciseReduction else 0f

    val finalDose = when (settings.roundingMode) {
        "0.5" -> (rawFinalDose * 2f).roundToInt() / 2f
        "1.0" -> rawFinalDose.roundToInt().toFloat()
        else -> rawFinalDose // NONE
    }

    // Determine glucose state color
    val glucoseColor = when {
        currentGlucose == null -> TextGray
        currentGlucose < 70 -> GlucoseLow
        currentGlucose <= 140 -> GlucoseStable
        currentGlucose <= 180 -> GlucoseWarning
        else -> GlucoseHigh
    }

    val glucoseStatusText = when {
        currentGlucose == null -> "혈당을 입력하세요"
        currentGlucose < 70 -> "저혈당 경보"
        currentGlucose <= 140 -> "정상 혈당 범위"
        currentGlucose <= 180 -> "조금 높은 혈당"
        else -> "고혈당 경보"
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .padding(bottom = 16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Glycemic Header Summary Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = SlateCardBg),
            shape = RoundedCornerShape(24.dp)
        ) {
            Column(
                modifier = Modifier.padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            text = "나의 당뇨 상태 요약",
                            color = TextGray,
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Medium
                        )
                        Text(
                            text = if (settings.libreConnected) "LibreView 연동됨" else "데모 모드 (가상 데이터)",
                            color = if (settings.libreConnected) GlucoseStable else TextMuted,
                            fontSize = 11.sp,
                            fontWeight = if (settings.libreConnected) FontWeight.Bold else FontWeight.Normal
                        )
                    }
                    
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        // Badge redirect to settings
                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(8.dp))
                                .background(PrimaryTeal.copy(alpha = 0.1f))
                                .clickable { viewModel.currentTab = 3 } // Navigate to settings
                                .padding(horizontal = 8.dp, vertical = 4.dp)
                        ) {
                            Text(
                                text = "연동 설정",
                                color = PrimaryTealLight,
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }

                        // Refresh button
                        if (viewModel.isSyncing) {
                            CircularProgressIndicator(
                                color = PrimaryTeal,
                                modifier = Modifier.size(16.dp),
                                strokeWidth = 2.dp
                            )
                        } else {
                            Icon(
                                imageVector = Icons.Default.Refresh,
                                contentDescription = "새로고침",
                                tint = TextGray,
                                modifier = Modifier
                                    .size(20.dp)
                                    .clickable { viewModel.syncLibreData() }
                            )
                        }
                    }
                }

                HorizontalDivider(color = SlateBorder)

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    // HbA1c
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(text = "당화혈색소 추정치", color = TextGray, fontSize = 12.sp)
                        Text(text = "${String.format(Locale.US, "%.1f", settings.libreHbA1c)} %", color = TextWhite, fontSize = 22.sp, fontWeight = FontWeight.Bold)
                    }
                    // Divider
                    Box(
                        modifier = Modifier
                            .width(1.dp)
                            .height(40.dp)
                            .background(SlateBorder)
                    )
                    // Avg Glucose
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(text = "일주일 평균 혈당", color = TextGray, fontSize = 12.sp)
                        Text(text = "${settings.libreAvgGlucose.toInt()} mg/dL", color = TextWhite, fontSize = 22.sp, fontWeight = FontWeight.Bold)
                    }
                }

                HorizontalDivider(color = SlateBorder.copy(alpha = 0.5f))
                
                Text(
                    text = "최근 일주일 혈당 변화 추이",
                    color = TextWhite,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(top = 4.dp)
                )

                if (readings.isEmpty()) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(110.dp)
                            .background(SlateDarkBg, RoundedCornerShape(12.dp)),
                        contentAlignment = Alignment.Center
                    ) {
                        Text("혈당 데이터가 없습니다.", color = TextGray, fontSize = 12.sp)
                    }
                } else {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(115.dp)
                            .clip(RoundedCornerShape(12.dp))
                            .background(SlateDarkBg)
                            .padding(horizontal = 8.dp, vertical = 6.dp)
                    ) {
                        GlucoseLineChart(
                            readings = readings,
                            modifier = Modifier.fillMaxSize()
                        )

                        // Y-Axis Overlay
                        Column(
                            modifier = Modifier
                                .fillMaxHeight()
                                .align(Alignment.CenterStart)
                                .padding(start = 4.dp, top = 2.dp, bottom = 2.dp),
                            verticalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(text = "300", color = TextMuted, fontSize = 8.sp)
                            Text(text = "180", color = GlucoseHigh.copy(alpha = 0.7f), fontSize = 8.sp, fontWeight = FontWeight.Bold)
                            Text(text = "120", color = PrimaryTealLight.copy(alpha = 0.5f), fontSize = 8.sp)
                            Text(text = "70", color = GlucoseLow.copy(alpha = 0.7f), fontSize = 8.sp, fontWeight = FontWeight.Bold)
                            Text(text = "40", color = TextMuted, fontSize = 8.sp)
                        }
                    }
                }
            }
        }

        // Insulin Calculation Input Fields
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = SlateCardBg),
            shape = RoundedCornerShape(24.dp)
        ) {
            Column(
                modifier = Modifier.padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                Text(
                    text = "속효성 인슐린 주사 계산기",
                    color = TextWhite,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold
                )

                // Input current glucose
                OutlinedTextField(
                    value = viewModel.inputGlucose,
                    onValueChange = { viewModel.inputGlucose = it },
                    label = { Text("식전 현재 혈당 (mg/dL)") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    shape = RoundedCornerShape(12.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = TextWhite,
                        unfocusedTextColor = TextWhite,
                        focusedBorderColor = PrimaryTeal,
                        unfocusedBorderColor = SlateBorder,
                        focusedLabelColor = PrimaryTeal,
                        unfocusedLabelColor = TextGray
                    ),
                    modifier = Modifier.fillMaxWidth(),
                    trailingIcon = {
                        Text(
                            text = glucoseStatusText,
                            color = glucoseColor,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(end = 8.dp)
                        )
                    }
                )

                // Input Carbohydrates
                OutlinedTextField(
                    value = viewModel.inputCarbs,
                    onValueChange = { viewModel.inputCarbs = it },
                    label = { Text("식사 탄수화물량 (g)") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    shape = RoundedCornerShape(12.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = TextWhite,
                        unfocusedTextColor = TextWhite,
                        focusedBorderColor = PrimaryTeal,
                        unfocusedBorderColor = SlateBorder,
                        focusedLabelColor = PrimaryTeal,
                        unfocusedLabelColor = TextGray
                    ),
                    modifier = Modifier.fillMaxWidth(),
                    placeholder = { Text("0") }
                )

                // Post-meal exercise selection dropdown
                var exerciseExpanded by remember { mutableStateOf(false) }
                Column(modifier = Modifier.fillMaxWidth()) {
                    Text(
                        text = "식후 예정 운동",
                        color = TextGray,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Medium,
                        modifier = Modifier.padding(bottom = 6.dp)
                    )
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .border(1.dp, SlateBorder, RoundedCornerShape(12.dp))
                            .clickable { exerciseExpanded = true }
                            .padding(horizontal = 16.dp, vertical = 14.dp)
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = exerciseOptions.getOrNull(viewModel.selectedExerciseIndex)?.first ?: "선택 없음",
                                color = TextWhite,
                                fontSize = 15.sp
                            )
                            Icon(
                                imageVector = if (exerciseExpanded) Icons.Default.KeyboardArrowUp else Icons.Default.KeyboardArrowDown,
                                contentDescription = null,
                                tint = TextGray
                            )
                        }
                    }

                    DropdownMenu(
                        expanded = exerciseExpanded,
                        onDismissRequest = { exerciseExpanded = false },
                        modifier = Modifier
                            .fillMaxWidth(0.9f)
                            .background(SlateCardBg)
                            .border(1.dp, SlateBorder, RoundedCornerShape(8.dp))
                    ) {
                        exerciseOptions.forEachIndexed { index, (label, _) ->
                            DropdownMenuItem(
                                text = { Text(label, color = TextWhite) },
                                onClick = {
                                    viewModel.selectedExerciseIndex = index
                                    exerciseExpanded = false
                                }
                            )
                        }
                    }
                }

                // Meal Photo Attachment (Before Meal)
                Column(modifier = Modifier.fillMaxWidth()) {
                    Text(
                        text = "식사 전 음식 사진 첨부",
                        color = TextGray,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Medium,
                        modifier = Modifier.padding(bottom = 6.dp)
                    )
                    
                    if (viewModel.tempPhotoBefore.isEmpty()) {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(100.dp)
                                .border(1.dp, SlateBorder, RoundedCornerShape(12.dp))
                                .background(SlateDarkBg.copy(alpha = 0.5f))
                                .clickable {
                                    photoPickerLauncher.launch(
                                        PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)
                                    )
                                },
                            contentAlignment = Alignment.Center
                        ) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                Text("+ 식사 전 사진 등록", color = PrimaryTealLight, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                                Spacer(modifier = Modifier.height(4.dp))
                                Text("식사 섭취 전 사진을 기록합니다.", color = TextMuted, fontSize = 11.sp)
                            }
                        }
                    } else {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(160.dp)
                                .clip(RoundedCornerShape(12.dp))
                                .border(1.dp, SlateBorder, RoundedCornerShape(12.dp))
                        ) {
                            val bitmap = remember(viewModel.tempPhotoBefore) {
                                try {
                                    BitmapFactory.decodeFile(viewModel.tempPhotoBefore)?.asImageBitmap()
                                } catch (e: Exception) {
                                    null
                                }
                            }
                            if (bitmap != null) {
                                Image(
                                    bitmap = bitmap,
                                    contentDescription = "식사 전 음식 사진",
                                    modifier = Modifier.fillMaxSize(),
                                    contentScale = ContentScale.Crop
                                )
                            }
                            
                            // Delete photo overlay button
                            Box(
                                modifier = Modifier
                                    .align(Alignment.TopEnd)
                                    .padding(8.dp)
                                    .clip(RoundedCornerShape(8.dp))
                                    .background(Color.Black.copy(alpha = 0.6f))
                                    .clickable { viewModel.tempPhotoBefore = "" }
                                    .padding(horizontal = 8.dp, vertical = 4.dp)
                            ) {
                                Text("삭제", color = Color.Red, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }
            }
        }

        // Calculation Results & Target Display
        if (currentGlucose != null || carbs > 0) {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = SlateCardBg),
                shape = RoundedCornerShape(24.dp)
            ) {
                Column(
                    modifier = Modifier.padding(20.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    Text(
                        text = "실시간 용량 계산서",
                        color = TextWhite,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.fillMaxWidth(),
                        textAlign = TextAlign.Start
                    )

                    // Display details
                    Column(
                        modifier = Modifier.fillMaxWidth(),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(text = "식사용 용량 (${carbs.toInt()}g / ICR ${settings.icr.toInt()}g)", color = TextGray, fontSize = 14.sp)
                            Text(text = "+ ${String.format(Locale.US, "%.2f", foodDose)} U", color = TextWhite, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                        }
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            val glucoseDiff = if (currentGlucose != null) currentGlucose - settings.targetGlucose else 0
                            Text(text = "혈당 교정 용량 (차이 ${glucoseDiff}mg / CF ${settings.isf.toInt()})", color = TextGray, fontSize = 14.sp)
                            val sign = if (correctionDose >= 0f) "+" else ""
                            Text(text = "$sign ${String.format(Locale.US, "%.2f", correctionDose)} U", color = if (correctionDose >= 0) TextWhite else GlucoseLow, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                        }
                        if (viewModel.selectedExerciseIndex > 0) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text(text = "식후 운동 감량 (${(reductionRate * 100).toInt()}% 감축)", color = TextGray, fontSize = 14.sp)
                                Text(text = "- ${String.format(Locale.US, "%.2f", exerciseReduction)} U", color = AccentOrangeLight, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                            }
                        }
                    }

                    HorizontalDivider(color = SlateBorder)

                    // Grand Result Display Circle
                    Box(
                        contentAlignment = Alignment.Center,
                        modifier = Modifier
                            .size(150.dp)
                            .border(
                                3.dp,
                                Brush.linearGradient(listOf(PrimaryTeal, AccentOrange)),
                                CircleShape
                            )
                            .background(SlateDarkBg, CircleShape)
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(
                                text = "권장 투여량",
                                color = TextGray,
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Medium
                            )
                            Text(
                                text = "${String.format(Locale.US, "%.1f", finalDose)} U",
                                color = AccentOrange,
                                fontSize = 36.sp,
                                fontWeight = FontWeight.ExtraBold
                            )
                            if (settings.roundingMode != "NONE") {
                                Text(
                                    text = "원합계: ${String.format(Locale.US, "%.2f", rawFinalDose)} U",
                                    color = TextMuted,
                                    fontSize = 11.sp
                                )
                            }
                        }
                    }

                    // Warning / Target range notification
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(12.dp))
                            .background(PrimaryTeal.copy(alpha = 0.05f))
                            .padding(12.dp),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            imageVector = Icons.Default.Info,
                            contentDescription = null,
                            tint = PrimaryTealLight,
                            modifier = Modifier.size(16.dp)
                        )
                        Text(
                            text = "목표 혈당 ${settings.targetGlucose} mg/dL을 기준하고 있으며, 반올림 옵션은 ${settings.roundingMode} 단위로 적용 중입니다.",
                            color = TextGray,
                            fontSize = 11.sp,
                            lineHeight = 15.sp
                        )
                    }

                    // Save Button
                    Button(
                        onClick = {
                            if (currentGlucose == null) return@Button
                            val exerciseName = when (viewModel.selectedExerciseIndex) {
                                1 -> "걷기 30분"
                                2 -> "걷기 1시간"
                                3 -> "달리기 30분"
                                4 -> "달리기 1시간"
                                else -> "없음"
                            }
                            val exerciseDuration = when (viewModel.selectedExerciseIndex) {
                                1, 3 -> 30
                                2, 4 -> 60
                                else -> 0
                            }
                            val log = LogEntry(
                                timestamp = System.currentTimeMillis(),
                                currentGlucose = currentGlucose,
                                carbs = carbs,
                                exerciseName = exerciseName,
                                exerciseDuration = exerciseDuration,
                                foodDose = foodDose,
                                correctionDose = correctionDose,
                                exerciseReduction = exerciseReduction,
                                finalDose = finalDose,
                                photoBefore = viewModel.tempPhotoBefore,
                                photoAfter = ""
                            )
                            viewModel.addLog(log)
                            Toast.makeText(context, "속효성 인슐린 ${finalDose}U 투여 및 로그 완료!", Toast.LENGTH_SHORT).show()
                            // Clear transient inputs
                            viewModel.inputGlucose = ""
                            viewModel.inputCarbs = ""
                            viewModel.selectedExerciseIndex = 0
                            viewModel.tempPhotoBefore = ""
                        },
                        enabled = currentGlucose != null,
                        colors = ButtonDefaults.buttonColors(
                            containerColor = PrimaryTeal,
                            contentColor = TextWhite,
                            disabledContainerColor = SlateBorder,
                            disabledContentColor = TextMuted
                        ),
                        shape = RoundedCornerShape(12.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text(
                            text = "기록 저장 및 투약 완료",
                            fontWeight = FontWeight.Bold,
                            fontSize = 15.sp
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun GlucoseLineChart(
    readings: List<Pair<Long, Int>>,
    modifier: Modifier = Modifier
) {
    if (readings.isEmpty()) return
    
    val minGlucose = 40f
    val maxGlucose = 300f
    
    val minTime = readings.first().first
    val maxTime = readings.last().first
    val timeRange = if (maxTime > minTime) (maxTime - minTime).toFloat() else 1f

    Canvas(modifier = modifier) {
        val width = size.width
        val height = size.height

        // 1. Draw horizontal threshold lines
        // High limit (180 mg/dL)
        val y180 = height - (((180f - minGlucose) / (maxGlucose - minGlucose)) * height)
        drawLine(
            color = GlucoseHigh.copy(alpha = 0.3f),
            start = Offset(0f, y180),
            end = Offset(width, y180),
            strokeWidth = 2f,
            pathEffect = PathEffect.dashPathEffect(floatArrayOf(10f, 10f), 0f)
        )

        // Low limit (70 mg/dL)
        val y70 = height - (((70f - minGlucose) / (maxGlucose - minGlucose)) * height)
        drawLine(
            color = GlucoseLow.copy(alpha = 0.3f),
            start = Offset(0f, y70),
            end = Offset(width, y70),
            strokeWidth = 2f,
            pathEffect = PathEffect.dashPathEffect(floatArrayOf(10f, 10f), 0f)
        )

        // Target (120 mg/dL)
        val y120 = height - (((120f - minGlucose) / (maxGlucose - minGlucose)) * height)
        drawLine(
            color = PrimaryTealLight.copy(alpha = 0.15f),
            start = Offset(0f, y120),
            end = Offset(width, y120),
            strokeWidth = 1f
        )

        // 2. Draw lines and fill area
        val points = readings.map { (time, value) ->
            val x = ((time - minTime).toFloat() / timeRange) * width
            val y = height - (((value.coerceIn(40, 300).toFloat() - minGlucose) / (maxGlucose - minGlucose)) * height)
            Offset(x, y)
        }

        if (points.isNotEmpty()) {
            val strokePath = Path().apply {
                moveTo(points.first().x, points.first().y)
                for (i in 1 until points.size) {
                    lineTo(points[i].x, points[i].y)
                }
            }

            val fillPath = Path().apply {
                moveTo(points.first().x, height)
                lineTo(points.first().x, points.first().y)
                for (i in 1 until points.size) {
                    lineTo(points[i].x, points[i].y)
                }
                lineTo(points.last().x, height)
                close()
            }

            // Fill area
            drawPath(
                path = fillPath,
                brush = Brush.verticalGradient(
                    colors = listOf(PrimaryTeal.copy(alpha = 0.25f), Color.Transparent),
                    startY = 0f,
                    endY = height
                )
            )

            // Draw line
            drawPath(
                path = strokePath,
                color = PrimaryTealLight,
                style = Stroke(
                    width = 4f,
                    cap = androidx.compose.ui.graphics.StrokeCap.Round,
                    join = androidx.compose.ui.graphics.StrokeJoin.Round
                )
            )
        }
    }
}
