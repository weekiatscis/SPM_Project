# End-to-End Testing with Selenium

This folder contains automated end-to-end tests using Selenium WebDriver to test the complete user workflow of the SPM Project application.

## Test Coverage

The current test (`Test_AssignTaskToProj.py`) covers:
1. ✅ User login
2. ✅ Creating a new project
3. ✅ Creating a new task
4. ✅ Assigning task to project

## Prerequisites

### Required Software
- Python 3.7 or higher
- Google Chrome browser
- Selenium WebDriver

### Install Dependencies

```bash
pip install selenium
```

## Running the Tests

This mode keeps the browser open between test runs, making debugging easier and tests faster.

#### Mac/Linux: --------------------------------------------------------

1. **Start Chrome with remote debugging:**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome_dev_test \
  --no-first-run \
  --no-default-browser-check
```

2. **Run the test:**
```bash
python "tests/end_to_end testing/Test_AssignTaskToProj.py"
```

#### Windows:----------------------------------------------------------

1. **Start Chrome with remote debugging:**
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --user-data-dir=C:\temp\chrome_dev_test ^
  --no-first-run ^
  --no-default-browser-check
```


2. **Run the test:**
```cmd
python "tests\end_to_end testing\Test_AssignTaskToProj.py"
```

