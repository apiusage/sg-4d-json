@echo off
cd /d C:\Users\bston\Dropbox\- SG Pools\sg-4d-json-main

echo ==========================
echo Setting up .gitignore
echo ==========================

(
echo 4d.json
echo *.xls
echo *.xlsx
echo *.xlsm
echo *.csv
) > .gitignore

echo ==========================
echo Removing tracked ignored files (safe step)
echo ==========================

git rm -r --cached 4d.json 2>nul
git rm -r --cached *.xls 2>nul
git rm -r --cached *.xlsx 2>nul
git rm -r --cached *.xlsm 2>nul
git rm -r --cached *.csv 2>nul

echo ==========================
echo Adding files
echo ==========================

git add .

echo ==========================
echo Committing changes
echo ==========================

git commit -m "Update repo with proper .gitignore"

echo ==========================
echo Pushing to GitHub
echo ==========================

git push origin main

echo ==========================
echo DONE
echo ==========================

pause