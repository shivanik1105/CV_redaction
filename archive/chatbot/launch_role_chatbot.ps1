# PowerShell script to launch role chatbots
# Usage: .\launch_role_chatbot.ps1 -Role "senior_python_developer" -Share

param(
    [Parameter(Mandatory=$true)]
    [string]$Role,
    
    [Parameter(Mandatory=$false)]
    [switch]$Share,
    
    [Parameter(Mandatory=$false)]
    [int]$Port = 7860
)

Write-Host "🚀 Launching Role Chatbot: $Role" -ForegroundColor Green

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptPath "role_chatbot_template.py"

if (-not (Test-Path $pythonScript)) {
    Write-Host "❌ Error: role_chatbot_template.py not found" -ForegroundColor Red
    exit 1
}

$roleFolder = Join-Path $scriptPath "roles" $Role

if (-not (Test-Path $roleFolder)) {
    Write-Host "❌ Error: Role folder not found: $roleFolder" -ForegroundColor Red
    Write-Host ""
    Write-Host "Available roles:" -ForegroundColor Yellow
    Get-ChildItem (Join-Path $scriptPath "roles") -Directory | ForEach-Object { Write-Host "  - $($_.Name)" }
    Write-Host ""
    Write-Host "Create a new role with:" -ForegroundColor Cyan
    Write-Host "  python chatbot/create_role_chatbot.py --name `"Your Role Name`""
    exit 1
}

$args = @("--role", $Role, "--port", $Port)

if ($Share) {
    $args += "--share"
}

Write-Host "📁 Role folder: $roleFolder" -ForegroundColor Cyan
Write-Host "🌐 Port: $Port" -ForegroundColor Cyan

if ($Share) {
    Write-Host "🔗 Creating shareable link..." -ForegroundColor Cyan
}

Write-Host ""

python $pythonScript @args
