@echo off

cd /d C:\Users\bston\Dropbox\- SG Pools\sg-4d-json-main

echo === Set remote (GitHub repo) ===
git remote set-url origin https://github.com/apiusage/sg-4d-json.git

echo === Add all changes ===
git add .

echo === Commit changes ===
git commit -m "Force update" 2>nul

echo === Resolve any rebase state (if stuck) ===
git rebase --abort 2>nul

echo === Force push to GitHub ===
git push origin main --force

echo === Done ===
pause