# Deploy supplier_pricelist_sync module to NAS
# Run: .\deploy_to_nas.ps1

$source = "C:\Users\Sybde\Projects\supplier_pricelist_sync"
$dest = "O:\odoo\addons\supplier_pricelist_sync"

Write-Host "Deploying module to NAS..." -ForegroundColor Cyan

# Ensure target directory exists
New-Item -ItemType Directory -Force -Path $dest | Out-Null

# Copy module files (only Odoo-required files)
Write-Host "Copying __init__.py..." -ForegroundColor Gray
Copy-Item -Path "$source\__init__.py" -Destination $dest -Force

Write-Host "Copying __manifest__.py..." -ForegroundColor Gray
Copy-Item -Path "$source\__manifest__.py" -Destination $dest -Force

Write-Host "Copying models/..." -ForegroundColor Gray
Copy-Item -Path "$source\models" -Destination $dest -Recurse -Force

Write-Host "Copying views/..." -ForegroundColor Gray
Copy-Item -Path "$source\views" -Destination $dest -Recurse -Force

Write-Host "Copying security/..." -ForegroundColor Gray
Copy-Item -Path "$source\security" -Destination $dest -Recurse -Force

Write-Host "Copying wizard/..." -ForegroundColor Gray
Copy-Item -Path "$source\wizard" -Destination $dest -Recurse -Force

# Clean up __pycache__ in destination
Write-Host "Cleaning __pycache__ folders..." -ForegroundColor Gray
Get-ChildItem -Path $dest -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

Write-Host "`nDeploy completed successfully!" -ForegroundColor Green
Write-Host "Location: $dest" -ForegroundColor Yellow
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Restart Odoo op NAS" -ForegroundColor White
Write-Host "2. Apps → supplier_pricelist_sync → Upgrade" -ForegroundColor White
