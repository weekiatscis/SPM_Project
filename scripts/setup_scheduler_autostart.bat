@echo off
setlocal EnableDelayedExpansion

echo ======================================================================
echo SPM Notification Scheduler - Auto-start Setup (Windows)
echo ======================================================================
echo.
echo This will configure the notification scheduler to:
echo   - Start automatically when you log in
echo   - Keep running in the background
echo   - Check for task reminders every hour
echo   - Restart automatically if it crashes
echo.

set PROJECT_DIR=%~dp0
set SCHEDULER_SCRIPT=%PROJECT_DIR%src\microservices\notifications\notification_scheduler.py

echo Project directory: %PROJECT_DIR%
echo Scheduler script: %SCHEDULER_SCRIPT%
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python and add it to PATH.
    pause
    exit /b 1
)

REM Check if scheduler script exists
if not exist "%SCHEDULER_SCRIPT%" (
    echo ❌ Scheduler script not found: %SCHEDULER_SCRIPT%
    pause
    exit /b 1
)

REM Create logs directory
echo 1️⃣ Creating logs directory...
if not exist "%PROJECT_DIR%logs" mkdir "%PROJECT_DIR%logs"
echo    ✅ Created: %PROJECT_DIR%logs
echo.

REM Create batch file to run scheduler
echo 2️⃣ Creating scheduler batch file...
(
echo @echo off
echo title SPM Notification Scheduler
echo cd /d "%PROJECT_DIR%"
echo echo Starting SPM Notification Scheduler...
echo echo Project Directory: %%CD%%
echo echo.
echo :loop
echo echo [%%DATE%% %%TIME%%] Starting scheduler... ^>^> logs\notification_scheduler.log
echo python "%SCHEDULER_SCRIPT%" ^>^> logs\notification_scheduler.log 2^>^> logs\notification_scheduler_error.log
echo if %%ERRORLEVEL%% NEQ 0 ^(
echo     echo [%%DATE%% %%TIME%%] Scheduler exited with error code %%ERRORLEVEL%% ^>^> logs\notification_scheduler_error.log
echo     echo Scheduler crashed! Restarting in 30 seconds...
echo     timeout /t 30 /nobreak ^> nul
echo     goto loop
echo ^)
echo echo [%%DATE%% %%TIME%%] Scheduler stopped normally ^>^> logs\notification_scheduler.log
) > "%PROJECT_DIR%start_scheduler.bat"
echo    ✅ Created: %PROJECT_DIR%start_scheduler.bat
echo.

REM Create startup shortcut using PowerShell
echo 3️⃣ Creating startup shortcut...
set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
powershell -Command "try { $WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTUP_FOLDER%\SPM_Scheduler.lnk'); $Shortcut.TargetPath = '%PROJECT_DIR%start_scheduler.bat'; $Shortcut.WorkingDirectory = '%PROJECT_DIR%'; $Shortcut.WindowStyle = 7; $Shortcut.Save(); Write-Host '   ✅ Created startup shortcut' } catch { Write-Host '   ❌ Failed to create startup shortcut:' $_.Exception.Message }"
echo.

REM Create desktop shortcut
echo 4️⃣ Creating desktop shortcut...
set DESKTOP_FOLDER=%USERPROFILE%\Desktop
powershell -Command "try { $WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP_FOLDER%\SPM_Scheduler.lnk'); $Shortcut.TargetPath = '%PROJECT_DIR%start_scheduler.bat'; $Shortcut.WorkingDirectory = '%PROJECT_DIR%'; $Shortcut.Save(); Write-Host '   ✅ Created desktop shortcut' } catch { Write-Host '   ❌ Failed to create desktop shortcut:' $_.Exception.Message }"
echo.

echo 5️⃣ Starting notification scheduler...
start /min "" "%PROJECT_DIR%start_scheduler.bat"
timeout /t 3 /nobreak > nul
echo    ✅ Scheduler started!
echo.

echo ======================================================================
echo ✅ SETUP COMPLETE!
echo ======================================================================
echo.
echo The notification scheduler is now running and will:
echo   ✓ Start automatically when you log in to Windows
echo   ✓ Check for task reminders every hour
echo   ✓ Send email notifications based on reminder schedules
echo   ✓ Restart automatically if it crashes
echo   ✓ Run minimized in the background
echo.
echo 📊 Monitoring:
echo   View logs:        type logs\notification_scheduler.log
echo   View errors:      type logs\notification_scheduler_error.log
echo   View live logs:   powershell "Get-Content logs\notification_scheduler.log -Tail 10 -Wait"
echo.
echo 🔧 Management:
echo   Stop scheduler:   Close the scheduler window or kill python process
echo   Start manually:   Double-click desktop shortcut or run start_scheduler.bat
echo   Remove startup:   Delete "%STARTUP_FOLDER%\SPM_Scheduler.lnk"
echo.
echo ✨ All done! Your notification system is ready! ✨
echo.
pause