$ErrorActionPreference = "SilentlyContinue"

$root = if ($env:CLAUDE_PLUGIN_ROOT) {
    $env:CLAUDE_PLUGIN_ROOT
} elseif ($env:CODEX_PLUGIN_ROOT) {
    $env:CODEX_PLUGIN_ROOT
} else {
    Split-Path -Parent $PSScriptRoot
}
$dataDir = if ($env:PLUGIN_DATA) { $env:PLUGIN_DATA } else { $env:CLAUDE_PLUGIN_DATA }
$rulesPath = Join-Path $root "hooks/phrases.json"
$raw = [Console]::In.ReadToEnd()

try { $inputObject = $raw | ConvertFrom-Json } catch { exit 0 }
if (-not ($inputObject.prompt -is [string])) { exit 0 }
try { $rules = Get-Content $rulesPath -Raw | ConvertFrom-Json } catch { exit 0 }

$explicit = $inputObject.prompt.IndexOf("/hell", [StringComparison]::OrdinalIgnoreCase) -ge 0
$matched = $explicit
if (-not $explicit) {
    $autoDetect = $true
    $phrases = @($rules.phrases)
    $configPath = if ($dataDir) { Join-Path $dataDir "config.json" } else { $null }
    if ($configPath -and (Test-Path $configPath)) {
        try { $config = Get-Content $configPath -Raw | ConvertFrom-Json } catch { exit 0 }
        if ($null -ne $config.auto_detect) { $autoDetect = [bool]$config.auto_detect }
        $phrases += @($config.additional_phrases)
    }
    if (-not $autoDetect) { exit 0 }
    foreach ($phrase in $phrases) {
        if ($phrase -and $inputObject.prompt.IndexOf(
            [string]$phrase,
            [StringComparison]::OrdinalIgnoreCase
        ) -ge 0) {
            $matched = $true
            break
        }
    }
}

if (-not $matched) { exit 0 }

if (-not $explicit -and $dataDir -and [int]$rules.cooldown_seconds -gt 0) {
    New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
    $safeSession = [regex]::Replace([string]$inputObject.session_id, "[^A-Za-z0-9._-]", "")
    if (-not $safeSession) { $safeSession = "unknown" }
    $marker = Join-Path $dataDir "last-trigger-$safeSession"
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    if (Test-Path $marker) {
        try { $last = [long](Get-Content $marker -Raw) } catch { $last = 0 }
        if (($now - $last) -lt [int]$rules.cooldown_seconds) { exit 0 }
    }
    Set-Content -NoNewline -Path $marker -Value $now
}

if ($explicit) {
    Write-Output "Invoke the hell-report skill now. /hell authorizes local draft generation only. Continue the user's active task while drafting. Show the complete Issue title and body, then require a separate explicit confirmation before any GitHub submission."
} else {
    Write-Output "Assess whether your prior behavior contains a major mistake with concrete impact; this phrase match alone is not proof. Continue the user's active task and do not stall it for Hell Claude. If no major mistake occurred, do not mention a report. If one likely occurred, briefly ask whether the user wants a local Hell report draft while continuing work that does not depend on the answer. Only an unambiguous yes authorizes local draft generation; it does not authorize submission. After yes, invoke the hell-report skill, create the redacted draft, show the complete Issue title and body, and require a separate explicit confirmation before any GitHub or browser action."
}
exit 0
