package com.example.insuladviser.ui.main

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.insuladviser.data.AppSettings
import com.example.insuladviser.theme.*
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    viewModel: MainScreenViewModel,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val settings by viewModel.settingsState.collectAsState()
    val scrollState = rememberScrollState()

    // Local states for text fields
    var targetGlucoseStr by remember(settings.targetGlucose) { mutableStateOf(settings.targetGlucose.toString()) }
    var icrStr by remember(settings.icr) { mutableStateOf(settings.icr.toString()) }
    var isfStr by remember(settings.isf) { mutableStateOf(settings.isf.toString()) }
    var roundingMode by remember(settings.roundingMode) { mutableStateOf(settings.roundingMode) }

    // Exercise reduction rates slider local states
    var walk30Rate by remember(settings.walking30Reduction) { mutableStateOf(settings.walking30Reduction) }
    var walk60Rate by remember(settings.walking60Reduction) { mutableStateOf(settings.walking60Reduction) }
    var run30Rate by remember(settings.running30Reduction) { mutableStateOf(settings.running30Reduction) }
    var run60Rate by remember(settings.running60Reduction) { mutableStateOf(settings.running60Reduction) }

    var libreEmail by remember(settings.libreEmail) { mutableStateOf(settings.libreEmail) }
    var librePassword by remember(settings.librePassword) { mutableStateOf(settings.librePassword) }
    var libreRegion by remember(settings.libreRegion) { mutableStateOf(settings.libreRegion) }

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .padding(bottom = 16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Group 1: Core Coefficients Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = SlateCardBg),
            shape = RoundedCornerShape(20.dp)
        ) {
            Column(
                modifier = Modifier.padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                Text(
                    text = "의학 기초 매개변수 설정",
                    color = TextWhite,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )

                // Target Blood Glucose
                OutlinedTextField(
                    value = targetGlucoseStr,
                    onValueChange = { targetGlucoseStr = it },
                    label = { Text("식사 전 목표 혈당 (mg/dL)") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    shape = RoundedCornerShape(10.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = TextWhite,
                        unfocusedTextColor = TextWhite,
                        focusedBorderColor = PrimaryTeal,
                        unfocusedBorderColor = SlateBorder
                    ),
                    modifier = Modifier.fillMaxWidth()
                )

                // ICR
                OutlinedTextField(
                    value = icrStr,
                    onValueChange = { icrStr = it },
                    label = { Text("탄수화물 계수 (ICR - 1U당 탄수화물g)") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                    shape = RoundedCornerShape(10.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = TextWhite,
                        unfocusedTextColor = TextWhite,
                        focusedBorderColor = PrimaryTeal,
                        unfocusedBorderColor = SlateBorder
                    ),
                    modifier = Modifier.fillMaxWidth()
                )

                // ISF
                OutlinedTextField(
                    value = isfStr,
                    onValueChange = { isfStr = it },
                    label = { Text("혈당 교정 계수 (ISF - 1U당 낮추는 혈당)") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                    shape = RoundedCornerShape(10.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = TextWhite,
                        unfocusedTextColor = TextWhite,
                        focusedBorderColor = PrimaryTeal,
                        unfocusedBorderColor = SlateBorder
                    ),
                    modifier = Modifier.fillMaxWidth()
                )
            }
        }

        // Group 2: Rounding mode Selector Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = SlateCardBg),
            shape = RoundedCornerShape(20.dp)
        ) {
            Column(
                modifier = Modifier.padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Text(
                    text = "인슐린 용량 반올림 설정",
                    color = TextWhite,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "주사기나 펜의 정밀도에 맞춰 계산 결과를 반올림합니다.",
                    color = TextGray,
                    fontSize = 12.sp,
                    lineHeight = 16.sp
                )

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    val modes = listOf("NONE" to "무반올림", "0.5" to "0.5 U 단위", "1.0" to "1.0 U 단위")
                    modes.forEach { (modeVal, label) ->
                        val selected = roundingMode == modeVal
                        Box(
                            modifier = Modifier
                                .weight(1f)
                                .clip(RoundedCornerShape(8.dp))
                                .background(if (selected) PrimaryTeal else SlateDarkBg)
                                .border(1.dp, if (selected) PrimaryTealLight else SlateBorder, RoundedCornerShape(8.dp))
                                .clickable { roundingMode = modeVal }
                                .padding(vertical = 10.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = label,
                                color = if (selected) TextWhite else TextGray,
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }
                }
            }
        }

        // Group 3: Custom Exercise Reduction rates Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = SlateCardBg),
            shape = RoundedCornerShape(20.dp)
        ) {
            Column(
                modifier = Modifier.padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                Text(
                    text = "운동에 따른 인슐린 감량 비율 설정",
                    color = TextWhite,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )

                // Walk 30 min
                Column {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(text = "식후 30분 걷기 감량율", color = TextGray, fontSize = 13.sp)
                        Text(text = "${(walk30Rate * 100).toInt()}%", color = PrimaryTealLight, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                    }
                    Slider(
                        value = walk30Rate,
                        onValueChange = { walk30Rate = it },
                        valueRange = 0f..0.8f,
                        colors = SliderDefaults.colors(
                            thumbColor = PrimaryTeal,
                            activeTrackColor = PrimaryTealLight,
                            inactiveTrackColor = SlateBorder
                        )
                    )
                }

                // Walk 60 min
                Column {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(text = "식후 1시간 걷기 감량율", color = TextGray, fontSize = 13.sp)
                        Text(text = "${(walk60Rate * 100).toInt()}%", color = PrimaryTealLight, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                    }
                    Slider(
                        value = walk60Rate,
                        onValueChange = { walk60Rate = it },
                        valueRange = 0f..0.8f,
                        colors = SliderDefaults.colors(
                            thumbColor = PrimaryTeal,
                            activeTrackColor = PrimaryTealLight,
                            inactiveTrackColor = SlateBorder
                        )
                    )
                }

                // Run 30 min
                Column {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(text = "식후 30분 달리기 감량율", color = TextGray, fontSize = 13.sp)
                        Text(text = "${(run30Rate * 100).toInt()}%", color = AccentOrange, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                    }
                    Slider(
                        value = run30Rate,
                        onValueChange = { run30Rate = it },
                        valueRange = 0f..0.8f,
                        colors = SliderDefaults.colors(
                            thumbColor = AccentOrange,
                            activeTrackColor = AccentOrangeLight,
                            inactiveTrackColor = SlateBorder
                        )
                    )
                }

                // Run 60 min
                Column {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(text = "식후 1시간 달리기 감량율", color = TextGray, fontSize = 13.sp)
                        Text(text = "${(run60Rate * 100).toInt()}%", color = AccentOrange, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                    }
                    Slider(
                        value = run60Rate,
                        onValueChange = { run60Rate = it },
                        valueRange = 0f..0.8f,
                        colors = SliderDefaults.colors(
                            thumbColor = AccentOrange,
                            activeTrackColor = AccentOrangeLight,
                            inactiveTrackColor = SlateBorder
                        )
                    )
                }
            }
        }

        // Group 4: LibreView Sync Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = SlateCardBg),
            shape = RoundedCornerShape(20.dp)
        ) {
            Column(
                modifier = Modifier.padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                Text(
                    text = "LibreView (Libre LinkUp) 연동 설정",
                    color = TextWhite,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "FreeStyle Libre 연속혈당측정기 계정을 연동하여 최근 일주일간의 혈당 변화 그래프와 당화혈색소 추정치를 가져옵니다.",
                    color = TextGray,
                    fontSize = 12.sp,
                    lineHeight = 16.sp
                )

                // Email
                OutlinedTextField(
                    value = libreEmail,
                    onValueChange = { libreEmail = it },
                    label = { Text("Libre LinkUp 이메일 주소") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                    shape = RoundedCornerShape(10.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = TextWhite,
                        unfocusedTextColor = TextWhite,
                        focusedBorderColor = PrimaryTeal,
                        unfocusedBorderColor = SlateBorder
                    ),
                    modifier = Modifier.fillMaxWidth()
                )

                // Password
                OutlinedTextField(
                    value = librePassword,
                    onValueChange = { librePassword = it },
                    label = { Text("비밀번호") },
                    visualTransformation = androidx.compose.ui.text.input.PasswordVisualTransformation(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                    shape = RoundedCornerShape(10.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = TextWhite,
                        unfocusedTextColor = TextWhite,
                        focusedBorderColor = PrimaryTeal,
                        unfocusedBorderColor = SlateBorder
                    ),
                    modifier = Modifier.fillMaxWidth()
                )

                // Region dropdown
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(text = "서버 지역 선택", color = TextGray, fontSize = 11.sp)
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(6.dp)
                    ) {
                        val regions = listOf("ap" to "한국/아태", "us" to "미국", "eu" to "유럽", "de" to "독일")
                        regions.forEach { (regVal, label) ->
                            val isSel = libreRegion == regVal
                            Box(
                                modifier = Modifier
                                    .weight(1f)
                                    .clip(RoundedCornerShape(6.dp))
                                    .background(if (isSel) PrimaryTeal else SlateDarkBg)
                                    .border(0.5.dp, if (isSel) PrimaryTealLight else SlateBorder, RoundedCornerShape(6.dp))
                                    .clickable { libreRegion = regVal }
                                    .padding(vertical = 8.dp),
                                contentAlignment = Alignment.Center
                            ) {
                                Text(
                                    text = label,
                                    color = if (isSel) TextWhite else TextGray,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                        }
                    }
                }

                HorizontalDivider(color = SlateBorder.copy(alpha = 0.5f))

                // Connection Status Indicators
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(text = "연결 상태", color = TextGray, fontSize = 12.sp)
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(6.dp)
                        ) {
                            Box(
                                modifier = Modifier
                                    .size(8.dp)
                                    .clip(androidx.compose.foundation.shape.CircleShape)
                                    .background(if (settings.libreConnected) GlucoseStable else AccentOrange)
                            )
                            Text(
                                text = if (settings.libreConnected) "연결됨 (실제 데이터)" else "데모 모드 (가상 데이터)",
                                color = if (settings.libreConnected) GlucoseStable else TextGray,
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                        if (settings.libreLastSyncTime > 0L) {
                            val syncDate = remember(settings.libreLastSyncTime) {
                                java.text.SimpleDateFormat("MM-dd HH:mm", java.util.Locale.getDefault()).format(java.util.Date(settings.libreLastSyncTime))
                            }
                            Text(text = "최근 동기화: $syncDate", color = TextMuted, fontSize = 11.sp, modifier = Modifier.padding(top = 2.dp))
                        }
                    }

                    // Disconnect button
                    if (settings.libreConnected) {
                        Button(
                            onClick = {
                                viewModel.disconnectLibre()
                                libreEmail = ""
                                librePassword = ""
                                Toast.makeText(context, "연동 해제 및 데모 데이터로 전환되었습니다.", Toast.LENGTH_SHORT).show()
                            },
                            colors = ButtonDefaults.buttonColors(containerColor = GlucoseHigh.copy(alpha = 0.15f)),
                            border = androidx.compose.foundation.BorderStroke(0.5.dp, GlucoseHigh),
                            shape = RoundedCornerShape(8.dp),
                            contentPadding = PaddingValues(horizontal = 12.dp, vertical = 6.dp)
                        ) {
                            Text("연동 해제", color = GlucoseHigh, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                        }
                    }
                }

                // Error alert
                viewModel.syncErrorMessage?.let { err ->
                    Text(
                        text = "❌ $err",
                        color = GlucoseHigh,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        lineHeight = 15.sp
                    )
                }

                // Sync and Test button
                Button(
                    onClick = {
                        val currentSettings = settings.copy(
                            libreEmail = libreEmail,
                            librePassword = librePassword,
                            libreRegion = libreRegion
                        )
                        viewModel.saveSettings(currentSettings)
                        viewModel.syncLibreData()
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = if (viewModel.isSyncing) SlateDarkBg else PrimaryTeal),
                    shape = RoundedCornerShape(10.dp),
                    enabled = !viewModel.isSyncing,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    if (viewModel.isSyncing) {
                        CircularProgressIndicator(color = PrimaryTeal, modifier = Modifier.size(18.dp))
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("동기화 중...", color = TextGray, fontSize = 13.sp)
                    } else {
                        Text(
                            text = if (settings.libreConnected) "혈당 정보 지금 업데이트" else "LibreView 동기화 시작",
                            fontWeight = FontWeight.Bold,
                            fontSize = 13.sp
                        )
                    }
                }
            }
        }

        // Save Button
        Button(
            onClick = {
                val targetGlucose = targetGlucoseStr.toIntOrNull()
                val icr = icrStr.toFloatOrNull()
                val isf = isfStr.toFloatOrNull()

                if (targetGlucose == null || icr == null || isf == null || icr <= 0f || isf <= 0f) {
                    Toast.makeText(context, "올바른 숫자를 입력하세요. 계수는 0보다 커야 합니다.", Toast.LENGTH_LONG).show()
                    return@Button
                }

                val newSettings = settings.copy(
                    targetGlucose = targetGlucose,
                    icr = icr,
                    isf = isf,
                    roundingMode = roundingMode,
                    walking30Reduction = walk30Rate,
                    walking60Reduction = walk60Rate,
                    running30Reduction = run30Rate,
                    running60Reduction = run60Rate,
                    libreEmail = libreEmail,
                    librePassword = librePassword,
                    libreRegion = libreRegion
                )

                viewModel.saveSettings(newSettings)
                Toast.makeText(context, "설정이 영구 저장되었습니다.", Toast.LENGTH_SHORT).show()
            },
            colors = ButtonDefaults.buttonColors(containerColor = PrimaryTeal),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(text = "설정 저장", fontWeight = FontWeight.Bold, fontSize = 15.sp)
        }
    }
}
