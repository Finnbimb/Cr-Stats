#!/bin/bash
set -e
cd /root/Cr-Stats
git pull

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt -q
pkill -f "bot.py" || true
nohup python -u bot.py > bot.log 2>&1 &
systemctl restart crstats-backend
cd ..

# Frontend
cd frontend
npm install --silent
npm run build
cp -r dist/* /var/www/crstats/
cd ..

echo "Bot, Backend und Frontend neugestartet"
