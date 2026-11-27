@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Генерирую отчёт из сохранённой базы...
call ".venv\Scripts\activate.bat"
python main.py --report

echo.
echo Готово. Файл: output\report.md
pause