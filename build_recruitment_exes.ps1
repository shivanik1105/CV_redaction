$ErrorActionPreference = 'Stop'

$python = 'c:/Users/shiva/Downloads/samplecvs/.venv/Scripts/python.exe'

Write-Host 'Building CVRedactor.exe...' -ForegroundColor Cyan
& $python -m PyInstaller --noconfirm build_cv_redactor.spec --distpath release/cvredactor --workpath build/cvredactor

Write-Host 'Building RecruitmentSystem.exe...' -ForegroundColor Cyan
& $python -m PyInstaller --noconfirm build_recruitment_system.spec --distpath release/recruitment --workpath build/recruitment

Write-Host ''
Write-Host 'Build complete.' -ForegroundColor Green
Write-Host 'Outputs:' -ForegroundColor Yellow
Write-Host '  release/cvredactor/CVRedactor.exe'
Write-Host '  release/recruitment/RecruitmentSystem.exe'
