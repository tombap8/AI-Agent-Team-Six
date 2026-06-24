import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome=120.0.0.0 Safari/537.36')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.set_capability('unhandledPromptBehavior', 'dismiss')

driver = webdriver.Chrome(options=options)
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})

try:
    url = 'https://data.krx.co.kr/'
    print(f"Loading {url}...")
    driver.get(url)
    
    time.sleep(2)
    
    # Click login button
    print("Clicking login button...")
    login_btn = driver.find_element(By.XPATH, "//a[contains(@href, 'MDCCOMS001.cmd')]")
    login_btn.click()
    
    print("Waiting 5 seconds for iframe...")
    time.sleep(5)
    
    # Dismiss alert if any
    try:
        alert = driver.switch_to.alert
        print("Dismissing alert:", alert.text)
        alert.dismiss()
    except:
        pass
        
    print("Switching to iframe...")
    driver.switch_to.frame("COMS001_FRAME")
    
    # Save iframe HTML source
    iframe_html_path = r"C:\Users\kosa\.gemini\antigravity-ide\brain\2c12c07b-f08d-485c-bf72-1b6e5048641e\scratch\iframe_source.html"
    with open(iframe_html_path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("Iframe HTML saved to:", iframe_html_path)
    
finally:
    driver.quit()
