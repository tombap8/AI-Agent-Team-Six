package com.example.insuladviser.data

import android.util.Log
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Locale
import java.util.TimeZone

class LibreLinkUpClient {

    sealed class FetchResult {
        data class Success(
            val readings: List<Pair<Long, Int>>,
            val avgGlucose: Float,
            val estHbA1c: Float
        ) : FetchResult()
        
        data class Error(val message: String) : FetchResult()
    }

    private fun getBaseUrl(region: String): String {
        return when (region.lowercase(Locale.US)) {
            "us" -> "https://api-us.libreview.io"
            "eu" -> "https://api-eu.libreview.io"
            "ap" -> "https://api-ap.libreview.io"
            "de" -> "https://api-de.libreview.io"
            "fr" -> "https://api-fr.libreview.io"
            "jp" -> "https://api-jp.libreview.io"
            "ae" -> "https://api-ae.libreview.io"
            else -> "https://api.libreview.io" // Global fallback
        }
    }

    private fun parseIso8601(dateStr: String): Long {
        return try {
            // Take the first 19 characters: "yyyy-MM-ddTHH:mm:ss"
            val normalized = dateStr.take(19)
            val format = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US)
            format.timeZone = TimeZone.getTimeZone("UTC")
            format.parse(normalized)?.time ?: System.currentTimeMillis()
        } catch (e: Exception) {
            System.currentTimeMillis()
        }
    }

    fun fetchRecentGlucose(email: String, password: String, region: String): FetchResult {
        val baseUrl = getBaseUrl(region)
        
        try {
            // STEP 1: Login
            val loginUrl = URL("$baseUrl/llu/auth/login")
            val loginConn = loginUrl.openConnection() as HttpURLConnection
            loginConn.requestMethod = "POST"
            loginConn.setRequestProperty("Content-Type", "application/json")
            loginConn.setRequestProperty("version", "4.7.0")
            loginConn.setRequestProperty("product", "llu.android")
            loginConn.doOutput = true
            loginConn.connectTimeout = 8000
            loginConn.readTimeout = 8000

            val loginBody = JSONObject().apply {
                put("email", email)
                put("password", password)
            }

            OutputStreamWriter(loginConn.outputStream).use { writer ->
                writer.write(loginBody.toString())
                writer.flush()
            }

            val loginCode = loginConn.responseCode
            if (loginCode != HttpURLConnection.HTTP_OK && loginCode != HttpURLConnection.HTTP_CREATED) {
                val errMsg = readErrorStream(loginConn)
                return FetchResult.Error("로그인 실패 (코드: $loginCode). 아이디와 비밀번호를 확인해주세요.")
            }

            val loginResponse = readInputStream(loginConn)
            val loginJson = JSONObject(loginResponse)
            val status = loginJson.optInt("status", -1)
            
            // Check status or error message
            if (status != 0 && loginJson.has("errors")) {
                return FetchResult.Error("인증 오류: 계정 정보를 찾을 수 없습니다.")
            }

            val dataObj = loginJson.optJSONObject("data") ?: return FetchResult.Error("응답 데이터 오류")
            val authTicketObj = dataObj.optJSONObject("authTicket") ?: return FetchResult.Error("인증 티켓 획득 실패")
            val token = authTicketObj.optString("token", "")
            if (token.isEmpty()) return FetchResult.Error("인증 토큰이 비어 있습니다.")

            // STEP 2: Get Connections to find Patient ID
            val connUrl = URL("$baseUrl/llu/connections")
            val connConn = connUrl.openConnection() as HttpURLConnection
            connConn.requestMethod = "GET"
            connConn.setRequestProperty("Authorization", "Bearer $token")
            connConn.setRequestProperty("version", "4.7.0")
            connConn.setRequestProperty("product", "llu.android")
            connConn.connectTimeout = 8000
            connConn.readTimeout = 8000

            val connCode = connConn.responseCode
            if (connCode != HttpURLConnection.HTTP_OK) {
                return FetchResult.Error("연결 목록 조회 실패 (코드: $connCode)")
            }

            val connResponse = readInputStream(connConn)
            val connJson = JSONObject(connResponse)
            val connDataArr = connJson.optJSONArray("data")
            if (connDataArr == null || connDataArr.length() == 0) {
                return FetchResult.Error("연동된 CGM 환자 프로필이 없습니다. LibreLinkUp 앱에서 공유 초청을 먼저 승인해주세요.")
            }

            // Find patient (usually the self connection or first one)
            var patientId = ""
            for (i in 0 until connDataArr.length()) {
                val connItem = connDataArr.getJSONObject(i)
                val pid = connItem.optString("patientId", "")
                if (pid.isNotEmpty()) {
                    patientId = pid
                    break
                }
            }

            if (patientId.isEmpty()) {
                return FetchResult.Error("환자 ID를 찾을 수 없습니다.")
            }

            // STEP 3: Fetch Glucose Graph Data
            val graphUrl = URL("$baseUrl/llu/connections/$patientId/graph")
            val graphConn = graphUrl.openConnection() as HttpURLConnection
            graphConn.requestMethod = "GET"
            graphConn.setRequestProperty("Authorization", "Bearer $token")
            graphConn.setRequestProperty("version", "4.7.0")
            graphConn.setRequestProperty("product", "llu.android")
            graphConn.connectTimeout = 8000
            graphConn.readTimeout = 8000

            val graphCode = graphConn.responseCode
            if (graphCode != HttpURLConnection.HTTP_OK) {
                return FetchResult.Error("혈당 데이터 조회 실패 (코드: $graphCode)")
            }

            val graphResponse = readInputStream(graphConn)
            val graphJson = JSONObject(graphResponse)
            val graphDataObj = graphJson.optJSONObject("data") ?: return FetchResult.Error("혈당 그래프 데이터 응답 누락")
            val graphDataArr = graphDataObj.optJSONArray("graphData") ?: JSONArray()

            val readings = mutableListOf<Pair<Long, Int>>()
            var sumGlucose = 0
            var countReadings = 0

            for (i in 0 until graphDataArr.length()) {
                val item = graphDataArr.getJSONObject(i)
                val value = item.optInt("Value", -1)
                val timestampStr = item.optString("Timestamp", "")
                if (value > 0 && timestampStr.isNotEmpty()) {
                    val timeMs = parseIso8601(timestampStr)
                    readings.add(Pair(timeMs, value))
                    sumGlucose += value
                    countReadings++
                }
            }

            if (readings.isEmpty()) {
                return FetchResult.Error("최근 등록된 혈당 센서 기록이 없습니다.")
            }

            // Calculate average & estimated HbA1c
            val avgGlucose = sumGlucose.toFloat() / countReadings
            // ADAG formula: HbA1c = (AvgGlucose + 46.7) / 28.7
            val estHbA1c = (avgGlucose + 46.7f) / 28.7f

            return FetchResult.Success(
                readings = readings.sortedBy { it.first }, // Sort chronologically
                avgGlucose = avgGlucose,
                estHbA1c = estHbA1c
            )

        } catch (e: Exception) {
            Log.e("LibreLinkUpClient", "Error fetching glucose", e)
            return FetchResult.Error("네트워크 오류: ${e.localizedMessage ?: "서버에 연결할 수 없습니다."}")
        }
    }

    private fun readInputStream(conn: HttpURLConnection): String {
        return conn.inputStream.bufferedReader().use { it.readText() }
    }

    private fun readErrorStream(conn: HttpURLConnection): String {
        return try {
            conn.errorStream?.bufferedReader()?.use { it.readText() } ?: ""
        } catch (e: Exception) {
            ""
        }
    }
}
