@echo off
cd /d C:\Users\bston\Dropbox\- SG Pools\sg-4d-json-main

echo ==========================
echo 1. Update .gitignore (safe only)
echo ==========================

(
echo 4d.json
echo *.xls
echo *.xlsx
echo *.xlsm
echo *.csv
echo *.log
echo __pycache__/
echo *.pyc
echo .env
echo .DS_Store
) > .gitignore

echo ==========================
echo 2. Stage ONLY allowed changes
echo ==========================

git add .

echo ==========================
echo 3. Commit changes (if any)
echo ==========================

git commit -m "Auto update (safe push)" 2>nul

echo ==========================
echo 4. ALWAYS sync with GitHub first. Get the latest changes from GitHub and put my changes on top of them.
echo ==========================

git pull origin main --rebase

echo ==========================
echo 5. Push safely (NO FORCE)
echo ==========================

git push origin main

echo ==========================
echo DONE - SAFE SYNC COMPLETE
echo ==========================

pause