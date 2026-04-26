@echo off
cd /d "C:\Users\bston\Dropbox\- SG Pools\sg-4d-json-main"

:: Revert to previous commit
git reset --hard HEAD~1

:: Add and commit again
git add .
git commit -m "Updates"

:: Ensure branch is main
git branch -M main

:: Reset remote
git remote remove origin 2>nul
git remote add origin https://github.com/apiusage/sg-4d-json.git

:: Force push
git push -u origin main --force

pause