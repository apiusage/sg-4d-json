@echo off
cd /d "C:\Users\bston\Dropbox\- SG Pools\sg-4d-json-main"

:: Reset to before 9PM yesterday
git reset --hard $(git rev-list -1 --before="2026-04-26 21:00" main)

:: Push
git push origin main --force

pause