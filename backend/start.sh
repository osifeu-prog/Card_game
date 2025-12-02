#!/bin/bash

# Script להרצת האפליקציה
# Railway יקבע את PORT אוטומטית

echo "Starting Telegram Bot Application..."
echo "Port: ${PORT:-8000}"

# הרצת האפליקציה
exec python main.py
