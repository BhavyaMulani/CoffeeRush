#!/bin/sh
cd "$(dirname "$0")" || exit 1
export COFFEE_RUSH_PORT=18765
python3 server.py &
GAME_PID=$!
trap 'kill "$GAME_PID" 2>/dev/null' EXIT INT TERM
sleep 2
if command -v open >/dev/null 2>&1; then
  open http://127.0.0.1:18765
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open http://127.0.0.1:18765 >/dev/null 2>&1 &
else
  echo "Open http://127.0.0.1:18765 in your browser"
fi
wait "$GAME_PID"
