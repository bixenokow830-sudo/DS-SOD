[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$sourceRoot = 'D:\OneDrive\Desktop\my paper'
$repoRoot = 'D:\OneDrive\Desktop\DS-SOD'
$stateDir = Join-Path $env:LOCALAPPDATA 'DS-SOD-AutoSync'
$statePath = Join-Path $stateDir 'state.json'
$logPath = Join-Path $stateDir 'auto-sync.log'
$lockPath = Join-Path $stateDir 'auto-sync.lock'

New-Item -ItemType Directory -Force -Path $stateDir | Out-Null

function Write-Log([string]$message) {
    $line = '{0} {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $message
    Add-Content -LiteralPath $logPath -Value $line -Encoding UTF8
}

$lock = $null
try {
    $lock = [System.IO.File]::Open($lockPath, 'OpenOrCreate', 'ReadWrite', 'None')
} catch {
    exit 0
}

try {
    $now = [DateTime]::UtcNow
    if (-not (Test-Path -LiteralPath $statePath)) {
        @{ last_scan_utc = $now.ToString('o') } | ConvertTo-Json |
            Set-Content -LiteralPath $statePath -Encoding UTF8
        Write-Log 'Initialized. Future changes will be synchronized.'
        exit 0
    }

    $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    $lastScan = [DateTime]::Parse($state.last_scan_utc).ToUniversalTime()
    $cutoff = $lastScan.AddMinutes(-2)
    $allowedExtensions = @('.md', '.json', '.html', '.htm', '.csv', '.tsv', '.png', '.jpg', '.jpeg', '.svg', '.pdf')
    $blockedName = '(?i)(^\.env|password|passwd|passphrase|apikey|api_key|access_key|private_key|credential|secret|id_rsa)'
    $blockedExtension = @('.pem', '.key', '.p12', '.pfx', '.keystore', '.jks', '.ppk', '.asc', '.gpg')
    $mappings = @(
        @{ Source = (Join-Path $sourceRoot 'paper'); Destination = (Join-Path $repoRoot 'paper') },
        @{ Source = (Join-Path $sourceRoot 'output\pdf'); Destination = (Join-Path $repoRoot 'output\pdf') }
    )

    $copied = New-Object System.Collections.Generic.List[string]
    foreach ($mapping in $mappings) {
        if (-not (Test-Path -LiteralPath $mapping.Source)) { continue }
        $files = Get-ChildItem -LiteralPath $mapping.Source -Recurse -File | Where-Object {
            $_.LastWriteTimeUtc -gt $cutoff -and
            $allowedExtensions -contains $_.Extension.ToLowerInvariant() -and
            $_.Name -notmatch $blockedName -and
            $blockedExtension -notcontains $_.Extension.ToLowerInvariant() -and
            $_.FullName -notmatch '(?i)[\\/](secrets|credentials)[\\/]'
        }
        foreach ($file in $files) {
            $relative = $file.FullName.Substring($mapping.Source.Length).TrimStart('\', '/')
            $destination = Join-Path $mapping.Destination $relative
            $destinationDir = Split-Path -Parent $destination
            New-Item -ItemType Directory -Force -Path $destinationDir | Out-Null
            Copy-Item -LiteralPath $file.FullName -Destination $destination -Force
            $copied.Add($file.FullName.Substring($sourceRoot.Length).TrimStart('\', '/'))
        }
    }

    $dirty = @(& git -C $repoRoot status --porcelain 2>$null)
    $ahead = & git -C $repoRoot rev-list --count 'origin/main..HEAD' 2>$null
    if ($copied.Count -gt 0 -or $dirty.Count -gt 0 -or ([int]$ahead -gt 0)) {
        $message = 'conversation artifact backup ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
        $output = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repoRoot 'init-backup.ps1') `
            -ProjectDir $repoRoot -Message $message 2>&1
        $code = $LASTEXITCODE
        $output | ForEach-Object { Write-Log ([string]$_) }
        if ($code -ne 0) {
            Write-Log "Backup failed with exit code $code. State was not advanced; the next run will retry."
            exit $code
        }
        Write-Log ("Synchronized {0} source file(s)." -f $copied.Count)
    } else {
        Write-Log 'No new artifacts.'
    }

    @{ last_scan_utc = $now.ToString('o') } | ConvertTo-Json |
        Set-Content -LiteralPath $statePath -Encoding UTF8
} catch {
    Write-Log ('ERROR: ' + $_.Exception.Message)
    exit 1
} finally {
    if ($lock) { $lock.Dispose() }
}
