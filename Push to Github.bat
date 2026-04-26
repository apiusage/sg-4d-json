@echo off
cd /d C:\Users\bston\Dropbox\- SG Pools\sg-4d-json-main

:: create/overwrite .gitignore
echo 4d.json>.gitignore
echo *.xls>>.gitignore
echo *.xlsx>>.gitignore
echo *.xlsm>>.gitignore
echo *.csv>>.gitignore

git init
git rm --cached 4d.json *.xls *.xlsx *.xlsm *.csv 2>nul
git add .
git commit -m "Updates"
git remote set-url origin https://github.com/apiusage/sg-4d-json.git 2>nul
git push origin main --force

pause