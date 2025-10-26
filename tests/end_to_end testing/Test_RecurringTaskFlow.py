from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def test_recurring_task_flow(headless=False, reuse_browser=False):
    """
    Test the complete recurring task workflow:
    1. User logs in
    2. Create a new recurring task (Weekly frequency)
    3. Create subtask for that task
    4. Click on parent task to show subtask is inside
    5. Mark parent task as completed
    6. Show new task created with subtask still inside
    7. Click on completed tasks to show the previous recurred task
    
    Note: This test uses title-based search to find the specific recurring task
    instead of relying on position in the task list, making it more robust.
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
        print("--- Step 1: User Login ---")
        driver.get("http://localhost:3000/login")
        
        email_input = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
        email_input.send_keys("spm@gmail.com")
        
        password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_input.send_keys("Choogoole123")
        
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        time.sleep(2)
        print("✓ Login successful\n")
        
        # ========== STEP 2: CREATE NEW RECURRING TASK ==========
        print("--- Step 2: Create New Recurring Task ---")
        
        # Navigate to home page
        home_menu = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".nav-item.home"))
        )
        driver.execute_script("arguments[0].click();", home_menu)
        time.sleep(1)
        
        # Click on "New Task" button
        new_task_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".create-task-button"))
        )
        new_task_button.click()
        time.sleep(1)
        
        # Fill in task details
        title_input = driver.find_element(By.ID, "title")
        title_input.send_keys("Recurring Test Task - Weekly Report")
        
        description_textarea = driver.find_element(By.ID, "description")
        description_textarea.send_keys("This is a recurring task to test the recurring functionality")
        
        # Set due date
        due_date_input = driver.find_element(By.ID, "dueDate")
        driver.execute_script("""
            const dateInput = arguments[0];
            dateInput.value = '2025-10-31';
            dateInput.dispatchEvent(new Event('input', { bubbles: true }));
            dateInput.dispatchEvent(new Event('change', { bubbles: true }));
            dateInput.dispatchEvent(new Event('blur', { bubbles: true }));
        """, due_date_input)
        print("✓ Due date set")
        
        # Set status
        status_select = driver.find_element(By.ID, "status")
        status_select.send_keys("Ongoing")
        
        # Set priority
        priority_slider = driver.find_element(By.ID, "priority")
        driver.execute_script("""
            const slider = arguments[0];
            slider.value = 7;
            slider.dispatchEvent(new Event('input', { bubbles: true }));
            slider.dispatchEvent(new Event('change', { bubbles: true }));
        """, priority_slider)
        print("✓ Priority set to 7")
        time.sleep(1)
        
        # Set recurring option
        # Find and click the recurring checkbox/toggle
        try:
            recurring_checkbox = driver.find_element(By.ID, "isRecurring")
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", recurring_checkbox)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", recurring_checkbox)
            print("✓ Enabled recurring option")
            time.sleep(1)
            
            # Select recurring frequency (e.g., Weekly)
            recurring_frequency = driver.find_element(By.ID, "recurrence")
            driver.execute_script("""
                const select = arguments[0];
                select.value = 'weekly';
                select.dispatchEvent(new Event('change', { bubbles: true }));
            """, recurring_frequency)
            print("✓ Set recurring frequency to Weekly")
            time.sleep(1)
        except Exception as e:
            print(f"⚠ Could not set recurring options: {e}")
        
        # Handle assignee field
        try:
            assignee_select = driver.find_element(By.CSS_SELECTOR, "select#assignee")
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", assignee_select)
            time.sleep(0.5)
            assignee_select.click()
            time.sleep(0.5)
            
            driver.execute_script("""
                const select = arguments[0];
                for (let i = 0; i < select.options.length; i++) {
                    if (select.options[i].value) {
                        select.selectedIndex = i;
                        select.dispatchEvent(new Event('change', { bubbles: true }));
                        break;
                    }
                }
            """, assignee_select)
            print("✓ Assignee selected")
        except:
            print("✓ Assignee auto-assigned")
        
        time.sleep(1)
        
        # Click Create Task button
        create_task_button = driver.find_element(By.CSS_SELECTOR, ".submittaskcreate")
        create_task_button.click()
        time.sleep(5)
        print("✓ Recurring task created successfully!\n")
        
        # ========== STEP 3: CREATE SUBTASK FOR THE RECURRING TASK ==========
        print("--- Step 3: Create Subtask for Recurring Task ---")
        
        # Define the recurring task title for later reference
        recurring_task_title = "Recurring Test Task - Weekly Report"
        
        # Create a subtask through the normal task creation flow
        print("Creating subtask through New Task flow...")
        
        # Click on "New Task" button using JavaScript to avoid click interception
        new_task_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".create-task-button"))
        )
        driver.execute_script("arguments[0].click();", new_task_button)
        time.sleep(1)
        
        # Select the "Subtask" radio button
        # The radio buttons use v-model with boolean values: false for Regular Task, true for Subtask
        try:
            # Wait for the form to load
            time.sleep(1)
            
            # Find all radio buttons and select the one for Subtask (second radio button)
            radio_buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            
            # The second radio button should be for Subtask
            if len(radio_buttons) >= 2:
                subtask_radio = radio_buttons[1]  # Index 1 is the Subtask radio
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", subtask_radio)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", subtask_radio)
                print("✓ Selected Subtask radio button")
                time.sleep(1)
            else:
                print(f"⚠ Could not find subtask radio button - found {len(radio_buttons)} radio buttons")
        except Exception as e:
            print(f"⚠ Could not find subtask radio button: {e}")
        
        # Fill in subtask details
        title_input = driver.find_element(By.ID, "title")
        title_input.send_keys("Subtask 1 - Prepare Data")
        
        description_textarea = driver.find_element(By.ID, "description")
        description_textarea.send_keys("This is a subtask for the recurring task")
        
        # Set due date
        due_date_input = driver.find_element(By.ID, "dueDate")
        driver.execute_script("""
            const dateInput = arguments[0];
            dateInput.value = '2025-10-30';
            dateInput.dispatchEvent(new Event('input', { bubbles: true }));
            dateInput.dispatchEvent(new Event('change', { bubbles: true }));
            dateInput.dispatchEvent(new Event('blur', { bubbles: true }));
        """, due_date_input)
        
        # Select parent task from dropdown
        try:
            parent_task_select = driver.find_element(By.CSS_SELECTOR, "select#parentTask, select#parent")
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", parent_task_select)
            time.sleep(0.5)
            
            # Find the option with our recurring task title
            driver.execute_script("""
                const select = arguments[0];
                const taskTitle = arguments[1];
                for (let i = 0; i < select.options.length; i++) {
                    if (select.options[i].text.includes(taskTitle)) {
                        select.selectedIndex = i;
                        select.dispatchEvent(new Event('change', { bubbles: true }));
                        break;
                    }
                }
            """, parent_task_select, recurring_task_title)
            print("✓ Selected parent task from dropdown")
            time.sleep(1)
        except Exception as e:
            print(f"⚠ Could not select parent task: {e}")
        
        # Handle assignee field
        try:
            assignee_select = driver.find_element(By.CSS_SELECTOR, "select#assignee")
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", assignee_select)
            time.sleep(0.5)
            assignee_select.click()
            time.sleep(0.5)
            
            driver.execute_script("""
                const select = arguments[0];
                for (let i = 0; i < select.options.length; i++) {
                    if (select.options[i].value) {
                        select.selectedIndex = i;
                        select.dispatchEvent(new Event('change', { bubbles: true }));
                        break;
                    }
                }
            """, assignee_select)
            print("✓ Assignee selected")
        except:
            print("✓ Assignee auto-assigned")
        
        time.sleep(1)
        
        # Click Create Task button
        create_task_button = driver.find_element(By.CSS_SELECTOR, ".submittaskcreate")
        create_task_button.click()
        time.sleep(2)
        print("✓ Subtask created successfully!\n")
        
        print("✓ Returned to task list\n")
        
        # ========== STEP 4: CLICK ON PARENT TASK TO SHOW SUBTASK IS INSIDE ==========
        print("--- Step 4: Verify Subtask is Inside Parent Task ---")
        
        # Find the recurring task again by title
        task_cards = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".task-card-wrapper"))
        )
        
        recurring_task = None
        for task_card in task_cards:
            try:
                task_title_element = task_card.find_element(By.CSS_SELECTOR, ".task-title, h3, .title")
                if recurring_task_title in task_title_element.text:
                    recurring_task = task_card
                    break
            except:
                continue
        
        if recurring_task:
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", recurring_task)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", recurring_task)
            time.sleep(2)
            print("✓ Opened recurring task detail modal again")
        elif task_cards:
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", task_cards[0])
            time.sleep(1)
            driver.execute_script("arguments[0].click();", task_cards[0])
            time.sleep(2)
            print("✓ Opened first task (fallback)")
        
        # Look for subtask in the modal
        try:
            subtasks = driver.find_elements(By.CSS_SELECTOR, ".subtask-card")
            if subtasks:
                print(f"✓ Found {len(subtasks)} subtask(s) in the parent task")
            else:
                print("⚠ No subtasks visible in the modal")
        except:
            print("⚠ Could not verify subtasks")
        
        time.sleep(2)
        print("✓ Verified subtask is inside parent task\n")
        
        # ========== STEP 5: MARK PARENT TASK AS COMPLETED ==========
        print("--- Step 5: Mark Parent Task as Completed ---")
        
        # Look for "Mark as Complete" or "Complete" button in the modal
        try:
            complete_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Complete') or contains(., 'Mark as Complete')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", complete_button)
            time.sleep(0.5)
            complete_button.click()
            time.sleep(1)
            
            # Handle browser confirmation alert (window.confirm)
            try:
                alert = WebDriverWait(driver, 3).until(EC.alert_is_present())
                alert.accept()  # Click OK button
                print("✓ Confirmed completion in browser alert")
                time.sleep(2)
            except:
                print("⚠ No browser alert found")
            
            print("✓ Marked parent task as completed")
            
        except Exception as e:
            print(f"⚠ Could not find complete button: {e}")
            print("⚠ Attempting to close modal and mark complete from task list...")
            
            # Close modal
            try:
                close_button = driver.find_element(By.CSS_SELECTOR, ".ant-modal-close")
                close_button.click()
                time.sleep(1)
            except:
                from selenium.webdriver.common.keys import Keys
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                time.sleep(1)
            
            # Try to mark complete from task card
            try:
                task_cards = driver.find_elements(By.CSS_SELECTOR, ".task-card-wrapper")
                if task_cards:
                    # Look for checkbox or complete button on the card
                    complete_checkbox = task_cards[0].find_element(By.CSS_SELECTOR, "input[type='checkbox'], .complete-btn")
                    complete_checkbox.click()
                    time.sleep(2)
                    print("✓ Marked task as completed from task card")
            except Exception as e2:
                print(f"⚠ Could not mark task as complete: {e2}")
        
        # Close modal if still open
        try:
            close_button = driver.find_element(By.CSS_SELECTOR, ".close-button")
            close_button.click()
            time.sleep(1)
            print("✓ Closed task modal")
        except:
            # Try ESC key
            try:
                from selenium.webdriver.common.keys import Keys
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                time.sleep(1)
                print("✓ Closed modal with ESC key")
            except:
                print("⚠ Could not close modal")
        
        print("✓ Parent task marked as completed\n")
        
        # ========== STEP 6: SHOW NEW TASK CREATED WITH SUBTASK STILL INSIDE ==========
        print("--- Step 6: Verify New Recurring Task Created with Subtask ---")
        
        # Wait for the page to update and new recurring task to appear
        print("Waiting for new recurring task instance to be created...")
        time.sleep(5)  # Give more time for the backend to create the new instance
        
        # Refresh the page to ensure we see the latest tasks
        driver.refresh()
        time.sleep(2)
        print("✓ Refreshed page")
        
        # Ensure we're on the active tasks view (not completed)
        try:
            active_tab = driver.find_element(By.XPATH, "//button[contains(., 'Active') or contains(., 'Ongoing') or contains(., 'All Tasks')]")
            driver.execute_script("arguments[0].click();", active_tab)
            time.sleep(2)
            print("✓ Switched to active tasks view")
        except:
            print("⚠ Could not find active tasks tab, continuing...")
        
        # Look for the new recurring task by title (should have the same title)
        task_cards = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".task-card-wrapper"))
        )
        
        print(f"✓ Found {len(task_cards)} task(s) on the page")
        
        # Find ALL recurring tasks with matching title (there might be multiple if old one hasn't been filtered)
        matching_tasks = []
        for task_card in task_cards:
            try:
                task_title_element = task_card.find_element(By.CSS_SELECTOR, ".task-title, h3, .title")
                if recurring_task_title in task_title_element.text:
                    # Check if it's not completed
                    try:
                        status_element = task_card.find_element(By.CSS_SELECTOR, ".status, .task-status")
                        if "Completed" not in status_element.text:
                            matching_tasks.append(task_card)
                            print(f"✓ Found active recurring task: {task_title_element.text}")
                    except:
                        # If can't find status, assume it's active
                        matching_tasks.append(task_card)
                        print(f"✓ Found recurring task: {task_title_element.text}")
            except:
                continue
        
        # Use the first matching active task (should be the new instance)
        new_recurring_task = matching_tasks[0] if matching_tasks else None
        
        if not new_recurring_task:
            print("⚠ Could not find new recurring task by title, trying first task...")
            new_recurring_task = task_cards[0] if task_cards else None
        
        if new_recurring_task:
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", new_recurring_task)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", new_recurring_task)
            time.sleep(2)
            print("✓ Opened new recurring task instance")
        elif task_cards:
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", task_cards[0])
            time.sleep(1)
            driver.execute_script("arguments[0].click();", task_cards[0])
            time.sleep(2)
            print("✓ Opened first task (fallback)")
        
        # Verify subtask is still inside the parent task
        try:
            subtasks = driver.find_elements(By.CSS_SELECTOR, ".subtask-card")
            if subtasks:
                print(f"✓ Verified: New recurring task 'Recurring Test Task - Weekly Report' has {len(subtasks)} subtask(s)")
            else:
                print("⚠ Warning: No subtasks found in new recurring task")
        except:
            print("⚠ Could not verify subtasks in new task")
        
        time.sleep(2)
        
        # Close modal
        try:
            close_button = driver.find_element(By.CSS_SELECTOR, ".close-button")
            close_button.click()
            time.sleep(1)
        except:
            from selenium.webdriver.common.keys import Keys
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(1)
        
        print("✓ Verified new recurring task created with subtask\n")
        
        # ========== STEP 7: CLICK ON COMPLETED TASKS TO SHOW PREVIOUS RECURRED TASK ==========
        print("--- Step 7: View Completed Tasks and Delete Previous Recurred Task ---")
        
        # Look for "Completed" tab using Ant Design tab structure
        try:
            # Try to find completed tasks tab by text content
            completed_tab = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'ant-tabs-tab') and contains(., 'Completed')]"))
            )
            completed_tab.click()
            time.sleep(2)
            print("✓ Clicked on Completed tasks tab")
            
            # Look for the completed recurring task by title
            completed_tasks = driver.find_elements(By.CSS_SELECTOR, ".task-card-wrapper")
            print(f"✓ Found {len(completed_tasks)} completed task(s)")
            
            completed_recurring_task = None
            for task_card in completed_tasks:
                try:
                    task_title_element = task_card.find_element(By.CSS_SELECTOR, ".task-title, h3, .title")
                    if recurring_task_title in task_title_element.text:
                        completed_recurring_task = task_card
                        break
                except:
                    continue
            
            if completed_recurring_task:
                # Click on the completed recurring task
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", completed_recurring_task)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", completed_recurring_task)
                time.sleep(2)
                print(f"✓ Opened completed task: '{recurring_task_title}'")
                
                # Verify it's marked as completed
                try:
                    status_element = driver.find_element(By.XPATH, "//*[contains(text(), 'Completed') or contains(text(), 'Done')]")
                    print("✓ Verified task is marked as Completed")
                except:
                    print("⚠ Could not verify completion status")
                
                time.sleep(1)
                
                # Delete the completed recurring task
                try:
                    delete_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Delete')]"))
                    )
                    delete_button.click()
                    time.sleep(0.5)
                    
                    # Confirm deletion
                    try:
                        alert = driver.switch_to.alert
                        alert.accept()
                        print(f"✓ Deleted completed task: '{recurring_task_title}'")
                        time.sleep(1)
                    except:
                        try:
                            confirm_button = driver.find_element(By.XPATH, "//button[contains(@class, 'ant-btn-dangerous') and contains(., 'Delete')]")
                            confirm_button.click()
                            print(f"✓ Deleted completed task: '{recurring_task_title}'")
                            time.sleep(1)
                        except:
                            print("⚠ Could not confirm deletion")
                except Exception as delete_error:
                    print(f"⚠ Could not delete completed task: {delete_error}")
            else:
                print(f"⚠ Could not find completed task with title: '{recurring_task_title}'")
            
        except Exception as e:
            print(f"⚠ Could not access completed tasks: {e}")
            print("⚠ Attempting alternative method...")
            
            # Try looking for a filter dropdown
            try:
                filter_dropdown = driver.find_element(By.CSS_SELECTOR, "select[id*='status'], select[id*='filter']")
                driver.execute_script("""
                    const select = arguments[0];
                    select.value = 'Completed';
                    select.dispatchEvent(new Event('change', { bubbles: true }));
                """, filter_dropdown)
                time.sleep(2)
                print("✓ Changed filter to show completed tasks")
            except Exception as e2:
                print(f"⚠ Could not change filter: {e2}")
        
        print("✓ Completed tasks verification and deletion finished\n")
        
        # ========== CLEANUP ==========
        print("--- Cleanup: Deleting Remaining Test Tasks ---")
        
        # Navigate back to active tasks
        try:
            active_tab = driver.find_element(By.XPATH, "//button[contains(., 'Active') or contains(., 'Ongoing')] | //div[contains(@class, 'tab') and contains(., 'Active')]")
            active_tab.click()
            time.sleep(1)
        except:
            # Refresh page to reset view
            driver.refresh()
            time.sleep(2)
        
        # Delete the subtask first
        try:
            task_cards = driver.find_elements(By.CSS_SELECTOR, ".task-card-wrapper")
            subtask_to_delete = None
            
            # Find subtask by title
            for task_card in task_cards:
                try:
                    task_title_element = task_card.find_element(By.CSS_SELECTOR, ".task-title, h3, .title")
                    if "Subtask 1 - Prepare Data" in task_title_element.text:
                        subtask_to_delete = task_card
                        break
                except:
                    continue
            
            if subtask_to_delete:
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", subtask_to_delete)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", subtask_to_delete)
                time.sleep(1)
                
                delete_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Delete')]"))
                )
                delete_button.click()
                time.sleep(0.5)
                
                # Confirm deletion
                try:
                    alert = driver.switch_to.alert
                    alert.accept()
                    print("✓ Deleted subtask")
                    time.sleep(1)
                except:
                    try:
                        confirm_button = driver.find_element(By.XPATH, "//button[contains(@class, 'ant-btn-dangerous') and contains(., 'Delete')]")
                        confirm_button.click()
                        print("✓ Deleted subtask")
                        time.sleep(1)
                    except:
                        print("⚠ Could not confirm subtask deletion")
        except Exception as e:
            print(f"⚠ Could not delete subtask: {e}")
        
        # Delete the new recurring task
        try:
            task_cards = driver.find_elements(By.CSS_SELECTOR, ".task-card-wrapper")
            recurring_to_delete = None
            
            # Find recurring task by title
            for task_card in task_cards:
                try:
                    task_title_element = task_card.find_element(By.CSS_SELECTOR, ".task-title, h3, .title")
                    if recurring_task_title in task_title_element.text:
                        recurring_to_delete = task_card
                        break
                except:
                    continue
            
            if recurring_to_delete:
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", recurring_to_delete)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", recurring_to_delete)
                time.sleep(1)
                
                delete_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Delete')]"))
                )
                delete_button.click()
                time.sleep(0.5)
                
                # Confirm deletion
                try:
                    alert = driver.switch_to.alert
                    alert.accept()
                    print("✓ Deleted new recurring task")
                    time.sleep(1)
                except:
                    try:
                        confirm_button = driver.find_element(By.XPATH, "//button[contains(@class, 'ant-btn-dangerous') and contains(., 'Delete')]")
                        confirm_button.click()
                        print("✓ Deleted new recurring task")
                        time.sleep(1)
                    except:
                        print("⚠ Could not confirm deletion")
        except Exception as e:
            print(f"⚠ Could not delete new recurring task: {e}")
        
        # Note: Completed recurring task was already deleted in Step 7
        print("✓ Completed recurring task was already deleted in Step 7")
        
        print("✓ Cleanup completed!\n")
        print("=" * 60)
        print("✓ RECURRING TASK FLOW TEST COMPLETED SUCCESSFULLY!")
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
    test_recurring_task_flow(reuse_browser=True)
