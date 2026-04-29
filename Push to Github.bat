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
) > .gitignore

echo ==========================
echo Removing already tracked ignored files
echo ==========================

git rm -r --cached . 2>nul

echo ==========================
echo Re-adding clean files only
echo ==========================

git add .

echo ==========================
echo Committing changes
echo ==========================

git commit -m "Clean repo + fix .gitignore"

echo ==========================
echo Pushing
echo ==========================

git push origin main

pause