# Hyperframes Dependencies Check & Install
# Ejecutar en la carpeta del proyecto

Write-Host "=== Checking Dependencies ===" -ForegroundColor Cyan

# Check Node.js
Write-Host "`n[1] Node.js..." -NoNewline
try {
    $nodeVersion = node --version 2>$null
    Write-Host "OK ($nodeVersion)" -ForegroundColor Green
} catch {
    Write-Host "MISSING - Install from https://nodejs.org" -ForegroundColor Red
}

# Check npm
Write-Host "[2] npm..." -NoNewline
try {
    $npmVersion = npm --version 2>$null
    Write-Host "OK (v$npmVersion)" -ForegroundColor Green
} catch {
    Write-Host "MISSING" -ForegroundColor Red
}

# Check FFmpeg
Write-Host "[3] FFmpeg..." -NoNewline
try {
    $ffmpegVersion = ffmpeg -version 2>&1 | Select-Object -First 1
    if ($ffmpegVersion) {
        Write-Host "OK" -ForegroundColor Green
    }
} catch {
    Write-Host "MISSING - Install from https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -ForegroundColor Red
}

# Check Hyperframes
Write-Host "[4] Hyperframes..." -NoNewline
try {
    $hfVersion = npx hyperframes --version 2>$null
    Write-Host "OK" -ForegroundColor Green
} catch {
    Write-Host "NOT INSTALLED - Run: npm install @hyperframes/core@alpha" -ForegroundColor Yellow
}

Write-Host "`n=== To Install ===" -ForegroundColor Cyan
Write-Host "npm install @hyperframes/core@alpha"
Write-Host "`n=== Render ===" -ForegroundColor Cyan
Write-Host "npx hyperframes render"