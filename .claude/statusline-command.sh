#!/usr/bin/env bash
# Claude Code status line, left to right: context window usage, Claude.ai
# rate-limit usage (5h / 7d), model + effort, output style, directory, and
# git branch/worktree. Compact and colored.

input=$(cat)

RESET=$'\033[0m'
CYAN=$'\033[36m'
MAGENTA=$'\033[35m'
BLUE=$'\033[34m'
GRAY=$'\033[90m'
GREEN=$'\033[32m'
YELLOW=$'\033[33m'
RED=$'\033[31m'

# green < 50%, yellow < 80%, red >= 80%
pct_color() {
  local p
  p=$(printf '%.0f' "$1" 2>/dev/null || echo 0)
  if [ "$p" -ge 80 ]; then echo "$RED"
  elif [ "$p" -ge 50 ]; then echo "$YELLOW"
  else echo "$GREEN"
  fi
}

dir=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // empty')
model=$(echo "$input" | jq -r '.model.display_name // "?"')
effort=$(echo "$input" | jq -r '.effort.level // empty')
style=$(echo "$input" | jq -r '.output_style.name // empty')

ctx_used=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
five_used=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
five_resets=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
week_used=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
week_resets=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // empty')

now=$(date +%s)

# format remaining seconds until an epoch as "Xd Yh" / "Xh Ym" / "Xm"
fmt_remaining() {
  local resets_at="$1" remaining
  remaining=$(( resets_at - now ))
  if [ "$remaining" -le 0 ]; then
    echo "now"
    return
  fi
  local days=$(( remaining / 86400 ))
  local hours=$(( (remaining % 86400) / 3600 ))
  local mins=$(( (remaining % 3600) / 60 ))
  if [ "$days" -gt 0 ]; then
    printf '%dd%dh' "$days" "$hours"
  elif [ "$hours" -gt 0 ]; then
    printf '%dh%dm' "$hours" "$mins"
  else
    printf '%dm' "$mins"
  fi
}

branch=""
worktree=""
if [ -n "$dir" ] && git -C "$dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  branch=$(git -C "$dir" symbolic-ref --short HEAD 2>/dev/null \
    || git -C "$dir" rev-parse --short HEAD 2>/dev/null)
  git_dir=$(git -C "$dir" rev-parse --git-dir 2>/dev/null)
  common_dir=$(git -C "$dir" rev-parse --git-common-dir 2>/dev/null)
  if [ "$git_dir" != "$common_dir" ]; then
    worktree=$(basename "$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null)")
  fi
fi

parts=()

if [ -n "$ctx_used" ]; then
  parts+=("${GRAY}ctx${RESET} ${GREEN}$(printf '%.0f' "$ctx_used")%${RESET}")
fi

rl=""
if [ -n "$five_used" ]; then
  rl="${GRAY}$(fmt_remaining "$five_resets")${RESET} $(pct_color "$five_used")$(printf '%.0f' "$five_used")%${RESET}"
fi
if [ -n "$week_used" ]; then
  [ -n "$rl" ] && rl="${rl} ${GRAY}·${RESET} "
  rl="${rl}${GRAY}$(fmt_remaining "$week_resets")${RESET} $(pct_color "$week_used")$(printf '%.0f' "$week_used")%${RESET}"
fi
[ -n "$rl" ] && parts+=("$rl")

if [ -n "$effort" ]; then
  parts+=("${CYAN}${model}${RESET}${GRAY}·${RESET}${MAGENTA}${effort}${RESET}")
else
  parts+=("${CYAN}${model}${RESET}")
fi

if [ -n "$style" ]; then
  parts+=("${BLUE}${style}${RESET}")
fi

if [ -n "$dir" ]; then
  parts+=("${YELLOW}📁 $(basename "$dir")${RESET}")
fi

if [ -n "$branch" ]; then
  g="${GREEN}⎇ ${branch}${RESET}"
  [ -n "$worktree" ] && g="${g} ${MAGENTA}⑂ ${worktree}${RESET}"
  parts+=("$g")
fi

sep=" ${GRAY}│${RESET} "
out=""
for p in "${parts[@]}"; do
  if [ -z "$out" ]; then
    out="$p"
  else
    out="${out}${sep}${p}"
  fi
done

printf '%s' "$out"
