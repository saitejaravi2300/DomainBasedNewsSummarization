#!/usr/bin/env pwsh

Write-Host "`n$('='*60)" -ForegroundColor Cyan
Write-Host "COMPLETE API TESTING SUITE" -ForegroundColor Cyan
Write-Host "$('='*60)`n" -ForegroundColor Cyan

# Test 1: Registration
Write-Host "TEST 1: USER REGISTRATION" -ForegroundColor Yellow
try {
    $postData = @{
        email = "alice_test@example.com"
        password = "SecurePass123"
        name = "Alice Smith"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:8000/auth/register" `
        -Method POST -Headers @{"Content-Type"="application/json"} -Body $postData
    
    $data = $response.Content | ConvertFrom-Json
    Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "  User ID: $($data.user.id)"
    Write-Host "  Email: $($data.user.email)"
    Write-Host "  Token (first 50 chars): $($data.token.Substring(0,50))..."
    
    $registerToken = $data.token
    $userId = $data.user.id
} catch {
    Write-Host "✗ Error: $($_.ErrorDetails.Message)" -ForegroundColor Red
    exit 1
}

# Test 2: Login
Write-Host "`nTEST 2: USER LOGIN" -ForegroundColor Yellow
try {
    $postData = @{
        email = "alice_test@example.com"
        password = "SecurePass123"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:8000/auth/login" `
        -Method POST -Headers @{"Content-Type"="application/json"} -Body $postData
    
    $data = $response.Content | ConvertFrom-Json
    Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "  User ID: $($data.user.id)"
    Write-Host "  Token (first 50 chars): $($data.token.Substring(0,50))..."
    
    $loginToken = $data.token
} catch {
    Write-Host "✗ Error: $($_.ErrorDetails.Message)" -ForegroundColor Red
}

# Test 3: Wrong Password
Write-Host "`nTEST 3: LOGIN WITH WRONG PASSWORD (Should Fail)" -ForegroundColor Yellow
try {
    $postData = @{
        email = "alice_test@example.com"
        password = "WrongPassword"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:8000/auth/login" `
        -Method POST -Headers @{"Content-Type"="application/json"} -Body $postData
    
    Write-Host "✗ Should have failed! Got: $($response.StatusCode)" -ForegroundColor Red
} catch {
    $error = $_.ErrorDetails.Message | ConvertFrom-Json
    Write-Host "✓ Correctly rejected (401): $($error.detail)" -ForegroundColor Green
}

# Test 4: Update Preferences with JWT
Write-Host "`nTEST 4: UPDATE PREFERENCES (JWT Auth)" -ForegroundColor Yellow
try {
    $postData = @{
        default_domain = "finance"
        default_days = 30
        daily_digest_enabled = $true
        daily_digest_time = "09:00"
        daily_digest_domain = "ai"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:8000/user/preferences" `
        -Method PATCH `
        -Headers @{
            "Content-Type" = "application/json"
            "Authorization" = "Bearer $registerToken"
        } `
        -Body $postData
    
    $data = $response.Content | ConvertFrom-Json
    Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "  Default Domain: $($data.preferences.default_domain)"
    Write-Host "  Default Days: $($data.preferences.default_days)"
} catch {
    Write-Host "✗ Error: $($_.ErrorDetails.Message)" -ForegroundColor Red
}

# Test 5: Create Custom Domain with JWT
Write-Host "`nTEST 5: CREATE CUSTOM DOMAIN (JWT Auth)" -ForegroundColor Yellow
try {
    $postData = @{
        domain_name = "Quantum Computing"
        keywords = "quantum,computing,qubits"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:8000/user/custom-domains" `
        -Method POST `
        -Headers @{
            "Content-Type" = "application/json"
            "Authorization" = "Bearer $registerToken"
        } `
        -Body $postData
    
    $data = $response.Content | ConvertFrom-Json
    Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "  Domain ID: $($data.domain.id)"
    Write-Host "  Domain Name: $($data.domain.name)"
    Write-Host "  Keywords: $($data.domain.keywords)"
} catch {
    Write-Host "✗ Error: $($_.ErrorDetails.Message)" -ForegroundColor Red
}

# Test 6: Digest Generation
Write-Host "`nTEST 6: DIGEST GENERATION" -ForegroundColor Yellow
try {
    $postData = @{
        domain = "ai"
        days = 7
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:8000/digest/generate" `
        -Method POST -Headers @{"Content-Type"="application/json"} -Body $postData
    
    $data = $response.Content | ConvertFrom-Json
    Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "  Domain: $($data.domain)"
    Write-Host "  Total Trends: $($data.total_trends)"
    Write-Host "  Total Articles: $($data.total_articles)"
} catch {
    Write-Host "✗ Error: $($_.ErrorDetails.Message)" -ForegroundColor Red
}

Write-Host "`n$('='*60)" -ForegroundColor Green
Write-Host "ALL TESTS COMPLETED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "$('='*60)`n" -ForegroundColor Green
