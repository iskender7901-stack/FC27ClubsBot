Add-Type -AssemblyName System.Drawing

$ClubId = "87430"
$Platform = "common-gen5"
$ReportsDir = Join-Path $PSScriptRoot "reports"
if (-not (Test-Path $ReportsDir)) { New-Item -ItemType Directory -Path $ReportsDir | Out-Null }

Write-Host "EA FC Clubs API'den mac verisi araniyor..." -ForegroundColor Cyan

$Headers = @{
    "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    "Accept" = "application/json"
}

# Hem Lig hem Hazırlık maçlarını tara, en günceli bul
$match = $null
$matchTypes = @("friendlyMatch", "leagueMatch", "playoffMatch")

foreach ($kind in $matchTypes) {
    $Url = "https://proclubs.ea.com/api/fc/clubs/matches?clubIds=$ClubId&platform=$Platform&matchType=$kind"
    try {
        $res = Invoke-RestMethod -Uri $Url -Method Get -Headers $Headers -TimeoutSec 10
        if ($res -and $res.Count -gt 0) {
            $match = $res[0]
            Write-Host "[BULUNDU] Son mac turu: $kind" -ForegroundColor Green
            break
        }
    } catch {
        Write-Host "[!] $kind sorgulanamadi." -ForegroundColor DarkGray
    }
}

if (-not $match) {
    Write-Host "[HATA] Oynanmis mac verisi bulunamadi." -ForegroundColor Red
    return
}

$clubs = $match.clubs.PSObject.Properties | ForEach-Object { $_.Value }
$myTeam = $clubs | Where-Object { [string]$_.id -eq $ClubId }
if (-not $myTeam) { $myTeam = $clubs[0] }
$oppTeam = $clubs | Where-Object { [string]$_.id -ne [string]$myTeam.id }
if (-not $oppTeam) { $oppTeam = $clubs[1] }

# Skor & Sonuç
$myScore = [int]$myTeam.goals
$oppScore = [int]$oppTeam.goals
$isWin = $myScore -gt $oppScore
$isLoss = $myScore -lt $oppScore

# 2. Grafik Tuvali Hazırlığı (1600 x 900)
$W = 1600
$H = 900
$bmp = New-Object System.Drawing.Bitmap($W, $H)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit

# Renkler
$bgBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(5, 9, 16))
$g.FillRectangle($bgBrush, 0, 0, $W, $H)

$greenBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(37, 243, 162))
$whiteBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::White)
$grayBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(148, 163, 184))
$purpleBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(197, 77, 255))
$scoreBoxBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(3, 7, 14))

$borderPen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(38, 50, 71), 2)
$greenPen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(37, 243, 162), 2)
$redPen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(255, 77, 109), 2)

# Fontlar
$fontTitle = New-Object System.Drawing.Font("Segoe UI", 26, [System.Drawing.FontStyle]::Bold)
$fontSub = New-Object System.Drawing.Font("Segoe UI", 12, [System.Drawing.FontStyle]::Bold)
$fontLarge = New-Object System.Drawing.Font("Segoe UI", 48, [System.Drawing.FontStyle]::Bold)
$fontRegular = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Bold)
$fontSmall = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Regular)

# Üst Başlık (Header)
$g.DrawRectangle($borderPen, 28, 22, 1544, 90)
$g.DrawString("GS", $fontTitle, $greenBrush, 50, 38)
$g.DrawString("Powered by GraveShift", $fontTitle, $whiteBrush, 110, 38)
$g.DrawString("EA SPORTS FC 27 / PRO CLUBS", $fontSub, $greenBrush, 115, 80)
$g.DrawString("PRO CLUBS HUB", $fontSub, $grayBrush, 1400, 50)

# Sol Panel: Skor ve Takım İstatistikleri
$g.DrawRectangle($greenPen, 28, 132, 592, 710)

# Sonuç Rozeti (LOSS / WIN)
$badgePen = if ($isWin) { $greenPen } elseif ($isLoss) { $redPen } else { $borderPen }
$badgeText = if ($isWin) { "GALIBIYET" } elseif ($isLoss) { "MAGLUBIYET" } else { "BERABERLIK" }
$badgeBrush = if ($isWin) { $greenBrush } elseif ($isLoss) { New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 77, 109)) } else { $grayBrush }
$g.DrawRectangle($badgePen, 58, 155, 532, 35)
$g.DrawString($badgeText, $fontRegular, $badgeBrush, 280, 162)

# Takım İsimleri & Skor
$myTeamName = if ($myTeam.details.name) { $myTeam.details.name } else { "ABRAKADABRA ESP" }
$oppTeamName = if ($oppTeam.details.name) { $oppTeam.details.name } else { "RAKIP TAKIM" }
$g.DrawString($myTeamName, $fontSub, $whiteBrush, 70, 240)
$g.DrawString("VS", $fontSub, $grayBrush, 310, 240)
$g.DrawString($oppTeamName, $fontSub, $whiteBrush, 430, 240)

