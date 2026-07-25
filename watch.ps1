# ─────────────────────────────────────────────────────────────
# watch.ps1 - Skill Library File Watcher (bidirectional sync)
#
# Watches all three tool directories + the library for changes
# and automatically runs pull/push when files are added or modified.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File watch.ps1
#   powershell -ExecutionPolicy Bypass -File watch.ps1 -Debounce 5
#
# To run at startup, create a shortcut in shell:startup or use
# Task Scheduler with: powershell -WindowStyle Hidden -File watch.ps1
# ─────────────────────────────────────────────────────────────

param(
    [int]$Debounce = 3  # seconds to wait after last change before syncing
)

$LibraryDir = "$env:USERPROFILE\skill-library"
$CodexDir   = "$env:USERPROFILE\.codex\skills"
$ClaudeDir  = "$env:USERPROFILE\.claude\commands"
$FactoryDir = "$env:USERPROFILE\.factory\droids"
$LogFile    = "$LibraryDir\watcher.log"

# ── Shared state (accessible from event handlers) ──────────

$Global:SyncQueue = [System.Collections.ArrayList]::Synchronized([System.Collections.ArrayList]::new())

# ── Logging ─────────────────────────────────────────────────

function Write-Log([string]$Message) {
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -ErrorAction SilentlyContinue
}

# ── Find Git Bash ───────────────────────────────────────────

$BashExe = $null
foreach ($p in @(
    "$env:ProgramFiles\Git\bin\bash.exe",
    "${env:ProgramFiles(x86)}\Git\bin\bash.exe",
    "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe"
)) {
    if (Test-Path $p) { $BashExe = $p; break }
}
if (-not $BashExe) {
    $found = Get-Command bash -ErrorAction SilentlyContinue
    if ($found) { $BashExe = $found.Source }
}
if (-not $BashExe) {
    Write-Log "ERROR - Could not find bash.exe (Git Bash). Cannot run sync."
    exit 1
}

# ── Run sync.sh ─────────────────────────────────────────────

function Invoke-Sync([string]$Mode) {
    $libPath = $LibraryDir -replace '\\', '/'
    Write-Log "SYNC - Running $Mode..."

    try {
        if ($Mode -eq "both" -or $Mode -eq "pull") {
            $out = & $BashExe -c "cd '$libPath' && bash sync.sh pull all 2>&1"
            foreach ($line in $out) {
                $clean = $line -replace '\x1b\[[0-9;]*m', ''
                if ($clean -match '\[IMPORT\]') { Write-Log "  $clean" }
            }
        }
        if ($Mode -eq "both" -or $Mode -eq "push") {
            $out = & $BashExe -c "cd '$libPath' && bash sync.sh push all 2>&1"
            foreach ($line in $out) {
                $clean = $line -replace '\x1b\[[0-9;]*m', ''
                if ($clean -match '\[NEW\]|\[GEN\]') { Write-Log "  $clean" }
            }
        }
        Write-Log "SYNC - $Mode complete"
    }
    catch {
        Write-Log "SYNC ERROR - $($_.Exception.Message)"
    }
}

# ── Create watchers ─────────────────────────────────────────

function New-SkillWatcher([string]$WatchPath, [string]$Label, [string]$SyncMode,
                          [string]$Filter = "*", [bool]$IncludeSubdirs = $true) {

    if (-not (Test-Path $WatchPath)) {
        Write-Log "WARN - $Label path missing, skipped"
        return $null
    }

    $w = New-Object System.IO.FileSystemWatcher
    $w.Path = $WatchPath
    $w.Filter = $Filter
    $w.IncludeSubdirectories = $IncludeSubdirs
    $w.NotifyFilter = [System.IO.NotifyFilters]::FileName -bor
                      [System.IO.NotifyFilters]::DirectoryName -bor
                      [System.IO.NotifyFilters]::LastWrite
    $w.EnableRaisingEvents = $true

    # Event handler just enqueues to the global sync queue
    # Bake label and mode into the scriptblock as string literals
    $sb = [scriptblock]::Create(@"
        `$n = `$Event.SourceEventArgs.Name
        `$p = `$Event.SourceEventArgs.FullPath
        # Skip our own artifacts and internal directories
        if (`$n -match '(watcher\.log|catalog\.json|\.git[\\/])') { return }
        # Skip Codex .system internal skills
        if (`$n -match '^\.system[\\/]') { return }
        # Skip auto-generated files in tool dirs
        if (`$p -and (Test-Path `$p -ErrorAction SilentlyContinue) -and -not (Test-Path `$p -PathType Container -ErrorAction SilentlyContinue)) {
            `$h = Get-Content `$p -TotalCount 1 -ErrorAction SilentlyContinue
            if (`$h -match 'AUTO-GENERATED from skill-library') { return }
        }
        `$Global:SyncQueue.Add(@{ Label = '$Label'; Mode = '$SyncMode'; File = `$n; Time = [datetime]::Now }) | Out-Null
"@)

    Register-ObjectEvent $w Created -Action $sb | Out-Null
    Register-ObjectEvent $w Changed -Action $sb | Out-Null
    Register-ObjectEvent $w Renamed -Action $sb | Out-Null
    Register-ObjectEvent $w Deleted -Action $sb | Out-Null

    Write-Log "Watching $Label ($WatchPath)"
    return $w
}

# ── Start watchers ──────────────────────────────────────────

Write-Log "========================================="
Write-Log "Skill Library Watcher starting"
Write-Log "  Debounce ${Debounce}s"
Write-Log "========================================="

$watchers = @(
    (New-SkillWatcher $LibraryDir "Library" "push"),
    (New-SkillWatcher $CodexDir   "Codex"   "both"),
    (New-SkillWatcher $ClaudeDir  "Claude"  "pull"  "*.md" $false),
    (New-SkillWatcher $FactoryDir "Factory" "pull"  "*.md" $false)
) | Where-Object { $_ -ne $null }

Write-Log "Watcher running. Press Ctrl+C to stop."

# ── Main loop: drain queue, debounce, sync ──────────────────

$lastChangeTime = [datetime]::MinValue
$pendingMode    = $null
$lastSyncTime   = [datetime]::MinValue

try {
    while ($true) {
        Start-Sleep -Milliseconds 500

        # Drain the queue
        while ($Global:SyncQueue.Count -gt 0) {
            $item = $Global:SyncQueue[0]
            $Global:SyncQueue.RemoveAt(0)

            $label = $item.Label
            $mode  = $item.Mode
            $file  = $item.File

            Write-Log "$label changed - $file"
            $lastChangeTime = [datetime]::Now

            # Merge modes
            if ($pendingMode -eq "both" -or ($pendingMode -and $pendingMode -ne $mode)) {
                $pendingMode = "both"
            } else {
                $pendingMode = $mode
            }
        }

        # Fire sync after debounce period with no new changes
        if ($pendingMode -and ([datetime]::Now - $lastChangeTime).TotalSeconds -ge $Debounce) {
            # Rate limit: at least 2s between syncs
            if (([datetime]::Now - $lastSyncTime).TotalSeconds -ge 2) {
                Invoke-Sync $pendingMode
                $lastSyncTime = [datetime]::Now
                $pendingMode  = $null
            }
        }
    }
}
finally {
    Write-Log "Watcher stopping..."
    foreach ($w in $watchers) {
        if ($w) { $w.EnableRaisingEvents = $false; $w.Dispose() }
    }
    Write-Log "Watcher stopped."
}
