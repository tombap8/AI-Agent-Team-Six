# -*- coding: utf-8 -*-
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

# Load .env (located in parent folder of utils)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(os.path.join(parent_dir, '.env'))

def get_krx_cookie(force_new=False):
    cookie_file = os.path.join(os.path.dirname(__file__), 'krx_cookie.txt')
    
    # Check cache (valid for 15 minutes)
    if not force_new and os.path.exists(cookie_file):
        mtime = os.path.getmtime(cookie_file)
        if time.time() - mtime < 900:  # 15 minutes
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookie = f.read().strip()
                if cookie:
                    print("[KRX Login] Using cached cookie.")
                    return cookie
                    
    print("[KRX Login] Obtaining new cookie via headless Chrome...")
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Automatically dismiss unexpected alert dialogs
    options.set_capability('unhandledPromptBehavior', 'dismiss')
    
    driver = webdriver.Chrome(options=options)
    
    # Stealth: Bypass navigator.webdriver detection
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
    def handle_alert():
        try:
            alert = driver.switch_to.alert
            alert_text = alert.text
            print(f"[KRX Login] Handled active alert: {alert_text}")
            alert.dismiss()
            time.sleep(1)
            return True
        except:
            return False
            
    try:
        # Load main page
        driver.get('https://data.krx.co.kr/')
        handle_alert()
        
        # Click login button in header
        login_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'MDCCOMS001.cmd')]"))
        )
        login_btn.click()
        
        # Wait and switch to COMS001_FRAME iframe, handling alerts
        switched = False
        start_time = time.time()
        while time.time() - start_time < 20:
            try:
                WebDriverWait(driver, 2).until(
                    EC.frame_to_be_available_and_switch_to_it((By.ID, "COMS001_FRAME"))
                )
                print("[KRX Login] Successfully switched to COMS001_FRAME iframe.")
                switched = True
                break
            except Exception as e:
                if handle_alert():
                    continue
                time.sleep(0.5)
                
        if not switched:
            raise Exception("Timed out waiting to switch to COMS001_FRAME iframe.")
            
        # Locate login inputs inside iframe
        username_field = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "mbrId"))
        )
        username_field.send_keys(os.getenv("KRX_USER_ID", "jhsong89"))
        
        password_field = driver.find_element(By.NAME, "pw")
        password_field.send_keys(os.getenv("KRX_USER_PW", "s@4452009"))
        
        # Submit login form
        submit_btn = driver.find_element(By.XPATH, "//a[contains(@class, 'jsLoginBtn')]")
        driver.execute_script("arguments[0].click();", submit_btn)
        
        # Wait and handle duplicate login popups inside the iframe
        time.sleep(3)
        handle_alert()
        
        # Look for the confirm "확인" button inside the iframe
        try:
            confirm_btns = driver.find_elements(By.XPATH, "//button[contains(@class, 'btn-confirm')]")
            if len(confirm_btns) > 0:
                print("[KRX Login] Duplicate login alert detected inside iframe. Clicking confirm button...")
                driver.execute_script("arguments[0].click();", confirm_btns[0])
                time.sleep(5)
            else:
                print("[KRX Login] No duplicate login popup found inside iframe.")
        except Exception as ce:
            print(f"[KRX Login] Failed to check/click duplicate alert: {ce}")
            
        # Switch to parent window for final diagnostics and cookie retrieval
        driver.switch_to.default_content()
            
        # Wait for authentication redirect
        time.sleep(5)
        handle_alert()
        
        # Diagnostics
        print("[KRX Login] Post-login URL:", driver.current_url)
        print("[KRX Login] Post-login Title:", driver.title)
        screenshot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'post_login.png')
        driver.save_screenshot(screenshot_path)
        print("[KRX Login] Post-login screenshot saved to:", screenshot_path)
        
        # Switch back to default context
        try:
            driver.switch_to.default_content()
        except:
            handle_alert()
            driver.switch_to.default_content()
        
        # Extract ALL cookies
        cookies = driver.get_cookies()
        print(f"[KRX Login] All retrieved cookies: {[(c['name'], c['value']) for c in cookies]}")
        
        # Format cookies as a single header string
        cookie_parts = []
        for cookie in cookies:
            cookie_parts.append(f"{cookie['name']}={cookie['value']}")
            
        if cookie_parts:
            cookie_str = "; ".join(cookie_parts)
            # Make sure mdc.client_session is set to true
            if "mdc.client_session" not in cookie_str:
                cookie_str += "; mdc.client_session=true"
                
            with open(cookie_file, 'w', encoding='utf-8') as f:
                f.write(cookie_str)
            print("[KRX Login] Successfully obtained new cookie header.")
            return cookie_str
        else:
            raise Exception("No cookies found after login.")
            
    except Exception as e:
        print(f"[KRX Login] Error during automated login: {e}")
        raise e
    finally:
        driver.quit()

if __name__ == "__main__":
    cookie = get_krx_cookie(force_new=True)
    print("Retrieved Cookie:", cookie)
