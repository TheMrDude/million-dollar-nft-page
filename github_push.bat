@echo off
cd "c:\Users\fourl\CascadeProjects\million-dollar-nft-page"

REM Set Git configuration
"C:\Program Files\Git\cmd\git.exe" config --global user.name "TheMrDude"
"C:\Program Files\Git\cmd\git.exe" config --global user.email "mrdudesblog@gmail.com"

REM Initialize repository
"C:\Program Files\Git\cmd\git.exe" init

REM Remove existing remote if it exists
"C:\Program Files\Git\cmd\git.exe" remote remove origin 2>nul

REM Add remote repository
"C:\Program Files\Git\cmd\git.exe" remote add origin https://github.com/TheMrDude/million-dollar-nft-page.git

REM Add all files
"C:\Program Files\Git\cmd\git.exe" add .

REM Commit changes
"C:\Program Files\Git\cmd\git.exe" commit -m "Initial commit: Million Dollar NFT Page"

REM Rename master to main and force push
"C:\Program Files\Git\cmd\git.exe" branch -M master main
"C:\Program Files\Git\cmd\git.exe" push -u -f origin main

echo Repository push complete!
