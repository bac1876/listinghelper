# GitHub Secrets Setup Script for Windows
# This script automates adding Cloudinary secrets to your GitHub repository

Write-Host "=== GitHub Secrets Setup for Remotion Video Rendering ===" -ForegroundColor Cyan
Write-Host ""

# Function to securely read password
function Read-Password {
    param([string]$Prompt)
    Write-Host $Prompt -NoNewline
    $password = Read-Host -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
    $plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
    return $plainPassword
}

# Get GitHub credentials
$githubUsername = Read-Host "Enter your GitHub username"
$githubRepo = Read-Host "Enter your repository name"

Write-Host ""
Write-Host "--- Cloudinary Credentials ---" -ForegroundColor Yellow
$cloudinaryCloud = Read-Host "Enter Cloudinary Cloud Name"
$cloudinaryKey = Read-Host "Enter Cloudinary API Key"
$cloudinarySecret = Read-Password "Enter Cloudinary API Secret: "

Write-Host ""
Write-Host "--- GitHub Authentication ---" -ForegroundColor Yellow
Write-Host "To add secrets via GitHub CLI, you'll need a Personal Access Token with 'repo' scope."
Write-Host ""

# Check if GitHub CLI is installed
$ghInstalled = Get-Command gh -ErrorAction SilentlyContinue

if (-not $ghInstalled) {
    Write-Host "GitHub CLI (gh) is not installed." -ForegroundColor Red
    Write-Host "Would you like to install it? (Recommended)" -ForegroundColor Yellow
    $install = Read-Host "Install GitHub CLI? (y/n)"
    
    if ($install -eq 'y') {
        Write-Host "Installing GitHub CLI..." -ForegroundColor Green
        # Install using winget (Windows Package Manager)
        winget install --id GitHub.cli
        
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        Write-Host "GitHub CLI installed!" -ForegroundColor Green
    } else {
        Write-Host "Please install GitHub CLI manually from: https://cli.github.com/" -ForegroundColor Yellow
        Write-Host "Or follow the manual setup in GITHUB_ACTIONS_SETUP.md" -ForegroundColor Yellow
        exit 1
    }
}

# Authenticate with GitHub CLI
Write-Host ""
Write-Host "Authenticating with GitHub..." -ForegroundColor Cyan
gh auth login

# Set the repository
Write-Host ""
Write-Host "Setting repository context..." -ForegroundColor Cyan
gh repo set "$githubUsername/$githubRepo"

# Function to add a secret
function Add-GitHubSecret {
    param(
        [string]$Name,
        [string]$Value
    )
    
    Write-Host "Adding secret: $Name" -ForegroundColor Yellow
    $Value | gh secret set $Name
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Successfully added $Name" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to add $Name" -ForegroundColor Red
    }
}

# Add all secrets
Write-Host ""
Write-Host "Adding Cloudinary secrets to repository..." -ForegroundColor Cyan
Add-GitHubSecret -Name "CLOUDINARY_CLOUD_NAME" -Value $cloudinaryCloud
Add-GitHubSecret -Name "CLOUDINARY_API_KEY" -Value $cloudinaryKey
Add-GitHubSecret -Name "CLOUDINARY_API_SECRET" -Value $cloudinarySecret

# Create Personal Access Token reminder
Write-Host ""
Write-Host "=== Personal Access Token Setup ===" -ForegroundColor Cyan
Write-Host "You need to create a Personal Access Token for Railway to trigger GitHub Actions." -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Go to: https://github.com/settings/tokens/new" -ForegroundColor White
Write-Host "2. Name it: 'Railway Video Render - $githubRepo'" -ForegroundColor White
Write-Host "3. Select scopes:" -ForegroundColor White
Write-Host "   - repo (Full control of private repositories)" -ForegroundColor Gray
Write-Host "   - workflow (Update GitHub Action workflows)" -ForegroundColor Gray
Write-Host "4. Generate token and COPY IT IMMEDIATELY!" -ForegroundColor Yellow
Write-Host ""

# Open browser to token page
$openBrowser = Read-Host "Open GitHub token page in browser? (y/n)"
if ($openBrowser -eq 'y') {
    Start-Process "https://github.com/settings/tokens/new"
}

Write-Host ""
Write-Host "=== Railway Environment Variables ===" -ForegroundColor Cyan
Write-Host "Add these to your Railway app:" -ForegroundColor Yellow
Write-Host ""
Write-Host "USE_GITHUB_ACTIONS=true" -ForegroundColor White
Write-Host "GITHUB_TOKEN=<your_personal_access_token>" -ForegroundColor White
Write-Host "GITHUB_OWNER=$githubUsername" -ForegroundColor White
Write-Host "GITHUB_REPO=$githubRepo" -ForegroundColor White
Write-Host ""

# Save to file for easy copying
$envVars = @"
USE_GITHUB_ACTIONS=true
GITHUB_TOKEN=<your_personal_access_token>
GITHUB_OWNER=$githubUsername
GITHUB_REPO=$githubRepo
"@

$envVars | Out-File -FilePath "railway_github_env_vars.txt" -Encoding UTF8
Write-Host "Environment variables saved to: railway_github_env_vars.txt" -ForegroundColor Green

Write-Host ""
Write-Host "✅ Setup complete! Your GitHub repository is configured for Remotion video rendering." -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Create and copy your Personal Access Token" -ForegroundColor White
Write-Host "2. Add the environment variables to Railway" -ForegroundColor White
Write-Host "3. Test the video generation!" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to exit"