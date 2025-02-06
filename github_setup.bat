@echo off
cd "c:\Users\fourl\CascadeProjects\million-dollar-nft-page"

REM Configure Git user
git config --global user.name "TheMrDude"
git config --global user.email "mrdudesblog@gmail.com"

REM Initialize repository if not already done
git init

REM Add all files
git add .

REM Commit changes
git commit -m "Initial commit: Million Dollar NFT Page"

REM Add remote repository
git remote add origin https://github.com/TheMrDude/million-dollar-nft-page.git

REM Push to GitHub
REM Replace YOUR_PERSONAL_ACCESS_TOKEN with the token you generated
git push -u https://YOUR_PERSONAL_ACCESS_TOKEN@github.com/TheMrDude/million-dollar-nft-page.git main

echo Repository push complete!