$g.FillRectangle($scoreBoxBrush, 78, 290, 492, 80)
$g.DrawRectangle($borderPen, 78, 290, 492, 80)
$scoreText = "$myScore  -  $oppScore"
$g.DrawString($scoreText, $fontLarge, $whiteBrush, 230, 292)

# Takım İstatistikleri Tablosu
$g.DrawRectangle($borderPen, 58, 400, 532, 290)
$g.DrawString("TAKIM MAC ISTATISTIKLERI", $fontSub, $greenBrush, 210, 415)

$statsList = @(
    @{ Name = "SUTLAR"; My = [int]$myTeam.shots; Opp = [int]$oppTeam.shots },
    @{ Name = "PASLAR"; My = [int]$myTeam.passesmade; Opp = [int]$oppTeam.passesmade },
    @{ Name = "PAS ISABETI"; My = "$($myTeam.passingsuccessrate)%"; Opp = "$($oppTeam.passingsuccessrate)%" },
    @{ Name = "MUDAHALE"; My = [int]$myTeam.tacklesmade; Opp = [int]$oppTeam.tacklesmade }
)

$yPos = 460
foreach ($st in $statsList) {
    $g.DrawString($st.My, $fontRegular, $purpleBrush, 100, $yPos)
    $g.DrawString($st.Name, $fontSmall, $grayBrush, 270, $yPos)
    $g.DrawString($st.Opp, $fontRegular, $greenBrush, 500, $yPos)
    $yPos += 35
}

# Sağ Panel: Oyuncu Performans Listesi
$g.DrawRectangle($borderPen, 640, 132, 932, 710)
$g.DrawString("GELISMIS OYUNCU ISTATISTIKLERI", $fontTitle, $whiteBrush, 665, 155)
$g.DrawString("MAC PERFORMANSI  •  REYTİNGE GORE SIRALI", $fontSmall, $grayBrush, 668, 195)

$g.FillRectangle($scoreBoxBrush, 660, 225, 892, 35)
$g.DrawRectangle($borderPen, 660, 225, 892, 35)
$headers = "#", "OYUNCU", "MEV", "RYT", "G", "A", "INT", "SHT", "PASS", "TKL"
$xCoords = 675, 710, 880, 930, 980, 1020, 1060, 1110, 1170, 1310

for ($i = 0; $i -lt $headers.Count; $i++) {
    $colBrush = if ($headers[$i] -eq "OYUNCU") { $greenBrush } else { $grayBrush }
    $g.DrawString($headers[$i], $fontSmall, $colBrush, $xCoords[$i], 233)
}

# Oyuncuları Listele
$rawPlayers = $match.players.$ClubId.PSObject.Properties | ForEach-Object { $_.Value }
if ($rawPlayers) {
    $sortedPlayers = $rawPlayers | Sort-Object { [double]$_.rating } -Descending
    $rowY = 270
    $idx = 1
    foreach ($p in ($sortedPlayers | Select-Object -First 10)) {
        if ($idx -eq 1) {
            $highlightBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(40, 0, 255, 135))
            $g.FillRectangle($highlightBrush, 660, $rowY, 892, 32)
            $g.DrawRectangle($greenPen, 660, $rowY, 892, 32)
        } else {
            $rowPen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(30, 40, 60), 1)
            $g.DrawRectangle($rowPen, 660, $rowY, 892, 32)
        }

        $pName = if ($p.playername.Length -gt 15) { $p.playername.Substring(0, 15) } else { $p.playername }
        $pos = if ($p.pos) { $p.pos } else { "MIDF" }
        $rtg = [string]$p.rating
        $gCount = [string]$p.goals
        $aCount = [string]$p.assists
        $intCount = [string]$p.interceptions
        $shtCount = [string]$p.shots
        $passes = "$($p.passessuccessful)/$($p.passesmade)"
        $tkl = [string]$p.tacklesmade

        $rowValues = $idx, $pName, $pos, $rtg, $gCount, $aCount, $intCount, $shtCount, $passes, $tkl
        for ($k = 0; $k -lt $rowValues.Count; $k++) {
            $valBrush = if ($k -eq 3 -and [double]$rtg -ge 7.5) { $greenBrush } else { $whiteBrush }
            $g.DrawString([string]$rowValues[$k], $fontSmall, $valBrush, $xCoords[$k], ($rowY + 7))
        }

        $rowY += 38
        $idx++
    }
} else {
    $g.DrawString("Oyuncu detay verisi bulunamadi.", $fontRegular, $grayBrush, 700, 300)
}

# 3. Dosyayı Kaydet ve Ekranda Aç
$cleanMatchId = [string]$match.matchId -replace '[^a-zA-Z0-9]', ''
$outputPath = Join-Path $ReportsDir "match_$cleanMatchId.png"
$bmp.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)

$g.Dispose()
$bmp.Dispose()

Write-Host "`n[BASARILI] Mac raporu uretildi -> $outputPath" -ForegroundColor Green
Invoke-Item $outputPath