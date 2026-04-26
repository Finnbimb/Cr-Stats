#!/bin/bash
cd /root/Cr-Stats
git pull
cd backend
source venv/bin/activate
pip install -r requirements.txt -q
pkill -f "bot.py" || true
nohup python -u bot.py > bot.log 2>&1 &
systemctl restart crstats-backend
echo "Bot und Backend neugestartet"
