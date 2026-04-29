@echo off
cd /d C:\Users\bston\Dropbox\- SG Pools\sg-4d-json-main

echo ==========================
echo Writing .gitignore
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
echo Applying gitignore (reset cache)
echo ==========================

git rm -r --cached .

echo ==========================
echo Re-adding clean files only
echo ==========================

git add .

echo ==========================
echo Committing changes
echo ==========================

git commit -m "Clean repo + improved .gitignore"

echo ==========================
echo Pushing
echo ==========================

git push origin main

pause