@echo off
chcp 65001 >nul
cd /d "%~dp0"

git add -A
git diff --cached --quiet
if not errorlevel 1 goto no_changes

set "commit_message="
set /p "commit_message=Yangilanish nomini yozing: "
if not defined commit_message set "commit_message=Kodlar yangilandi"

git commit -m "%commit_message%"
if errorlevel 1 goto failed

git pull --rebase
if errorlevel 1 goto failed

git push
if errorlevel 1 goto failed

echo.
echo Tayyor: barcha o'zgarishlar GitHub'ga yuborildi.
pause
exit /b 0

:no_changes
echo.
echo Yuboriladigan yangi o'zgarish topilmadi.
pause
exit /b 0

:failed
echo.
echo Xatolik yuz berdi. Yuqoridagi xabarni rasmga olib yuboring.
pause
exit /b 1
