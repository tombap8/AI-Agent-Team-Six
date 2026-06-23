# Insulin Dose Advisor Web Application (Streamlit)

This is a Streamlit-based web application version of the Insulin Dose Advisor, ported from the Jetpack Compose Android app. It calculates rapid-acting insulin doses, tracks meals and exercises, provides a food carbohydrate dictionary, Mifflin-St Jeor TDEE calculator, LibreLinkUp CGMS syncing, and an interactive ICR tuning system.

## Setup Instructions

### 1. Prerequisites
Ensure you have Python 3.8+ installed on your computer.

### 2. Create a Virtual Environment
Navigate to this directory in your terminal and run:
```bash
python -m venv .venv
```

### 3. Activate the Virtual Environment
- **Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Windows (Command Prompt):**
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **macOS / Linux:**
  ```bash
  source .venv/bin/activate
  ```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the Application
```bash
streamlit run app.py
```
The application will automatically open in your default browser at `http://localhost:8501`.

## Features
- **Insulin Dose Calculator**: Calculate food and correction insulin based on pre-meal glucose, carbs, and post-meal exercise.
- **LibreLinkUp CGMS Syncing**: Sync real-time glucose graphs, estimated HbA1c, and average weekly glucose. Runs in mock/demo mode by default.
- **Food Carb Dictionary & Meal Builder**: Custom carbohydrate calculator for typical Korean foods.
- **TDEE & Recommended Carbs Calculator**: Personalized daily carb goals.
- **Insulin Log History**: Persistent record tracking with meal photos and post-meal blood glucose ICR tuning.
