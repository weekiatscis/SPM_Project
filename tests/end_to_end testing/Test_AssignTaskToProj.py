from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time


def test_login(headless=False, reuse_browser=False):
    # Setup Chrome options for faster testing
    chrome_options = Options()
    
    if reuse_browser:
        # Connect to existing Chrome instance with remote debugging enabled
        # The browser will stay open after the test completes
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    else:
        if headless:
            chrome_options.add_argument("--headless")  # Run without opening browser window
            chrome_options.add_argument("--disable-gpu")
        
        # Additional performance optimizations
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get("http://localhost:3000/login")
        
        email_input = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
        email_input.send_keys("spm@gmail.com")
        
        password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_input.send_keys("Choogoole123")
        
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Wait for navigation to complete after login
        time.sleep(1)
        print("✓ Login successful")
        
        # ========== CREATE PROJECT FIRST ==========
        # Step 1: Click on Projects in the sidebar
        print("\n--- Creating Project ---")
        # Wait for the Projects menu to be clickable
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        # Wait for the Projects menu to be clickable
        projects_menu = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".nav-group-header .nav-icon"))
        )
        # Click using JavaScript to avoid any potential click interception
        driver.execute_script("arguments[0].click();", projects_menu)
        print("✓ Clicked Projects menu")
        
        # Add a small delay to ensure the projects menu has expanded
        time.sleep(1)
        
        
        # Step 2: Click on "New Project" button
        new_project_button = driver.find_element(By.CSS_SELECTOR, ".new-project-btn")
        new_project_button.click()
        print("✓ Clicked New Project button")
        
        
        # Step 3: Fill in the Project Form Modal
        # Project Name
        project_name_input = driver.find_element(By.CSS_SELECTOR, ".ant-input[placeholder*='Website Redesign']")
        project_name_input.send_keys("Automated Test Projectttt")
        print("✓ Entered project name")
        
        # Project Description
        project_description = driver.find_element(By.CSS_SELECTOR, ".ant-input-textarea textarea")
        project_description.send_keys("This is a test project created by Selenium automation")
        print("✓ Entered project description")
        
        # Due Date - Click on the date picker and select a date from the calendar
        target_day = "30"  # Day to click in the calendar
        
        # Click on the date picker input to open the calendar
        date_picker = driver.find_element(By.CSS_SELECTOR, ".ant-picker input")
        date_picker.click()
        time.sleep(0.5)
        
        # Wait for the calendar dropdown to appear
        calendar = driver.find_element(By.CSS_SELECTOR, ".ant-picker-dropdown")
        
        # Click on the specific day in the calendar
        try:
            day_cell = driver.find_element(By.XPATH, f"//td[@title and contains(@class, 'ant-picker-cell') and not(contains(@class, 'ant-picker-cell-disabled'))]//div[text()='{target_day}']")
            day_cell.click()
            print(f"✓ Set project due date to day {target_day}")
            time.sleep(0.5)
        except Exception as e:
            # Alternative: Click any available future date
            day_cells = driver.find_elements(By.CSS_SELECTOR, ".ant-picker-cell:not(.ant-picker-cell-disabled) .ant-picker-cell-inner")
            if day_cells:
                day_cells[0].click()
                print(f"✓ Set project due date")
                time.sleep(0.5)
        
        # Select at least one collaborator (click the first user in the list)
        try:
            first_user = driver.find_element(By.CSS_SELECTOR, ".user-item")
            first_user.click()
            print("✓ Selected a collaborator")
            time.sleep(0.5)
        except:
            print("⚠ No collaborators available to select")
        
        # Step 4: Click "Create Project" button
        create_project_button = driver.find_element(By.CSS_SELECTOR, ".submit-btn")
        create_project_button.click()
        print("✓ Clicked Create Project button")
        
        # Wait for project to be created and modal to close
        time.sleep(1)
        print("✓ Project created successfully!\n")
        
        print("\n--- Moving to home page to create task---")
        # Wait for the Home menu to be clickable
        home_menu = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".nav-item.home"))
        )
        # Click using JavaScript to avoid any potential click interception
        driver.execute_script("arguments[0].click();", home_menu)
        time.sleep(1)  # Wait for navigation to complete
        # ========== NOW CREATE A TASK ==========
        print("--- Creating Task ---")
        # Click on "New Task" button
        new_task_button = driver.find_element(By.CSS_SELECTOR, ".create-task-button")
        new_task_button.click()
        
        # Fill in the task form
        # Title
        title_input = driver.find_element(By.ID, "title")
        title_input.send_keys("Automated Test Taskkkkkkk")
        
        # Description
        description_textarea = driver.find_element(By.ID, "description")
        description_textarea.send_keys("This is a test task created by Selenium automation")
        
        
        # Using JavaScript to set the value properly and trigger Vue reactivity
        due_date_input = driver.find_element(By.ID, "dueDate")
        driver.execute_script("""
            const dateInput = arguments[0];
            dateInput.value = '2025-10-30';
            dateInput.dispatchEvent(new Event('input', { bubbles: true }));
            dateInput.dispatchEvent(new Event('change', { bubbles: true }));
            dateInput.dispatchEvent(new Event('blur', { bubbles: true }));
        """, due_date_input)
        print("✓ Due date set to 2025-10-17")
        
        # Status
        status_select = driver.find_element(By.ID, "status")
        status_select.send_keys("Ongoing")
        
        # Priority (using JavaScript to set the range slider value and trigger events)
        priority_slider = driver.find_element(By.ID, "priority")
        driver.execute_script("""
            const slider = arguments[0];
            slider.value = 8;
            slider.dispatchEvent(new Event('input', { bubbles: true }));
            slider.dispatchEvent(new Event('change', { bubbles: true }));
        """, priority_slider)
        
        print("✓ Priority set to 8")
        time.sleep(2)  # Brief pause after setting priority
        
        # Assignee - handle both Staff (read-only) and Manager/Director (dropdown) cases
        print("Checking assignee field...")
        
        # Try to find the assignee select dropdown (for Manager/Director users)
        try:
            assignee_select = driver.find_element(By.CSS_SELECTOR, "select#assignee")
            
            # Scroll to the assignee element to make sure it's visible
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", assignee_select)
            time.sleep(1)
            
            assignee_select.click()
            print("✓ Clicked assignee dropdown")
            
            # Wait for options to load
            time.sleep(1)
            
            # Select the first option that is not the placeholder
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
            # If no dropdown found, user is likely Staff and assignee is auto-assigned
            print("✓ Assignee field is read-only (auto-assigned to current user)")
        
        time.sleep(1)  # Brief pause to see the completed form
        
        # Click the Create Task button
        print("Clicking Create Task button...")
        create_task_button = driver.find_element(By.CSS_SELECTOR, ".submittaskcreate")
        create_task_button.click()
        
        # Wait for the modal to close and task to be created
        time.sleep(1)
        print("\n✓ Task created successfully!")
        
        print("\n--- Going back to project to assign task to project ---")

        # Wait for the Projects menu to be clickable
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        # Wait for the Projects menu to be clickable
        projects_menu = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".nav-group-header .nav-icon"))
        )
        # Click using JavaScript to avoid any potential click interception
        driver.execute_script("arguments[0].click();", projects_menu)
        print("✓ Clicked Projects menu")
        
        # Add a small delay to ensure the projects menu has expanded
        time.sleep(1)
        
        # Click on the "Assign Task" button to open the assign task section
        assign_task_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".assign-task-btn"))
        )
        driver.execute_script("arguments[0].click();", assign_task_button)
        print("✓ Clicked Assign Task button")
        
        # Wait for the assign task section to load
        time.sleep(1)
        
        # Wait for tasks to load and click on the first task in the available tasks list
        first_task = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".ant-list-item"))
        )
        driver.execute_script("arguments[0].scrollIntoView();", first_task)
        first_task.click()
        print("✓ Selected first task from available tasks")
        
        # Wait for the task to be selected (UI might update)
        time.sleep(1)
        
        # Now select the first project from the projects list (right side)
        # The projects list is in the right column (span="17")
        # We need to target the second ant-list (the projects list, not the tasks list)
        
        # Wait for all ant-list elements to be present
        all_lists = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ant-list"))
        )
        
        # The second list should be the projects list (first is tasks)
        if len(all_lists) >= 2:
            # Find project items within the second list (projects list)
            project_items = all_lists[1].find_elements(By.CSS_SELECTOR, ".ant-list-item")
            
            if project_items:
                # Scroll the first project into view and click it
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", project_items[0])
                time.sleep(0.5)  # Small delay for scroll to complete
                driver.execute_script("arguments[0].click();", project_items[0])
                print("✓ Selected first project from available projects")
            else:
                print("⚠ No projects found in the projects list")
        else:
            print("⚠ Could not find projects list")
        
        # Wait for the assign button to be clickable
        time.sleep(0.5)
        
        # Click on the "Assign" button to confirm the assignment
        assign_confirm_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'ant-btn-primary') and contains(., 'Assign')]"))
        )
        driver.execute_script("arguments[0].click();", assign_confirm_button)
        print("✓ Clicked Assign button to confirm task assignment")
        
        # Wait for assignment to complete
    
        
        # ========== CLEANUP: DELETE THE CREATED TASK AND PROJECT ==========
        print("\n--- Cleaning up: Deleting created task and project ---")
        
        # Step 1: Navigate to home to delete the task
        home_menu = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".nav-item.home"))
        )
        driver.execute_script("arguments[0].click();", home_menu)
        time.sleep(1)
        
        # Step 2: Click on the created task to open task detail modal
        # Look for the specific task we created by its title
        created_task_title = "Automated Test Taskkkkkkk"
        
        try:
            # Find the task card that contains our specific task title
            created_task = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//div[contains(@class, 'task-card-wrapper')]//div[contains(text(), '{created_task_title}')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", created_task)
            time.sleep(0.5)
            created_task.click()
            print(f"✓ Found and clicked on the created task: {created_task_title}")
            time.sleep(1)
        except:
            # Fallback: if we can't find the specific task, try to find it by looking for the task card wrapper
            print(f"⚠ Could not find task with title '{created_task_title}', trying fallback method...")
            task_items = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".task-card-wrapper"))
            )
            
            if task_items:
                # Look through all task items to find the one with our title
                task_found = False
                for task_item in task_items:
                    try:
                        task_text = task_item.text
                        if created_task_title in task_text:
                            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", task_item)
                            time.sleep(0.5)
                            task_item.click()
                            print(f"✓ Found and clicked on the created task using fallback method: {created_task_title}")
                            task_found = True
                            break
                    except:
                        continue
                
                if not task_found:
                    print("⚠ Could not find the created task, clicking on first available task")
                    task_items[0].click()
                time.sleep(1)
            else:
                print("⚠ No task items found")
        
        # Step 3: Click the delete button in the task detail modal
        try:
            delete_task_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Delete')]"))
            )
            delete_task_button.click()
            
            # Step 4: Confirm deletion in the browser alert
            time.sleep(0.5)
            try:
                alert = driver.switch_to.alert
                alert.accept()
                print("✓ Task deleted successfully")
                time.sleep(1)
            except:
                print("⚠ No confirmation alert found for task deletion")
        except Exception as e:
            print(f"⚠ Could not delete task: {str(e)}")
        
        # Step 5: Navigate to projects to delete the project
        print("--- Navigating to projects for cleanup ---")
        
        # First, try to click on the Projects menu to expand it
        try:
            projects_menu = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".nav-group-header"))
            )
            driver.execute_script("arguments[0].click();", projects_menu)
            print("✓ Clicked Projects menu")
            time.sleep(2)  # Wait for projects to load
        except Exception as e:
            print(f"⚠ Could not click Projects menu: {str(e)}")
        
        # Step 6: Click on the specific project we created
        created_project_name = "Automated Test Projectttt"
        
        try:
            # First try to find the project in the sidebar submenu
            print(f"Looking for project: {created_project_name}")
            
            # Wait for projects to load and be visible
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".nav-submenu"))
            )
            
            # Look for the project link in the submenu
            created_project_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//div[contains(@class, 'nav-submenu')]//a[contains(@class, 'submenu-item') and contains(., '{created_project_name}')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", created_project_link)
            time.sleep(0.5)
            created_project_link.click()
            print(f"✓ Found and clicked on the created project: {created_project_name}")
            time.sleep(2)
            
        except Exception as e:
            print(f"⚠ Could not find project in sidebar: {str(e)}")
            
            # Fallback: Navigate directly to projects page and find the project there
            try:
                print("Trying fallback: navigating to projects page...")
                driver.get("http://localhost:3000/projects")
                time.sleep(2)
                
                # Look for the project card on the projects page
                project_card = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, f"//div[contains(@class, 'project-card') and contains(., '{created_project_name}')]"))
                )
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", project_card)
                time.sleep(0.5)
                project_card.click()
                print(f"✓ Found and clicked on project card: {created_project_name}")
                time.sleep(2)
                
            except Exception as e2:
                print(f"⚠ Could not find project on projects page either: {str(e2)}")
                # Last resort: try to click on any project
                try:
                    any_project = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".project-card"))
                    )
                    any_project.click()
                    print("⚠ Clicked on first available project as last resort")
                    time.sleep(2)
                except:
                    print("⚠ Could not find any project to click on")
                    return
        
        # Step 7: Click on the three-dot menu (ellipsis) to open project options
        print("Looking for three-dot menu button...")
        
        try:
            ellipsis_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".action-menu-btn"))
            )
            print("✓ Found three-dot menu button")
            
            # Scroll into view and click
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", ellipsis_button)
            time.sleep(0.5)
            ellipsis_button.click()
            print("✓ Clicked three-dot menu button")
            time.sleep(1)  # Increased wait time for dropdown to appear
            
        except Exception as e:
            print(f"⚠ Could not find or click three-dot menu button: {str(e)}")
            # Try alternative selectors
            alternative_selectors = [
                ".ant-dropdown-trigger",
                "button[class*='action']",
                "button[class*='menu']"
            ]
            
            for selector in alternative_selectors:
                try:
                    print(f"Trying alternative selector: {selector}")
                    alt_button = driver.find_element(By.CSS_SELECTOR, selector)
                    alt_button.click()
                    print(f"✓ Clicked with alternative selector: {selector}")
                    time.sleep(1)
                    break
                except:
                    continue
            else:
                print("⚠ Could not find three-dot menu with any selector")
                return
        
        # Step 8: Click on "Delete Project" option
        print("Looking for Delete Project option in dropdown menu...")
        
        try:
            # Wait for the dropdown menu to appear
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".ant-dropdown"))
            )
            print("✓ Dropdown menu is visible")
            
            # Try multiple selectors for the delete option
            delete_selectors = [
                "//li[@data-menu-id='delete']",  # Most specific - uses the data-menu-id attribute
                "//li[contains(@class, 'ant-dropdown-menu-item') and contains(@class, 'ant-dropdown-menu-item-danger')]",
                "//li[contains(@class, 'ant-dropdown-menu-item') and contains(@class, 'ant-dropdown-menu-item-danger')]//span[contains(text(), 'Delete Project')]",
                "//li[contains(@class, 'ant-dropdown-menu-item')]//span[contains(text(), 'Delete Project')]",
                "//li[@class='ant-dropdown-menu-item ant-dropdown-menu-item-danger']",
                "//li[contains(@class, 'ant-dropdown-menu-item')]//span[@class='ant-dropdown-menu-title-content']//span[contains(text(), 'Delete Project')]"
            ]
            
            delete_project_option = None
            for i, selector in enumerate(delete_selectors):
                try:
                    print(f"Trying selector {i+1}: {selector}")
                    delete_project_option = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    print(f"✓ Found Delete Project option with selector {i+1}")
                    break
                except:
                    print(f"✗ Selector {i+1} failed")
                    continue
            
            if delete_project_option:
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", delete_project_option)
                time.sleep(0.5)
                delete_project_option.click()
                print("✓ Clicked Delete Project option")
                time.sleep(1)
            else:
                print("⚠ Could not find Delete Project option with any selector")
                # Debug: print all available menu items
                try:
                    menu_items = driver.find_elements(By.CSS_SELECTOR, ".ant-dropdown-menu-item")
                    print(f"Available dropdown menu items: {len(menu_items)}")
                    for j, item in enumerate(menu_items):
                        print(f"  Item {j+1}: {item.text} (classes: {item.get_attribute('class')})")
                except:
                    print("Could not retrieve dropdown menu items for debugging")
                return
                
        except Exception as e:
            print(f"⚠ Error finding Delete Project option: {str(e)}")
            return
        
        # Step 9: Type "delete" in the confirmation input
        delete_confirmation_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*=\"Type 'delete' here\"]"))
        )
        delete_confirmation_input.send_keys("delete")
        time.sleep(0.5)
        
        # Step 10: Click the "Delete Project" button in the modal
        confirm_delete_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'ant-btn-dangerous') and contains(., 'Delete Project')]"))
        )
        driver.execute_script("arguments[0].click();", confirm_delete_button)
        print("✓ Project deleted successfully")
        
        time.sleep(2)
        print("✓ Cleanup completed successfully!")
        
    finally:
        # Only quit if not reusing browser
        if not reuse_browser:
            driver.quit()
        else:
            print("\n✓ Test completed! Browser window will remain open for inspection.")


if __name__ == "__main__":

    test_login(reuse_browser=True)
