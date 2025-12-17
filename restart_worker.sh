#!/usr/bin/env bash
set -euo pipefail

# Перезапуск воркера и быстрый статус

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

if [ -f ".env" ]; then
  set -a
  source ".env"
  set +a
fi

PORT="${FLASK_PORT:-3000}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 не найден в PATH" >&2
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo ".venv не найден. Создайте окружение и установите зависимости: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt" >&2
  exit 1
fi

source .venv/bin/activate

mkdir -p logs

echo "Останавливаю предыдущий воркер (если был)..."
pkill -f import_worker.py >/dev/null 2>&1 || true
sleep 1

echo "Запускаю новый воркер..."
nohup python3 import_worker.py > logs/worker.out 2>&1 &
NEW_PID=$!

sleep 2
echo "Воркера PID: ${NEW_PID}"

echo "--- health ---"
curl -s "http://localhost:${PORT}/health" || true
echo

echo "--- status ---"
curl -s "http://localhost:${PORT}/status" || true
echo

echo "--- logs/import.log (tail) ---"
tail -n 40 logs/import.log 2>/dev/null || true

echo "--- logs/worker.out (tail) ---"
tail -n 40 logs/worker.out 2>/dev/null || true

