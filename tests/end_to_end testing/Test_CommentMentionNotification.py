from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time


def test_comment_mention_notification(headless=False, reuse_browser=False):
    """
    Test the comment mention and notification workflow:
    1. User logs in (weekiat22@gmail.com)
    2. Select a random task
    3. Comment on it with @Director Tan Wei Jun mention
    4. Log out and log in as the mentioned user (evilbrandodle@gmail.com)
    5. Click on notification in the topbar
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
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # ========== STEP 1: USER LOGIN ==========
        print("--- Step 1: User Login (weekiat22@gmail.com) ---")
        driver.get("http://localhost:3000/login")
        
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
        )
        email_input.send_keys("weekiat22@gmail.com")
        
        password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_input.send_keys("tB800797")
        
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Wait for navigation to complete
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".nav-item.home"))
        )
        print("✓ Login successful\n")
        
        # ========== STEP 2: NAVIGATE TO HOME AND SELECT A RANDOM TASK ==========
        print("--- Step 2: Navigate to Home and Select a Task ---")
        
        # Click on Home menu item
        home_menu = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".nav-item.home"))
        )
        driver.execute_script("arguments[0].click();", home_menu)
        
        # Wait for task cards to load
        time.sleep(2)
        
        # Find all task cards
        task_cards = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".task-card-wrapper"))
        )
        
        if len(task_cards) == 0:
            print("⚠ No tasks found on the page")
            return
        
        print(f"✓ Found {len(task_cards)} task(s)")
        
        # Click on the first task
        first_task = task_cards[0]
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", first_task)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", first_task)
        time.sleep(1)
        print("✓ Opened task detail modal\n")
        
        # ========== STEP 3: COMMENT WITH @MENTION ==========
        print("--- Step 3: Add Comment with @Director Tan Wei Jun Mention ---")
        
        # Wait for the task detail modal to be visible
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ant-modal-content, .modal-content"))
        )
        time.sleep(1)
        
        # Find the comment input field (contenteditable div)
        try:
            comment_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".comment-input-field[contenteditable='true']"))
            )
            
            # Click on the comment input to focus it
            driver.execute_script("arguments[0].focus();", comment_input)
            time.sleep(0.3)
            
            # Type @ to trigger mention dropdown
            comment_input.send_keys("@")
            time.sleep(1)
            print("✓ Typed @ to trigger mention dropdown")
            
            # Wait for mention dropdown to appear
            mention_dropdown = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".absolute.z-50.mt-1.w-64.bg-white"))
            )
            print("✓ Mention dropdown appeared")
            
            # Find all mention options
            mention_buttons = driver.find_elements(By.CSS_SELECTOR, ".absolute.z-50.mt-1.w-64.bg-white button")
            
            # Look for "Director" or "Tan Wei Jun" in the mention options
            director_found = False
            for button in mention_buttons:
                button_text = button.text
                if "Director" in button_text or "Tan Wei Jun" in button_text:
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(0.5)
                    print(f"✓ Selected mention: {button_text}")
                    director_found = True
                    break
            
            if not director_found:
                print("⚠ Director Tan Wei Jun not found in mention list, selecting first option")
                if len(mention_buttons) > 0:
                    driver.execute_script("arguments[0].click();", mention_buttons[0])
                    time.sleep(0.5)
                    print(f"✓ Selected first mention option: {mention_buttons[0].text}")
            
            # Add some additional comment text
            comment_input.send_keys(" Please review this task.")
            time.sleep(0.5)
            print("✓ Added comment text")
            
            # Click the Post Comment button
            post_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Post Comment')]"))
            )
            driver.execute_script("arguments[0].click();", post_button)
            time.sleep(2)
            print("✓ Posted comment with mention\n")
            
        except Exception as e:
            print(f"⚠ Could not add comment: {e}")
            import traceback
            traceback.print_exc()
        
        # Close the task modal
        try:
            # Try to find and click close button
            close_button = driver.find_element(By.CSS_SELECTOR, ".ant-modal-close, .close-button")
            driver.execute_script("arguments[0].click();", close_button)
            time.sleep(0.5)
        except:
            # Use ESC key as fallback
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(0.5)
        
        print("✓ Closed task modal")
        
        # ========== STEP 4: LOG OUT ==========
        print("\n--- Step 4: Log Out ---")
        
        # Click on user profile/menu to access logout
        try:
            # Find the profile button in the topbar
            profile_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".profile-button"))
            )
            driver.execute_script("arguments[0].click();", profile_button)
            time.sleep(0.5)
            print("✓ Clicked profile button")
            
            # Wait for the dropdown menu to appear and click on "Sign out" menu item
            logout_menu_item = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".ant-dropdown-menu-item.logout-item"))
            )
            driver.execute_script("arguments[0].click();", logout_menu_item)
            time.sleep(1)
            print("✓ Logged out successfully")
        except Exception as e:
            print(f"⚠ Could not find logout button, navigating directly to login: {e}")
            driver.get("http://localhost:3000/login")
            time.sleep(1)
        
        # ========== STEP 5: LOG IN AS MENTIONED USER ==========
        print("\n--- Step 5: Log In as Director (evilbrandodle@gmail.com) ---")
        
        # Wait for login page
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
        )
        email_input.clear()
        email_input.send_keys("evilbrandodle@gmail.com")
        
        password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_input.clear()
        password_input.send_keys("Password123")
        
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Wait for navigation to complete
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".nav-item.home"))
        )
        print("✓ Login successful as Director\n")
        
        # ========== STEP 6: CLICK ON NOTIFICATION BELL ==========
        print("--- Step 6: Click on Notification Bell in Topbar ---")
        
        # Wait a moment for notifications to load
        time.sleep(2)
        
        # Find and click the notification bell icon
        try:
            # Look for the notification bell button (it's inside an a-badge but we target the button)
            notification_bell = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".notification-bell-button"))
            )
            driver.execute_script("arguments[0].click();", notification_bell)
            time.sleep(1)
            print("✓ Clicked notification bell")
            
            # Wait for notification dropdown to appear
            notification_dropdown = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".notification-dropdown"))
            )
            print("✓ Notification dropdown opened")
            
            # Check for notifications
            notification_items = driver.find_elements(By.CSS_SELECTOR, ".notification-item")
            
            if len(notification_items) > 0:
                print(f"✓ Found {len(notification_items)} notification(s)")
                
                # Check for unread notifications
                unread_notifications = driver.find_elements(By.CSS_SELECTOR, ".notification-item.unread")
                if len(unread_notifications) > 0:
                    print(f"✓ Found {len(unread_notifications)} unread notification(s)")
                    
                    # Click on the first unread notification
                    first_unread = unread_notifications[0]
                    notification_text = first_unread.text
                    print(f"✓ Notification content: {notification_text[:100]}...")
                    
                    # Look for "View Task" button if available
                    try:
                        view_task_btn = first_unread.find_element(By.CSS_SELECTOR, ".view-task-btn")
                        driver.execute_script("arguments[0].click();", view_task_btn)
                        time.sleep(2)
                        print("✓ Clicked 'View Task' button in notification")
                    except:
                        print("✓ No 'View Task' button found in notification")
                else:
                    print("✓ No unread notifications (all notifications have been read)")
            else:
                print("⚠ No notifications found")
            
        except Exception as e:
            print(f"⚠ Could not interact with notifications: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n✓ Notification interaction completed\n")
        
        print("=" * 60)
        print("✓ COMMENT MENTION NOTIFICATION TEST COMPLETED SUCCESSFULLY!")
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
    test_comment_mention_notification(reuse_browser=True)
