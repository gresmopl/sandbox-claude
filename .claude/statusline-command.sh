#!/usr/bin/env bash
# Claude Code status line: 3 pure Unicode progress bars (no labels)
# Bar 1: token context usage (used_percentage of context window)
# Bar 2: cumulative cost vs $1.00 budget (estimated from total tokens)
# Bar 3: cache efficiency (cache_read_tokens / total input tokens)

BAR_WIDTH=10

# Unicode block fill chars: empty=░ quarter=▒ half=▓ full=█
render_bar() {
  local pct="$1"   # 0..100 (float ok)
  local width="$BAR_WIDTH"
  # clamp to 0..100
  pct=$(awk "BEGIN { p=$pct; if(p<0)p=0; if(p>100)p=100; printf \"%.4f\", p }")
  # filled cells (each cell = 1/width of 100%)
  # use quarter-block sub-cell precision: each cell has 4 sub-steps
  local steps=$(awk "BEGIN { printf \"%d\", ($pct / 100) * $width * 4 + 0.5 }")
  local full_cells=$(( steps / 4 ))
  local remainder=$(( steps % 4 ))
  local empty_cells=$(( width - full_cells - (remainder > 0 ? 1 : 0) ))

  local bar=""
  local i
  for (( i=0; i<full_cells; i++ )); do bar="${bar}█"; done
  if (( remainder > 0 )); then
    case $remainder in
      1) bar="${bar}▒" ;;
      2) bar="${bar}▓" ;;
      3) bar="${bar}▓" ;;
    esac
    (( empty_cells = width - full_cells - 1 ))
  else
    (( empty_cells = width - full_cells ))
  fi
  for (( i=0; i<empty_cells; i++ )); do bar="${bar}░"; done
  printf "%s" "$bar"
}

input=$(cat)

# --- Bar 1: context window usage ---
ctx_pct=$(echo "$input" | jq -r '.context_window.used_percentage // 0')
[ "$ctx_pct" = "null" ] && ctx_pct=0

# --- Bar 2: cost estimate vs $1.00 budget ---
# claude-sonnet-4-x pricing (approximate):
#   input:  $3.00 / 1M tokens  → $0.000003 per token
#   output: $15.00 / 1M tokens → $0.000015 per token
#   cache_write: $3.75/1M, cache_read: $0.30/1M
total_input=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
total_output=$(echo "$input" | jq -r '.context_window.total_output_tokens // 0')
cache_read=$(echo "$input" | jq -r '
  if .context_window.current_usage != null then
    .context_window.current_usage.cache_read_input_tokens // 0
  else 0 end')
cache_write=$(echo "$input" | jq -r '
  if .context_window.current_usage != null then
    .context_window.current_usage.cache_creation_input_tokens // 0
  else 0 end')

# cost in dollars (budget = $1.00)
cost_pct=$(awk "BEGIN {
  inp   = $total_input  * 0.000003
  out   = $total_output * 0.000015
  cr    = $cache_read   * 0.0000003
  cw    = $cache_write  * 0.00000375
  total = inp + out + cr + cw
  pct   = total / 1.00 * 100
  if (pct > 100) pct = 100
  printf \"%.4f\", pct
}")

# --- Bar 3: cache efficiency (cache_read / (total_input + cache_read)) ---
cache_eff_pct=$(awk "BEGIN {
  cr  = $cache_read
  inp = $total_input
  denom = inp + cr
  if (denom == 0) { printf \"0\"; exit }
  printf \"%.4f\", (cr / denom) * 100
}")

printf "%s\n%s\n%s\n" \
  "$(render_bar "$ctx_pct")" \
  "$(render_bar "$cost_pct")" \
  "$(render_bar "$cache_eff_pct")"
