param(
    [string]$Report = (Join-Path $PSScriptRoot '../report/KeyGuard_Report.docx'),
    [string]$Pdf = (Join-Path $PSScriptRoot '../report/KeyGuard_Report.pdf')
)
$ErrorActionPreference = 'Stop'
$reportPath = (Resolve-Path -LiteralPath $Report).Path
$pdfPath = [IO.Path]::GetFullPath($Pdf)
$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($reportPath, $false, $false)
    $document.Repaginate()
    $pages = $document.ComputeStatistics(2)
    $document.ExportAsFixedFormat($pdfPath, 17)
    $document.Save()
    Write-Output "RENDERED_PAGES=$pages"
    Write-Output "PDF=$pdfPath"
} finally {
    if ($null -ne $document) {
        $document.Close(0)
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($document)
    }
    if ($null -ne $word) {
        $word.Quit()
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($word)
    }
}
