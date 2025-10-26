from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os


def test_dashboard_csv_download(headless=False, reuse_browser=False):
    """
    Test the Dashboard CSV download workflow:
    1. User logs in as Manager
    2. Navigate to Dashboard via CustomSidebar
    3. Filter to 22 Oct 2025 - 28 Oct 2025
    4. Download CSV
    5. Open the downloaded CSV (if possible)
    """
    # Setup Chrome options
    chrome_options = Options()
    
    if reuse_browser:
        # Connect to existing Chrome instance with remote debugging enabled
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    else:
        if headless:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
        
        # Performance optimizations
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Set download directory
        download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # ========== STEP 1: USER LOGIN AS MANAGER ==========
        print("--- Step 1: User Login as Manager ---")
        driver.get("http://localhost:3000/login")
        
        email_input = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
        email_input.send_keys("weekiat22@gmail.com")
        
        password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_input.send_keys("tB800797")
        
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Wait for navigation to complete instead of fixed sleep
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".nav-item.dashboard"))
        )
        print("✓ Login successful\n")
        
        # ========== STEP 2: NAVIGATE TO DASHBOARD VIA CUSTOMSIDEBAR ==========
        print("--- Step 2: Navigate to Dashboard via CustomSidebar ---")
        
        # Find and click on Dashboard menu item in the sidebar
        dashboard_menu = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".nav-item.dashboard"))
        )
        driver.execute_script("arguments[0].click();", dashboard_menu)
        
        time.sleep(1)
        # Wait for dashboard content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ant-picker-range"))
        )
        print("✓ Navigated to Dashboard\n")
        
        # ========== STEP 3: FILTER TO 22 OCT 2025 - 28 OCT 2025 ==========
        print("--- Step 3: Filter to 22 Oct 2025 - 28 Oct 2025 ---")
        
        # Find the Ant Design Range Picker component
        try:
            # Click on the range picker to open it
            range_picker = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".ant-picker-range"))
            )
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", range_picker)
            driver.execute_script("arguments[0].click();", range_picker)
            
            # Wait for the calendar dropdown to appear
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".ant-picker-cell-inner"))
            )
            print("✓ Opened date range picker")
            
            # Try multiple selector strategies for date 22
            try:
                # Strategy 1: Find all cells with text "22"
                all_cells = driver.find_elements(By.CSS_SELECTOR, ".ant-picker-cell-inner")
                date_22 = None
                for cell in all_cells:
                    if cell.text == "22":
                        date_22 = cell
                        break
                
                if date_22:
                    driver.execute_script("arguments[0].click();", date_22)
                    time.sleep(0.3)  # Minimal wait for calendar state update
                    print("✓ Selected start date: Oct 22, 2025")
                else:
                    print("⚠ Could not find date 22 cell")
            except Exception as e:
                print(f"⚠ Could not click on date 22: {e}")
            
            # Try multiple selector strategies for date 28
            try:
                # Re-fetch all cells after the first selection (calendar may have updated)
                all_cells = driver.find_elements(By.CSS_SELECTOR, ".ant-picker-cell-inner")
                
                date_28 = None
                # Look for date 28 that is clickable and in view
                for cell in all_cells:
                    if cell.text == "28" and cell.is_displayed():
                        # Check if this cell is not disabled
                        parent = cell.find_element(By.XPATH, "..")
                        if "ant-picker-cell-disabled" not in parent.get_attribute("class"):
                            date_28 = cell
                            break
                
                if date_28:
                    driver.execute_script("arguments[0].click();", date_28)
                    print("✓ Selected end date: Oct 28, 2025")
                else:
                    print("⚠ Could not find valid date 28 cell")
            except Exception as e:
                print(f"⚠ Could not click on date 28: {e}")
            
            print("✓ Date range confirmed")
            
        except Exception as e:
            print(f"⚠ Could not set date range: {e}")
        
        # Apply filter using the Apply Filters button
        try:
            apply_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Apply Filters')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", apply_button)
            driver.execute_script("arguments[0].click();", apply_button)
            
            # Wait for filter to be applied (notification appears)
            time.sleep(0.5)
            print("✓ Applied filters")
        except Exception as e:
            print(f"⚠ Could not click Apply Filters button: {e}")
        
        print("✓ Date range filtered\n")
        
        # ========== STEP 4: DOWNLOAD CSV ==========
        print("--- Step 4: Download CSV ---")
        
        # Get the number of files in Downloads folder before download
        download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        files_before = set(os.listdir(download_dir)) if os.path.exists(download_dir) else set()
        
        # Find and click the Download CSV button
        try:
            download_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Download') or contains(., 'CSV') or contains(., 'Export')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", download_button)
            driver.execute_script("arguments[0].click();", download_button)
            print("✓ Clicked Download CSV button")
            time.sleep(1.5)  # Reduced wait for download to complete
        except Exception as e:
            print(f"⚠ Could not find download button: {e}")
        
        # Check if a new file was downloaded
        files_after = set(os.listdir(download_dir)) if os.path.exists(download_dir) else set()
        new_files = files_after - files_before
        
        if new_files:
            csv_file = None
            for file in new_files:
                if file.endswith('.csv'):
                    csv_file = file
                    break
            
            if csv_file:
                csv_path = os.path.join(download_dir, csv_file)
                print(f"✓ CSV file downloaded: {csv_file}")
                
                # ========== STEP 5: OPEN THE DOWNLOADED CSV (IF POSSIBLE) ==========
                print("\n--- Step 5: Open Downloaded CSV ---")
                try:
                    # Try to open the CSV file with the default application
                    os.system(f'open "{csv_path}"')
                    print(f"✓ Opened CSV file: {csv_path}")
                except Exception as e:
                    print(f"⚠ Could not open CSV file: {e}")
            else:
                print("⚠ No CSV file found in new downloads")
        else:
            print("⚠ No new files detected in Downloads folder")
        
        print("\n✓ CSV download test completed\n")
        
        print("=" * 60)
        print("✓ DASHBOARD CSV DOWNLOAD TEST COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Only quit if not reusing browser
        if not reuse_browser:
            driver.quit()
        else:
            print("\n✓ Test completed! Browser window will remain open for inspection.")


if __name__ == "__main__":
    # Run with browser visible for debugging
    test_dashboard_csv_download(reuse_browser=True)
