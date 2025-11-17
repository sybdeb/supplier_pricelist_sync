@echo off
echo ========================================
echo Deploying supplier_pricelist_sync to NAS
echo ========================================
echo.

set SOURCE=C:\Users\Sybde\Projects\supplier_pricelist_sync
set DEST=O:\odoo\addons\supplier_pricelist_sync

echo Copying __init__.py...
copy /Y "%SOURCE%\__init__.py" "%DEST%\" >nul

echo Copying __manifest__.py...
copy /Y "%SOURCE%\__manifest__.py" "%DEST%\" >nul

echo Copying models folder...
xcopy /E /I /Y /Q "%SOURCE%\models" "%DEST%\models" >nul

echo Copying views folder...
xcopy /E /I /Y /Q "%SOURCE%\views" "%DEST%\views" >nul

echo Copying security folder...
xcopy /E /I /Y /Q "%SOURCE%\security" "%DEST%\security" >nul

echo Copying wizard folder...
xcopy /E /I /Y /Q "%SOURCE%\wizard" "%DEST%\wizard" >nul

echo.
echo Cleaning __pycache__ folders...
for /d /r "%DEST%" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul

echo.
echo ========================================
echo Deploy completed successfully!
echo ========================================
echo Location: %DEST%
echo.
echo Next steps:
echo 1. Restart Odoo on NAS
echo 2. Apps -^> supplier_pricelist_sync -^> Upgrade
echo.
pause
