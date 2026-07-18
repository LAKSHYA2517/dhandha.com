#!/bin/bash
# Starts (or confirms) everything needed for the WhatsApp bot to work locally:
# MongoDB, the FastAPI backend, and the ngrok tunnel Meta needs to reach it.
#
# Usage: ./start_whatsapp_dev.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "== MongoDB =="
if nc -z localhost 27017 2>/dev/null; then
  echo "  already running"
else
  brew services start mongodb-community@7.0
  sleep 2
fi

echo "== Backend (FastAPI) =="
if curl -s -o /dev/null -w "" http://localhost:8000/api/health 2>/dev/null; then
  echo "  already running"
else
  source venv/bin/activate
  nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/fastapi.log 2>&1 &
  echo "  started (pid $!)"
  sleep 3
fi
curl -s http://localhost:8000/api/health && echo

echo "== ngrok tunnel =="
if curl -s http://localhost:4040/api/tunnels >/dev/null 2>&1; then
  echo "  already running"
else
  nohup ngrok http 8000 --log=stdout > /tmp/ngrok.log 2>&1 &
  echo "  started (pid $!)"
  sleep 4
fi

NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys,json;print(json.load(sys.stdin)['tunnels'][0]['public_url'])")
echo "  public URL: $NGROK_URL"

echo
echo "== Webhook handshake test =="
VERIFY_TOKEN=$(grep "WHATSAPP_VERIFY_TOKEN=" .env | cut -d= -f2-)
RESPONSE=$(curl -s "$NGROK_URL/api/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=$VERIFY_TOKEN&hub.challenge=check123")
if [ "$RESPONSE" = "check123" ]; then
  echo "  OK — webhook responding correctly"
else
  echo "  FAILED — got: $RESPONSE"
fi

echo
echo "== Meta dashboard webhook URL (should match the one above) =="
ACCESS_TOKEN=$(grep "WHATSAPP_ACCESS_TOKEN=" .env | cut -d= -f2-)
if [ -n "$ACCESS_TOKEN" ]; then
  curl -s "https://graph.facebook.com/v20.0/4585153595073433/phone_numbers?access_token=$ACCESS_TOKEN" | \
    python3 -c "
import sys, json
data = json.load(sys.stdin)
for p in data.get('data', []):
    print(' ', p['display_phone_number'], '->', p.get('webhook_configuration', {}).get('application'))
" 2>/dev/null || echo "  (couldn't fetch — check ACCESS_TOKEN)"
fi

echo
echo "Done. If the ngrok URL above ever differs from what's saved on the Meta"
echo "dashboard's Configure Webhooks page, paste the new one in there and click"
echo "'Verify and save'."
