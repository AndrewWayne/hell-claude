#!/usr/bin/env bash

# This Hook must fail open. It never blocks the user's prompt.
set -u

script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
root="${CLAUDE_PLUGIN_ROOT:-${CODEX_PLUGIN_ROOT:-$(dirname "$script_dir")}}"
data_dir="${PLUGIN_DATA:-${CLAUDE_PLUGIN_DATA:-}}"
rules="$root/hooks/phrases.json"
input="$(cat)"

command -v jq >/dev/null 2>&1 || exit 0
[ -f "$rules" ] || exit 0
prompt="$(printf '%s' "$input" | jq -er '.prompt | strings' 2>/dev/null)" || exit 0
session="$(printf '%s' "$input" | jq -r '.session_id // "unknown"' 2>/dev/null)" || exit 0

if printf '%s' "$prompt" | grep -Fqi -- '/hell'; then
  explicit=true
  matched=true
else
  explicit=false
  auto_detect=true
  phrases="$(jq -r '.phrases[]' "$rules" 2>/dev/null)" || exit 0
  if [ -n "$data_dir" ] && [ -f "$data_dir/config.json" ]; then
    auto_detect="$(jq -r 'if has("auto_detect") then .auto_detect else true end' "$data_dir/config.json" 2>/dev/null)" || exit 0
    custom="$(jq -r '.additional_phrases[]?' "$data_dir/config.json" 2>/dev/null)" || exit 0
    phrases="$phrases
$custom"
  fi
  [ "$auto_detect" = true ] || exit 0
  matched=false
  while IFS= read -r phrase; do
    if [ -n "$phrase" ] && printf '%s' "$prompt" | grep -Fqi -- "$phrase"; then
      matched=true
      break
    fi
  done <<EOF
$phrases
EOF
fi

[ "$matched" = true ] || exit 0

if [ "$explicit" = false ] && [ -n "$data_dir" ]; then
  cooldown="$(jq -r '.cooldown_seconds // 0' "$rules" 2>/dev/null)" || exit 0
  if [ "$cooldown" -gt 0 ] 2>/dev/null; then
    mkdir -p "$data_dir" 2>/dev/null || true
    safe_session="$(printf '%s' "$session" | tr -cd 'A-Za-z0-9._-')"
    marker="$data_dir/last-trigger-${safe_session:-unknown}"
    now="$(date +%s)"
    if [ -f "$marker" ]; then
      last="$(cat "$marker" 2>/dev/null || printf 0)"
      [ $((now - last)) -lt "$cooldown" ] 2>/dev/null && exit 0
    fi
    printf '%s' "$now" >"$marker" 2>/dev/null || true
  fi
fi

printf '%s\n' 'Invoke the hell-report skill now. Build only a local, redacted draft. Show the complete payload and require explicit confirmation before any GitHub submission.'
exit 0
