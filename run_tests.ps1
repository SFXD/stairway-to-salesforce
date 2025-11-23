# run_tests.ps1
# PowerShell script to run tests

Write-Host "Running Salesforce Tests..." -ForegroundColor Green

# Run all tests with coverage
Write-Host "`nRunning all tests with coverage..." -ForegroundColor Yellow
pytest dlt_salesforce_advanced/tests/ -v --cov=dlt_salesforce_advanced --cov-report=html --cov-report=term

# Run only unit tests
#Write-Host "`nRunning unit tests only..." -ForegroundColor Yellow
#pytest tests/unit/ -v -m unit

# Run tests for specific module
#Write-Host "`nRunning utils tests..." -ForegroundColor Yellow
#pytest tests/unit/utils/ -v

#Write-Host "`nRunning source tests..." -ForegroundColor Yellow
#pytest tests/unit/sources/ -v

#Write-Host "`nRunning destination tests..." -ForegroundColor Yellow
#pytest tests/unit/destinations/ -v

#Write-Host "`nTest run complete! Check htmlcov/index.html for coverage report." -ForegroundColor Green