@echo off
cd /d C:\Users\bston\Dropbox\- SG Pools\sg-4d-json-main
git init
git add .
git status
git commit -m "Updates"
git remote set-url origin https://github.com/apiusage/sg-4d-json.git
git push origin main --force
pause
