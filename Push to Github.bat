@echo off

cd /d C:\Users\bston\Dropbox\- SG Pools\sg-4d-json-main

echo === Ensure remote is correct ===
git remote set-url origin https://github.com/apiusage/sg-4d-json.git

echo === Stage changes (respects .gitignore) ===
git add .

echo === Commit changes ===
git commit -m "update" 2>nul

echo === Sync with remote (prevents overwrite/deletion) ===
git fetch origin
git merge origin/main --no-edit

echo === Push safely (NO FORCE) ===
git push origin main

echo === Done ===
pause