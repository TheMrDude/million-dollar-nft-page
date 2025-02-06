@echo off
cd "c:\Users\fourl\CascadeProjects\million-dollar-nft-page"

REM Set Git configuration
"C:\Program Files\Git\cmd\git.exe" config --global user.name "TheMrDude"
"C:\Program Files\Git\cmd\git.exe" config --global user.email "mrdudesblog@gmail.com"

REM Initialize repository
"C:\Program Files\Git\cmd\git.exe" init

REM Add all files
"C:\Program Files\Git\cmd\git.exe" add .

REM Commit changes
"C:\Program Files\Git\cmd\git.exe" commit -m "Initial commit: Million Dollar NFT Page"

REM Add remote repository
"C:\Program Files\Git\cmd\git.exe" remote add origin https://github.com/TheMrDude/million-dollar-nft-page.git

REM Push to GitHub
"C:\Program Files\Git\cmd\git.exe" push -u origin main

echo Repository push complete!
