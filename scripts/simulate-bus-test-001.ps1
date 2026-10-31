param(
    [Parameter(Mandatory = $true)]
    [array]$Points,

    [Parameter(Mandatory = $true)]
    [string]$ApiUrl,

    [Parameter(Mandatory = $true)]
    [hashtable]$Headers,

    [int]$IntervalSeconds = 20
)

$ErrorActionPreference = "Stop"

if ($Points.Count -lt 2) {
    throw "Le trajet doit contenir au moins deux points."
}

if ($IntervalSeconds -lt 1) {
    throw "IntervalSeconds doit etre superieur ou egal a 1."
}

Write-Host "====================================" -ForegroundColor Cyan
Write-Host " SIMULATEUR GPS - BUS-TEST-001" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

Write-Host "Points du trajet : $($Points.Count)"
Write-Host "Intervalle : $IntervalSeconds secondes"
Write-Host "Arret : CTRL+C"

$Numero = 0

while ($true) {

    foreach ($Point in $Points) {

        $Numero++

        $Body = @{
            latitude    = [double]$Point.latitude
            longitude   = [double]$Point.longitude
            speed       = 25
            recorded_at = (Get-Date).ToUniversalTime().ToString("o")
        } | ConvertTo-Json -Compress

        try {
            $null = Invoke-RestMethod `
                -Uri "$($ApiUrl.TrimEnd('/'))/gps/v2/devices/positions" `
                -Method POST `
                -Headers $Headers `
                -ContentType "application/json" `
                -Body $Body `
                -ErrorAction Stop

            Write-Host (
                "[{0}] Position {1}/{2} envoyee | LAT={3} | LON={4}" -f `
                (Get-Date -Format "HH:mm:ss"),
                (($Numero - 1) % $Points.Count + 1),
                $Points.Count,
                $Point.latitude,
                $Point.longitude
            ) -ForegroundColor Green
        }
        catch {
            Write-Host (
                "[{0}] Echec d'envoi GPS (position {1}/{2})." -f `
                (Get-Date -Format "HH:mm:ss"),
                (($Numero - 1) % $Points.Count + 1),
                $Points.Count
            ) -ForegroundColor Red
        }

        Start-Sleep -Seconds $IntervalSeconds
    }
}
