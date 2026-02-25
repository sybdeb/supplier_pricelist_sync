# Update Lean Version in dev_versies
# Run this after commits to keep dev_versies synchronized

Write-Host "=== Updating Lean Dev Version ===" -ForegroundColor Cyan

$source = 'C:\Users\Sybde\Projects\product_supplier_sync'
$dest = 'C:\Users\Sybde\Projects\dev_versies\product_supplier_sync'

# Remove old version using CMD (handles 'nul' device name issue)
Write-Host "Removing old dev version..." -ForegroundColor Yellow
if (Test-Path $dest) {
    cmd /c "rmdir /S /Q `"$dest`" 2>nul"
    Start-Sleep -Milliseconds 100
}

# Create destination folder
New-Item -ItemType Directory -Path $dest -Force | Out-Null

# Copy clean version (exclude docs, tests, backups, etc.)
Write-Host "Copying lean module to dev_versies..." -ForegroundColor Yellow
$robocopyResult = Robocopy $source $dest /E /XD tests __pycache__ .git .vscode docs /XF *.md *.sh *.pyc *.pyo .gitignore *.backup *_BACKUP.py /NFL /NDL /NJH /NJS

# Clean up any backup files that slipped through
Write-Host "Cleaning backup files..." -ForegroundColor Yellow
if (Test-Path "$dest\models") {
    Get-ChildItem "$dest\models" -Filter *.backup -ErrorAction SilentlyContinue | Remove-Item -Force
    Get-ChildItem "$dest\models" -Filter *_BACKUP.py -ErrorAction SilentlyContinue | Remove-Item -Force
}

# Remove 'nul' device file if it exists (Windows reserved name issue)
if (Test-Path "$dest\nul") {
    cmd /c "del /F /Q `"$dest\nul`" 2>nul"
}

Write-Host "=== Lean version updated in dev_versies ===" -ForegroundColor Green
