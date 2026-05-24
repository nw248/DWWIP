@echo off
chcp 65001 > nul
echo ========================================
echo   Запуск проекта дистанционного обучения
echo ========================================
echo.

:: Активация виртуального окружения Python
echo [1/3] Активация виртуального окружения...
call .venv\Scripts\activate.bat

:: Запуск бэкенда в новом окне
echo [2/3] Запуск бэкенда (Flask)...
start "Backend" cmd /k "cd /d %~dp0 && .venv\Scripts\activate && python app.py"

:: Ожидание запуска бэкенда
timeout /t 3 /nobreak > nul

:: Запуск фронтенда в новом окне
echo [3/3] Запуск фронтенда (Vue.js)...
start "Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev"

echo.
echo ========================================
echo   Проект запущен!
echo   Бэкенд: http://localhost:5000
echo   Фронтенд: http://localhost:5173
echo ========================================
echo.
pause