#!/bin/bash
FILE="$1"
CAPTION="${2:-Mensaje de Rex}"
TOKEN="${TELEGRAM_BOT_TOKEN:-}"
CHAT_ID="${TELEGRAM_CHAT_ID:-6571581166}"

if [[ -z "$TOKEN" ]]; then
  echo "TELEGRAM_BOT_TOKEN no definido"
  exit 1
fi

curl -X POST "https://api.telegram.org/bot$TOKEN/sendAudio" \
  -F "chat_id=$CHAT_ID" \
  -F "audio=@$FILE" \
  -F "caption=$CAPTION"
