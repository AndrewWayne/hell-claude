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
$safeSession = [regex]::Replace([string]$inputObject.session_id, "[^A-Za-z0-9._-]", "")
if (-not $safeSession) { $safeSession = "unknown" }
$modelFile = if ($dataDir) { Join-Path $dataDir "runtime-model-$safeSession" } else { $null }

function Get-PublicModel([object]$Value) {
    if (-not ($Value -is [string])) { return "unknown" }
    if ($Value.Length -gt 128) { return "unknown" }
    if ($Value -notmatch '^[A-Za-z0-9][A-Za-z0-9._:/+\-]{0,127}$') { return "unknown" }
    return $Value
}

$hasModel = $null -ne $inputObject.PSObject.Properties["model"] -and
    $inputObject.model -is [string] -and $inputObject.model.Length -gt 0
$rawModel = if ($hasModel) { [string]$inputObject.model } else { "" }

if ($inputObject.hook_event_name -eq "SessionStart") {
    $runtimeModel = Get-PublicModel $rawModel
    if ($modelFile -and $runtimeModel -ne "unknown") {
        New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
        Set-Content -NoNewline -Encoding utf8 -Path $modelFile -Value $runtimeModel
    }
    exit 0
}

$eventName = [string]$inputObject.hook_event_name
if (-not $eventName -and $inputObject.prompt -is [string]) { $eventName = "UserPromptSubmit" }
if ($eventName -ne "UserPromptSubmit") { exit 0 }
if (-not ($inputObject.prompt -is [string])) { exit 0 }
try { $rules = Get-Content $rulesPath -Raw | ConvertFrom-Json } catch { exit 0 }

if ($hasModel) {
    $runtimeModel = Get-PublicModel $rawModel
} elseif ($modelFile -and (Test-Path $modelFile)) {
    try { $runtimeModel = Get-PublicModel (Get-Content $modelFile -Raw) } catch { $runtimeModel = "unknown" }
} else {
    $runtimeModel = "unknown"
}
$modelContext = "Runtime model for report: $runtimeModel. Use it exactly as the report Model; do not infer a different model."

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
    $marker = Join-Path $dataDir "last-trigger-$safeSession"
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    if (Test-Path $marker) {
        try { $last = [long](Get-Content $marker -Raw) } catch { $last = 0 }
        if (($now - $last) -lt [int]$rules.cooldown_seconds) { exit 0 }
    }
    Set-Content -NoNewline -Path $marker -Value $now
}

if ($explicit) {
    Write-Output "Invoke the hell-report skill now. $modelContext /hell authorizes local draft generation only. Continue the user's active task while drafting. Show the complete Issue title and body, ask whether to submit it now, and treat a direct affirmative response as submission authorization. No fixed phrase is required."
} else {
    Write-Output "Assess whether your prior behavior contains a major mistake with concrete impact; this phrase match alone is not proof. $modelContext Continue the user's active task and do not stall it for Hell Claude. If no major mistake occurred, do not mention a report. If one likely occurred, briefly ask whether the user wants a local Hell report draft while continuing work that does not depend on the answer. Only an unambiguous yes authorizes local draft generation; it does not authorize submission. After yes, invoke the hell-report skill, create the redacted draft, show the complete Issue title and body, ask whether to submit it now, and treat a direct affirmative response as submission authorization. No fixed phrase is required."
}
exit 0
