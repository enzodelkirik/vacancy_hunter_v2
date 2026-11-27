@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Обновляю Excel из сохранённой базы...
call ".venv\Scripts\activate.bat"
python main.py --export

echo.
echo Готово. Файл: output\vacancies.xlsx
pause