#!/data/data/com.termux/files/usr/bin/bash
# ─────────────────────────────────────────────────────────────────
# VoidDesk Bootstrap — Termux / Proot / Android
# Sets up dependencies and launches the VoidDesk server
# ─────────────────────────────────────────────────────────────────

set -e

BOLD="\e[1m"
CYAN="\e[36m"
GREEN="\e[32m"
RED="\e[31m"
YELLOW="\e[33m"
RESET="\e[0m"

log()  { echo -e "${CYAN}[*]${RESET} $*"; }
ok()   { echo -e "${GREEN}[✓]${RESET} $*"; }
warn() { echo -e "${YELLOW}[!]${RESET} $*"; }
err()  { echo -e "${RED}[✗]${RESET} $*"; exit 1; }

echo -e "${BOLD}${CYAN}"
echo "  ██╗   ██╗ ██████╗ ██╗██████╗ ██████╗ ███████╗███████╗██╗  ██╗"
echo "  ██║   ██║██╔═══██╗██║██╔══██╗██╔══██╗██╔════╝██╔════╝██║ ██╔╝"
echo "  ██║   ██║██║   ██║██║██║  ██║██║  ██║█████╗  ███████╗█████╔╝ "
echo "  ╚██╗ ██╔╝██║   ██║██║██║  ██║██║  ██║██╔══╝  ╚════██║██╔═██╗ "
echo "   ╚████╔╝ ╚██████╔╝██║██████╔╝██████╔╝███████╗███████║██║  ██╗"
echo "    ╚═══╝   ╚═════╝ ╚═╝╚═════╝ ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝"
echo -e "${RESET}"
echo -e "  ${BOLD}Termux / Proot Bootstrap${RESET}"
echo ""

# ── Detect environment ────────────────────────────────────────────
IS_TERMUX=false
IS_PROOT=false

if [ -d "/data/data/com.termux" ]; then
  IS_TERMUX=true
  log "Environment: Termux (Android)"
elif [ -f "/proc/1/cgroup" ] && grep -q "docker\|lxc\|proot" /proc/1/cgroup 2>/dev/null; then
  IS_PROOT=true
  log "Environment: Container / proot"
else
  log "Environment: Standard Linux"
fi

# ── Install system packages ───────────────────────────────────────
if $IS_TERMUX; then
  log "Installing Termux packages..."
  pkg update -y -q
  pkg install -y python ffmpeg xdotool x11-repo 2>/dev/null || true
  pkg install -y xorg-xvfb xorg-xauth 2>/dev/null || true
  ok "Termux packages installed"
else
  log "Checking system packages..."
  MISSING=()
  for bin in ffmpeg python3 xdotool; do
    command -v "$bin" &>/dev/null || MISSING+=("$bin")
  done
  if [ ${#MISSING[@]} -gt 0 ]; then
    warn "Missing: ${MISSING[*]}"
    log "Attempting apt install..."
    sudo apt-get install -y ffmpeg python3 python3-pip xdotool xvfb 2>/dev/null || \
      err "Please install: ${MISSING[*]}"
  fi
  ok "System packages OK"
fi

# ── Python deps ───────────────────────────────────────────────────
log "Installing Python dependencies..."
pip install --quiet --upgrade websockets 2>/dev/null || \
  pip3 install --quiet --upgrade websockets

# Optional: evdev for uinput support
pip install --quiet evdev 2>/dev/null && ok "evdev installed (uinput support enabled)" || \
  warn "evdev not installed — uinput input injection unavailable (X11 xdotool will still work)"

ok "Python dependencies installed"

# ── Display setup ─────────────────────────────────────────────────
DISPLAY_NUM="${VOIDDESK_DISPLAY:-:1}"
RESOLUTION="${VOIDDESK_RES:-1280x720}"
PORT="${VOIDDESK_PORT:-8765}"
CODEC="${VOIDDESK_CODEC:-h264}"

if [ -z "$DISPLAY" ]; then
  log "No active display — starting Xvfb on $DISPLAY_NUM..."
  W=$(echo "$RESOLUTION" | cut -dx -f1)
  H=$(echo "$RESOLUTION" | cut -dx -f2)
  Xvfb "$DISPLAY_NUM" -screen 0 "${W}x${H}x24" -ac &
  XVFB_PID=$!
  export DISPLAY="$DISPLAY_NUM"
  sleep 1.5
  ok "Xvfb running (PID $XVFB_PID) on $DISPLAY"
else
  ok "Using existing display: $DISPLAY"
fi

# ── Optional: launch a desktop environment in Xvfb ───────────────
if [ "${VOIDDESK_DE:-}" != "" ]; then
  log "Launching desktop: $VOIDDESK_DE"
  case "$VOIDDESK_DE" in
    openbox) openbox-session &>/dev/null & ;;
    xfce)    startxfce4 &>/dev/null & ;;
    lxde)    startlxde &>/dev/null & ;;
    *)       $VOIDDESK_DE &>/dev/null & ;;
  esac
  sleep 2
fi

# ── Launch VoidDesk ───────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
cd "$PROJECT_DIR"

echo ""
log "Starting VoidDesk server..."
log "  Host    : 0.0.0.0:$PORT"
log "  Display : $DISPLAY"
log "  Res     : $RESOLUTION"
log "  Codec   : $CODEC"
echo ""
ok "Open browser → http://localhost:$PORT/../client/index.html"
echo ""

python3 -m server.main \
  --host 0.0.0.0 \
  --port "$PORT" \
  --display "$DISPLAY" \
  --res "$RESOLUTION" \
  --codec "$CODEC" \
  --backend auto \
  "$@"
