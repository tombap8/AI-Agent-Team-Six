package com.example.insuladviser.ui.main

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.*
import androidx.compose.material3.TabRowDefaults.tabIndicatorOffset
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.insuladviser.theme.*
import java.util.Locale
import kotlin.math.roundToInt

data class FoodReference(val name: String, val category: String, val carbs: Float, val unitDescription: String)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NutritionScreen(
    viewModel: MainScreenViewModel,
    modifier: Modifier = Modifier
) {
    var activeSubTab by remember { mutableStateOf(0) } // 0: 탄수화물 식사 도우미, 1: 일일 필요량 계산기
    val scrollState = rememberScrollState()

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(bottom = 16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Tab selectors
        TabRow(
            selectedTabIndex = activeSubTab,
            containerColor = SlateDarkBg,
            contentColor = PrimaryTealLight,
            indicator = { tabPositions ->
                TabRowDefaults.SecondaryIndicator(
                    modifier = Modifier.tabIndicatorOffset(tabPositions[activeSubTab]),
                    color = PrimaryTeal
                )
            },
            divider = { Divider(color = SlateBorder) }
        ) {
            Tab(
                selected = activeSubTab == 0,
                onClick = { activeSubTab = 0 },
                text = { Text("식사 탄수화물 사전", fontWeight = FontWeight.Bold) }
            )
            Tab(
                selected = activeSubTab == 1,
                onClick = { activeSubTab = 1 },
                text = { Text("권장 탄수화물 계산기", fontWeight = FontWeight.Bold) }
            )
        }

        if (activeSubTab == 0) {
            // Food Dictionary & Meal Builder UI
            FoodDictionaryAndBuilder(viewModel)
        } else {
            // BMR & TDEE Calculator UI
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(scrollState),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                DailyCarbohydrateCalculator(viewModel)
            }
        }
    }
}

