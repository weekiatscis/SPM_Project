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
        projects_menu = driver.find_element(By.CSS_SELECTOR, "[data-menu-id='projects']")
        projects_menu.click()
        print("✓ Clicked Projects menu")
        
        
        # Step 2: Click on "New Project" button
        new_project_button = driver.find_element(By.CSS_SELECTOR, ".new-project-btn")
        new_project_button.click()
        print("✓ Clicked New Project button")
        
        
        # Step 3: Fill in the Project Form Modal
        # Project Name
        project_name_input = driver.find_element(By.CSS_SELECTOR, ".ant-input[placeholder*='Website Redesign']")
        project_name_input.send_keys("Automated Test Project")
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
        home_menu = driver.find_element(By.CSS_SELECTOR, "[data-menu-id='home']")
        home_menu.click()
        time.sleep(0.5)
        # ========== NOW CREATE A TASK ==========
        print("--- Creating Task ---")
        # Click on "New Task" button
        new_task_button = driver.find_element(By.CSS_SELECTOR, ".createtask")
        new_task_button.click()
        
        # Fill in the task form
        # Title
        title_input = driver.find_element(By.ID, "title")
        title_input.send_keys("Automated Test Task")
        
        # Description
        description_textarea = driver.find_element(By.ID, "description")
        description_textarea.send_keys("This is a test task created by Selenium automation")
        
        
        # Using JavaScript to set the value properly and trigger Vue reactivity
        due_date_input = driver.find_element(By.ID, "dueDate")
        driver.execute_script("""
            const dateInput = arguments[0];
            dateInput.value = '2025-10-17';
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
        projects_menu = driver.find_element(By.CSS_SELECTOR, "[data-menu-id='projects']")
        projects_menu.click()
        print("✓ Clicked Projects menu")
        time.sleep(1)
        
        # Click on the "Assign Task" tab
        assign_task_tab = driver.find_element(By.XPATH, "//div[@role='tab' and contains(., 'Assign Task')]")
        assign_task_tab.click()
        print("✓ Clicked Assign Task tab")
        
        
        # Wait for tasks to load and click on the first task in the available tasks list
        first_task = driver.find_element(By.CSS_SELECTOR, ".ant-list-item")
        first_task.click()
        print("✓ Selected first task from available tasks")
        
        
        # Wait for projects list to load on the right side and click on the first project
        
        # Get all list items - first ones are tasks (left), later ones are projects (right)
        all_list_items = driver.find_elements(By.CSS_SELECTOR, ".ant-list-item")
        
        # Find the first project item (it will be in the second list, after the task items)
        # We can identify it by looking for items that contain the "Assign Task" button or project details
        project_items = driver.find_elements(By.XPATH, "//div[@style and contains(@style, 'height: 300px')]//li[contains(@class, 'ant-list-item')]")
        
        if project_items:
            project_items[0].click()
            print("✓ Selected first project from available projects")
            
        else:
            print("⚠ No projects found on the right side")
        
        # Click on the "Assign Task" button that appears after selecting a project
        assign_button = driver.find_element(By.XPATH, "//button[contains(., 'Assign') and (@type='primary' or contains(@class, 'ant-btn-primary'))]")
        assign_button.click()
        print("✓ Clicked Assign Task button")
        
        
        
        
    finally:
        # Only quit if not reusing browser
        if not reuse_browser:
            driver.quit()
        else:
            print("\n✓ Test completed! Browser window will remain open for inspection.")


if __name__ == "__main__":

    test_login(reuse_browser=True)
