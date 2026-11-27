@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

echo ==========================================
echo Vacancy Hunter v2 — поиск вакансий
echo ==========================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo ОШИБКА: не найден Python в папке .venv.
    echo Поиск не запущен.
    echo.
    pause
    exit /b 1
)

if not exist "main.py" (
    echo ОШИБКА: рядом с run.bat не найден main.py.
    echo.
    pause
    exit /b 1
)

if not exist "config.json" (
    echo ОШИБКА: рядом с run.bat не найден config.json.
    echo.
    pause
    exit /b 1
)

if not exist "config\queries_sport.txt" (
    echo ОШИБКА: не найден config\queries_sport.txt.
    echo.
    pause
    exit /b 1
)

if not exist "config\queries_corporate.txt" (
    echo ОШИБКА: не найден config\queries_corporate.txt.
    echo.
    pause
    exit /b 1
)

echo Будут использованы запросы:
echo.
echo --- Спортивное резюме ---
type "config\queries_sport.txt"
echo.
echo --- Корпоративное резюме ---
type "config\queries_corporate.txt"
echo.

echo Поиск выполняется по каждому запросу
echo для спортивного и корпоративного резюме.
echo.
echo Перед продолжением закрой Excel с выгрузкой.
echo Для отмены закрой это окно.
echo.
pause

".venv\Scripts\python.exe" main.py --all

if errorlevel 1 (
    echo.
    echo Выполнение завершилось с ошибкой.
    echo Скопируй сообщения из этого окна.
    echo.
    pause
    exit /b 1
)

echo.
echo Готово: поиск, оценка, экспорт и отчёт завершены.
echo.
pause
endlocal