Add-Type -AssemblyName System.Drawing
$col = New-Object System.Drawing.Text.InstalledFontCollection
$col.Families | Where-Object { $_.Name -match 'Montserrat' } | ForEach-Object { $_.Name }
Write-Output "---count---"
($col.Families | Where-Object { $_.Name -match 'Montserrat' }).Count
