param([string]$Path, [string]$Pdf)
$ErrorActionPreference = "Stop"
$full = (Resolve-Path $Path).Path
$out  = Join-Path (Get-Location) $Pdf
$w = New-Object -ComObject Word.Application
$w.Visible = $false
$w.DisplayAlerts = 0
try { $w.AutomationSecurity = 3 } catch {}
try {
    $d = $w.Documents.Open($full, $false, $true, $false)
    # ExportAsFixedFormat: fmt 17=PDF; Range 3=wdExportFromTo; From=1 To=1
    $d.ExportAsFixedFormat($out, 17, $false, 0, 3, 1, 1)
    $d.Close($false)
    Write-Output ("PDF_OK=" + $out)
} catch {
    Write-Output ("PDF_FAILED: " + $_.Exception.Message)
} finally {
    $w.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($w) | Out-Null
}
