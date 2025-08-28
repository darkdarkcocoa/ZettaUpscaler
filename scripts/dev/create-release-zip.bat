@echo off
echo Creating release package...

set RELEASE_NAME=ZettaUpscaler-Portable
set TEMP_DIR=%TEMP%\%RELEASE_NAME%

:: Clean up any existing temp directory
if exist "%TEMP_DIR%" rmdir /S /Q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"

:: Copy necessary files (excluding .venv, .git, etc.)
echo Copying files...
xcopy /E /I /Y upscaler "%TEMP_DIR%\upscaler" >nul
xcopy /E /I /Y scripts "%TEMP_DIR%\scripts" >nul
copy __main__.py "%TEMP_DIR%\" >nul
copy install.bat "%TEMP_DIR%\" >nul
copy LICENSE "%TEMP_DIR%\" >nul
copy README.md "%TEMP_DIR%\" >nul
copy QUICK_START.md "%TEMP_DIR%\" >nul
copy PROJECT_STRUCTURE.md "%TEMP_DIR%\" >nul
copy requirements.txt "%TEMP_DIR%\" >nul
copy setup.py "%TEMP_DIR%\" >nul

:: Create zip file
echo Creating ZIP file...
powershell -Command "Compress-Archive -Path '%TEMP_DIR%\*' -DestinationPath '%RELEASE_NAME%.zip' -Force"

:: Clean up
rmdir /S /Q "%TEMP_DIR%"

:: Get file size
for %%A in ("%RELEASE_NAME%.zip") do set SIZE=%%~zA
set /a SIZE_MB=%SIZE%/1048576

echo.
echo ========================================
echo Release package created successfully!
echo ========================================
echo File: %RELEASE_NAME%.zip
echo Size: %SIZE_MB% MB
echo.
echo Users can:
echo 1. Extract this ZIP file
echo 2. Run install.bat as Administrator
echo 3. Use 'upscaler' command anywhere!
echo ========================================
pause