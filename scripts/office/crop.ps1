param([string]$In, [int]$X, [int]$Y, [int]$W, [int]$H, [string]$Out)
Add-Type -AssemblyName System.Drawing
$src = [System.Drawing.Bitmap]::FromFile((Resolve-Path $In).Path)
$rect = New-Object System.Drawing.Rectangle($X, $Y, $W, $H)
$dst = $src.Clone($rect, $src.PixelFormat)
$outPath = Join-Path (Get-Location) $Out
$dst.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)
$src.Dispose(); $dst.Dispose()
Write-Output ("cropped -> " + $Out + "  " + $W + "x" + $H)
