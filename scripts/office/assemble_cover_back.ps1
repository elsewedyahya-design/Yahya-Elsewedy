param(
  [string]$Master = "MASTER_TEMPLATE.hardened.docx",
  [string]$Source = "FULL_OFFER.pixelperfect.docx",
  [string]$Out    = "FULL_OFFER.final.docx"
)
$ErrorActionPreference = "Stop"

# enums
$wdGoToPage = 1; $wdGoToAbsolute = 1; $wdGoToLast = -1
$wdCollapseEnd = 0
$wdSectionBreakNextPage = 2
$wdFormatOriginalFormatting = 16
$wdReplaceAll = 2
$wdStatisticPages = 2
$wdFormatXMLDocument = 12

$masterPath = (Resolve-Path $Master).Path
Copy-Item $Source $Out -Force
$outPath = (Join-Path (Get-Location).Path $Out)

$wd = New-Object -ComObject Word.Application
$wd.Visible = $false
$wd.DisplayAlerts = 0
try { $wd.AutomationSecurity = 3 } catch {}
$wd.Options.Pagination = $true

function Repl($doc, $find, $rep) {
  $f = $doc.Content.Find
  $f.ClearFormatting()
  $f.Replacement.ClearFormatting()
  $f.MatchWildcards = $false
  [void]$f.Execute($find, $false, $false, $false, $false, $false, $true, 1, $false, $rep, $wdReplaceAll)
}

try {
  $m = $wd.Documents.Open($masterPath, $false, $true, $false)   # readonly
  $f = $wd.Documents.Open($outPath,   $false, $false, $false)   # editable

  $m.Repaginate()
  $f.Repaginate()

  # ---------- BACK PAGE (append first; end offsets stay stable) ----------
  $bpStart = ($m.GoTo($wdGoToPage, $wdGoToLast, $null, $null)).Start
  $bpRange = $m.Range($bpStart, $m.Content.End)
  $bpRange.Copy()

  $tail = $f.Content
  $tail.Collapse($wdCollapseEnd)
  $tail.InsertBreak($wdSectionBreakNextPage)
  $tail2 = $f.Content
  $tail2.Collapse($wdCollapseEnd)
  [void]$tail2.PasteAndFormat($wdFormatOriginalFormatting)

  # ---------- COVER (replace flat cover at start) ----------
  $p2start = ($m.GoTo($wdGoToPage, $wdGoToAbsolute, 2, $null)).Start
  $coverRange = $m.Range(0, $p2start)
  $coverRange.Copy()

  # delete FULL_OFFER's existing flat cover = its first section, INCLUDING its section break
  $sec1End = $f.Sections.Item(1).Range.End
  $delRange = $f.Range(0, $sec1End)
  $delRange.Delete()

  # paste master cover at very start
  $ins = $f.Range(0, 0)
  [void]$ins.PasteAndFormat($wdFormatOriginalFormatting)

  # convert the cover's trailing manual page break into a section break (next page)
  $pb = $f.Content
  $pb.Find.ClearFormatting()
  $pb.Find.MatchWildcards = $false
  if ($pb.Find.Execute("^m")) {
    $pb.Delete()
    $pb.InsertBreak($wdSectionBreakNextPage)
  }

  # give the cover section the master's A4 page geometry
  $ms = $m.Sections.Item(1).PageSetup
  $fs = $f.Sections.Item(1).PageSetup
  $fs.PageWidth      = $ms.PageWidth
  $fs.PageHeight     = $ms.PageHeight
  $fs.Orientation    = $ms.Orientation
  $fs.TopMargin      = $ms.TopMargin
  $fs.BottomMargin   = $ms.BottomMargin
  $fs.LeftMargin     = $ms.LeftMargin
  $fs.RightMargin    = $ms.RightMargin
  $fs.HeaderDistance = $ms.HeaderDistance
  $fs.FooterDistance = $ms.FooterDistance
  $fs.Gutter         = $ms.Gutter

  # ---------- TOKENS ----------
  Repl $f "{{PROJECT_NAME}}" "CEER Automotive"
  Repl $f "{{CLIENT_NAME}}"  "XXXXXXX"
  Repl $f "{{DATE}}"         "22-10-2025"
  Repl $f "{{REFERENCE}}"    "240146SP-SAU-R2"
  Repl $f "{{REVISION}}"     "R2"

  $f.Repaginate()
  $f.SaveAs2($outPath, $wdFormatXMLDocument)

  # ---------- VERIFY ----------
  $pages = $f.ComputeStatistics($wdStatisticPages, $false)
  $secs  = $f.Sections.Count
  $left  = 0
  $chk = $f.Content.Find; $chk.ClearFormatting(); $chk.MatchWildcards = $false
  if ($chk.Execute("{{")) { $left = 1 }
  Write-Output ("ASSEMBLE_OK pages=" + $pages + " sections=" + $secs + " tokens_left=" + $left)

  $m.Close($false)
  $f.Close($false)
} catch {
  Write-Output ("ASSEMBLE_FAILED: " + $_.Exception.Message)
} finally {
  $wd.Quit()
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($wd) | Out-Null
}
