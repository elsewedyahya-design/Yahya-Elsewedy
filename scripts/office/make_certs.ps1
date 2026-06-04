param([string]$In, [string]$OutDir)
# Split the composite cert strip into 4 cards and pad each (white) to the
# target slot aspect (952500/1333500 = 0.714286) so they render in FULL_OFFER's
# existing cert frames with no distortion and no layout/extent change.
Add-Type -AssemblyName System.Drawing
$ratio = 952500.0 / 1333500.0      # target width/height
$src = [System.Drawing.Bitmap]::FromFile((Resolve-Path $In).Path)
$H = $src.Height
# 4 cards: equal quarters of width (last one takes the remainder)
$cards = @(
  @{x=0;    w=345},
  @{x=345;  w=345},
  @{x=690;  w=345},
  @{x=1035; w=($src.Width - 1035)}
)
$i = 1
foreach ($c in $cards) {
  $card = $src.Clone((New-Object System.Drawing.Rectangle($c.x, 0, $c.w, $H)), $src.PixelFormat)
  $targetH = [int][Math]::Round($c.w / $ratio)        # pad height to match slot aspect
  $canvas = New-Object System.Drawing.Bitmap($c.w, $targetH)
  $g = [System.Drawing.Graphics]::FromImage($canvas)
  $g.Clear([System.Drawing.Color]::White)
  $yOff = [int][Math]::Round(($targetH - $H) / 2)
  $g.DrawImage($card, 0, $yOff, $c.w, $H)
  $g.Dispose()
  $out = Join-Path (Resolve-Path $OutDir).Path ("cert{0}.png" -f $i)
  $canvas.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
  $card.Dispose(); $canvas.Dispose()
  Write-Output ("cert{0}.png  {1}x{2}  (aspect {3:N4})" -f $i, $c.w, $targetH, ($c.w / $targetH))
  $i++
}
$src.Dispose()
