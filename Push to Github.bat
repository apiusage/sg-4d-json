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
echo Resetting git tracking (apply ignore)
echo ==========================

git rm -r --cached .

echo ==========================
echo Re-adding clean files only
echo ==========================

git add .

echo ==========================
echo Committing changes
echo ==========================

git commit -m "Force sync + clean repo"

echo ==========================
echo FORCE PUSH to GitHub (overwrite remote)
echo ==========================

git push origin main --force

echo ==========================
echo DONE
echo ==========================

pause