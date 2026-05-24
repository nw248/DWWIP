@echo off
chcp 65001 > nul
echo Остановка всех процессов проекта...
taskkill /f /im python.exe /fi "windowtitle eq Backend*" 2>nul
taskkill /f /im node.exe 2>nul
echo Готово.
pause