@Composable
fun ColumnScope.FoodDictionaryAndBuilder(viewModel: MainScreenViewModel) {
    val foodsDatabase = remember {
        listOf(
            FoodReference("흰쌀밥", "밥류", 65f, "1공기 (210g)"),
            FoodReference("현미밥", "밥류", 55f, "1공기 (210g)"),
            FoodReference("잡곡밥", "밥류", 58f, "1공기 (210g)"),
            FoodReference("라면", "면류", 80f, "1봉지"),
            FoodReference("식빵", "빵류", 15f, "1장"),
            FoodReference("피자", "간식류", 30f, "1조각"),
            FoodReference("짜장면", "면류", 120f, "1그릇"),
            FoodReference("떡볶이", "간식류", 80f, "1인분"),
            FoodReference("바나나", "과일류", 25f, "1개"),
            FoodReference("사과", "과일류", 20f, "1개 (중)"),
            FoodReference("귤", "과일류", 10f, "1개"),
            FoodReference("콜라", "음료류", 27f, "1캔 (250ml)"),
            FoodReference("우유", "음료류", 12f, "1컵 (200ml)"),
            FoodReference("고구마", "구황작물", 30f, "1개 (중, 120g)"),
            FoodReference("감자", "구황작물", 20f, "1개 (중, 130g)"),
            FoodReference("삶은 계란", "단백질", 1f, "1개"),
            FoodReference("닭가슴살", "단백질", 0f, "1팩 (100g)"),
            FoodReference("사과 주스", "음료류", 30f, "1컵 (200ml)")
        )
    }

    var searchQuery by remember { mutableStateOf("") }
    val filteredFoods = remember(searchQuery) {
        if (searchQuery.isBlank()) {
            foodsDatabase
        } else {
            foodsDatabase.filter { it.name.contains(searchQuery, ignoreCase = true) || it.category.contains(searchQuery, ignoreCase = true) }
        }
    }

    // Top section: Cart / Meal Builder
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
                    text = "임시 식사 담기 (Meal Builder)",
                    color = TextWhite,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Bold
                )
                if (viewModel.mealItems.isNotEmpty()) {
                    Text(
                        text = "초기화",
                        color = AccentOrangeLight,
                        fontSize = 12.sp,
                        modifier = Modifier.clickable { viewModel.clearMeal() }
                    )
                }
            }

            if (viewModel.mealItems.isEmpty()) {
                Text(
                    text = "사전에서 음식을 검색하여 식단을 완성하세요.",
                    color = TextMuted,
                    fontSize = 13.sp,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 12.dp),
                    textAlign = TextAlign.Center
                )
            } else {
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    viewModel.mealItems.forEach { item ->
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column(modifier = Modifier.weight(1f)) {
                                Text(text = item.name, color = TextWhite, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                                Text(
                                    text = "단당 ${(item.carbsPerUnit).toInt()}g x ${item.quantity}개",
                                    color = TextGray,
                                    fontSize = 11.sp
                                )
                            }
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                Box(
                                    modifier = Modifier
                                        .size(24.dp)
                                        .border(1.dp, SlateBorder, RoundedCornerShape(4.dp))
                                        .clickable { viewModel.removeFoodFromMeal(item.name) },
                                    contentAlignment = Alignment.Center
                                ) {
                                    Text(text = "-", color = TextWhite, fontSize = 16.sp)
                                }
                                Text(
                                    text = "${item.quantity}",
                                    color = TextWhite,
                                    fontSize = 14.sp,
                                    fontWeight = FontWeight.Bold
                                )
                                Box(
                                    modifier = Modifier
                                        .size(24.dp)
                                        .border(1.dp, SlateBorder, RoundedCornerShape(4.dp))
                                        .clickable { viewModel.addFoodToMeal(item.name, item.carbsPerUnit) },
                                    contentAlignment = Alignment.Center
                                ) {
                                    Text(text = "+", color = TextWhite, fontSize = 14.sp)
                                }
                            }
                        }
                    }

                    Divider(color = SlateBorder)

                    val totalCarbs = viewModel.mealItems.sumOf { (it.carbsPerUnit * it.quantity).toDouble() }.toFloat()

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(text = "총 탄수화물 합계", color = TextWhite, fontWeight = FontWeight.Bold)
                        Text(
                            text = "${totalCarbs.toInt()} g",
                            color = AccentOrange,
                            fontSize = 20.sp,
                            fontWeight = FontWeight.ExtraBold
                        )
                    }

                    Button(
                        onClick = { viewModel.sendMealCarbsToCalculator() },
                        colors = ButtonDefaults.buttonColors(containerColor = PrimaryTeal),
                        shape = RoundedCornerShape(10.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text(text = "인슐린 계산기로 총 탄수화물량 전송", fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
    }

    // Search bar
    OutlinedTextField(
        value = searchQuery,
        onValueChange = { searchQuery = it },
        placeholder = { Text("음식명 또는 카테고리 검색") },
        leadingIcon = { Icon(imageVector = Icons.Default.Search, contentDescription = null, tint = TextGray) },
        trailingIcon = {
            if (searchQuery.isNotEmpty()) {
                Icon(
                    imageVector = Icons.Default.Clear,
                    contentDescription = null,
                    tint = TextGray,
                    modifier = Modifier.clickable { searchQuery = "" }
                )
            }
        },
        shape = RoundedCornerShape(12.dp),
        colors = OutlinedTextFieldDefaults.colors(
            focusedTextColor = TextWhite,
            unfocusedTextColor = TextWhite,
            focusedBorderColor = PrimaryTeal,
            unfocusedBorderColor = SlateBorder
        ),
        modifier = Modifier.fillMaxWidth()
    )

    // Food List
    Text(
        text = "자주 찾는 한국인 탄수화물 사전",
        color = TextGray,
        fontSize = 12.sp,
        fontWeight = FontWeight.Medium
    )

    LazyColumn(
        verticalArrangement = Arrangement.spacedBy(8.dp),
        modifier = Modifier.weight(1f)
    ) {
        items(filteredFoods) { food ->
            Card(
                colors = CardDefaults.cardColors(containerColor = SlateCardBg.copy(alpha = 0.5f)),
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .border(0.5.dp, SlateBorder, RoundedCornerShape(12.dp))
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 12.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(text = food.name, color = TextWhite, fontSize = 15.sp, fontWeight = FontWeight.Bold)
                            Spacer(modifier = Modifier.width(6.dp))
                            Box(
                                modifier = Modifier
                                    .clip(RoundedCornerShape(4.dp))
                                    .background(SlateBorder)
                                    .padding(horizontal = 4.dp, vertical = 1.dp)
                            ) {
                                Text(text = food.category, color = TextMuted, fontSize = 9.sp)
                            }
                        }
                        Text(text = "기준량: ${food.unitDescription}", color = TextGray, fontSize = 12.sp)
                    }
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = "${food.carbs.toInt()}g",
                            color = AccentOrangeLight,
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(end = 12.dp)
                        )
                        IconButton(
                            onClick = { viewModel.addFoodToMeal(food.name, food.carbs) },
                            modifier = Modifier
                                .size(32.dp)
                                .clip(CircleShape)
                                .background(PrimaryTeal.copy(alpha = 0.1f))
                        ) {
                            Icon(
                                imageVector = Icons.Default.Add,
                                contentDescription = null,
                                tint = PrimaryTealLight,
                                modifier = Modifier.size(16.dp)
                            )
                        }
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DailyCarbohydrateCalculator(viewModel: MainScreenViewModel) {
    val activityLevels = listOf("활동 거의 없음", "가벼운 활동 (주 1~3회)", "보통 활동 (주 3~5회)", "많은 활동 (주 6~7회)")
    var activityExpanded by remember { mutableStateOf(false) }

    // BMR & TDEE Mifflin-St Jeor Calculation
    val weight = viewModel.bmrWeight.toFloatOrNull() ?: 0f
    val height = viewModel.bmrHeight.toFloatOrNull() ?: 0f
    val age = viewModel.bmrAge.toFloatOrNull() ?: 0f

    val bmr = if (viewModel.bmrGender == "남성") {
        10f * weight + 6.25f * height - 5f * age + 5f
    } else {
        10f * weight + 6.25f * height - 5f * age - 161f
    }

    val activityFactor = when (viewModel.bmrActivity) {
        "활동 거의 없음" -> 1.2f
        "가벼운 활동 (주 1~3회)" -> 1.375f
        "보통 활동 (주 3~5회)" -> 1.55f
        "많은 활동 (주 6~7회)" -> 1.725f
        else -> 1.2f
    }

    val tdee = bmr * activityFactor

    // Target Carbohydrates Target in grams
    // Standard: 50% of TDEE energy. 1g Carb = 4 kcal
    val standardCarbs = (tdee * 0.50f) / 4f
    // Low Carb: 35% of TDEE energy
    val lowCarbs = (tdee * 0.35f) / 4f

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
                text = "일일 에너지 소비량 & 탄수화물 계산기",
                color = TextWhite,
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold
            )

            // Gender select
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.clickable { viewModel.bmrGender = "남성" }
                ) {
                    RadioButton(
                        selected = viewModel.bmrGender == "남성",
                        onClick = { viewModel.bmrGender = "남성" },
                        colors = RadioButtonDefaults.colors(selectedColor = PrimaryTeal)
                    )
                    Text("남성", color = TextWhite)
                }
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.clickable { viewModel.bmrGender = "여성" }
                ) {
                    RadioButton(
                        selected = viewModel.bmrGender == "여성",
                        onClick = { viewModel.bmrGender = "여성" },
                        colors = RadioButtonDefaults.colors(selectedColor = PrimaryTeal)
                    )
                    Text("여성", color = TextWhite)
                }
            }

            // Age
            OutlinedTextField(
                value = viewModel.bmrAge,
                onValueChange = { viewModel.bmrAge = it },
                label = { Text("나이 (세)") },
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

            // Height
            OutlinedTextField(
                value = viewModel.bmrHeight,
                onValueChange = { viewModel.bmrHeight = it },
                label = { Text("신장 (cm)") },
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

            // Weight
            OutlinedTextField(
                value = viewModel.bmrWeight,
                onValueChange = { viewModel.bmrWeight = it },
                label = { Text("체중 (kg)") },
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

            // Activity level dropdown
            Column(modifier = Modifier.fillMaxWidth()) {
                Text(
                    text = "활동 수준",
                    color = TextGray,
                    fontSize = 12.sp,
                    modifier = Modifier.padding(bottom = 6.dp)
                )
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .border(1.dp, SlateBorder, RoundedCornerShape(10.dp))
                        .clickable { activityExpanded = true }
                        .padding(horizontal = 16.dp, vertical = 14.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(text = viewModel.bmrActivity, color = TextWhite, fontSize = 14.sp)
                        Icon(
                            imageVector = if (activityExpanded) Icons.Default.KeyboardArrowUp else Icons.Default.KeyboardArrowDown,
                            contentDescription = null,
                            tint = TextGray
                        )
                    }
                }

                DropdownMenu(
                    expanded = activityExpanded,
                    onDismissRequest = { activityExpanded = false },
                    modifier = Modifier
                        .fillMaxWidth(0.85f)
                        .background(SlateCardBg)
                ) {
                    activityLevels.forEach { level ->
                        DropdownMenuItem(
                            text = { Text(level, color = TextWhite) },
                            onClick = {
                                viewModel.bmrActivity = level
                                activityExpanded = false
                            }
                        )
                    }
                }
            }
        }
    }

    // Results Display Card
    if (weight > 0f && height > 0f && age > 0f) {
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
                    text = "칼로리 및 영양 분석 결과",
                    color = TextWhite,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(text = "기초 대사량 (BMR)", color = TextGray)
                    Text(text = "${bmr.roundToInt()} kcal", color = TextWhite, fontWeight = FontWeight.Bold)
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(text = "일일 총 대사량 (TDEE)", color = TextGray)
                    Text(text = "${tdee.roundToInt()} kcal", color = PrimaryTealLight, fontWeight = FontWeight.Bold)
                }

                Divider(color = SlateBorder)

                Column(
                    modifier = Modifier.fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(8.dp))
                            .background(SlateDarkBg)
                            .padding(12.dp)
                    ) {
                        Text(text = "표준 탄수화물 식단 (50% 칼로리)", color = TextGray, fontSize = 12.sp)
                        Spacer(modifier = Modifier.height(4.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = "하루 권장량",
                                color = TextWhite,
                                fontSize = 14.sp
                            )
                            Text(
                                text = "${standardCarbs.roundToInt()} g / 하루",
                                color = AccentOrange,
                                fontSize = 18.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                        Text(
                            text = "끼니당 평균 약 ${(standardCarbs / 3f).roundToInt()}g 분배 권장",
                            color = TextMuted,
                            fontSize = 11.sp
                        )
                    }

                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(8.dp))
                            .background(SlateDarkBg)
                            .padding(12.dp)
                    ) {
                        Text(text = "저탄수화물 식단 (35% 칼로리)", color = TextGray, fontSize = 12.sp)
                        Spacer(modifier = Modifier.height(4.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = "하루 권장량",
                                color = TextWhite,
                                fontSize = 14.sp
                            )
                            Text(
                                text = "${lowCarbs.roundToInt()} g / 하루",
                                color = PrimaryTealLight,
                                fontSize = 18.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                        Text(
                            text = "끼니당 평균 약 ${(lowCarbs / 3f).roundToInt()}g 분배 권장",
                            color = TextMuted,
                            fontSize = 11.sp
                        )
                    }
                }

                Text(
                    text = "참조 사이트: calculator.net Carbohydrate Calculator 가이드라인을 기반하여 계산되었습니다.",
                    color = TextMuted,
                    fontSize = 10.sp,
                    lineHeight = 14.sp
                )
            }
        }
    }
}
