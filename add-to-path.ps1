# PATH에 Upscaler 디렉토리 추가 스크립트
$upscalerPath = $PSScriptRoot
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

if ($currentPath -notlike "*$upscalerPath*") {
    $newPath = "$currentPath;$upscalerPath"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "[SUCCESS] Added $upscalerPath to PATH" -ForegroundColor Green
    Write-Host "Please restart your terminal for changes to take effect" -ForegroundColor Yellow
} else {
    Write-Host "[INFO] $upscalerPath is already in PATH" -ForegroundColor Cyan
}

# 현재 세션에도 즉시 적용
$env:Path += ";$upscalerPath"

Write-Host "`n[AVAILABLE COMMANDS]" -ForegroundColor Cyan
Write-Host "  upscaler-gpu    : Full upscaler with GPU support"
Write-Host "  upscale-image   : Quick image upscaling"
Write-Host "  upscale-video   : Quick video upscaling"
Write-Host "`n[EXAMPLE USAGE]" -ForegroundColor Yellow
Write-Host "  upscaler-gpu image input.jpg output.jpg --scale 4"
Write-Host "  upscale-image photo.jpg photo_4x.jpg"
Write-Host "  upscale-video movie.mp4 movie_4x.mp4 --copy-audio"
