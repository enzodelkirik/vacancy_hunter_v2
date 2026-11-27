@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

echo ==========================================
echo Vacancy Hunter v2 — пересчёт оценок
echo ==========================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo ОШИБКА: не найден Python в папке .venv.
    echo Пересчёт не запущен.
    echo.
    pause
    exit /b 1
)

if not exist "main.py" (
    echo ОШИБКА: рядом с rescore.bat не найден main.py.
    echo.
    pause
    exit /b 1
)

if not exist "config.json" (
    echo ОШИБКА: рядом с rescore.bat не найден config.json.
    echo.
    pause
    exit /b 1
)

echo Будет использована база из config.json.
echo Новый поиск и загрузка страниц не запускаются.
echo Оценки в базе, Excel и отчёт будут обновлены.
echo.
echo Перед продолжением закрой Excel с выгрузкой.
echo Для отмены закрой это окно.
echo.
pause

".venv\Scripts\python.exe" main.py --rescore --export --report

if errorlevel 1 (
    echo.
    echo Выполнение завершилось с ошибкой.
    echo Если ошибка возникла при экспорте или создании
    echo отчёта, оценки в базе уже могли обновиться.
    echo Скопируй сообщения из этого окна.
    echo.
    pause
    exit /b 1
)

echo.
echo Готово: пересчёт, экспорт и создание отчёта завершены.
echo.
pause
endlocal