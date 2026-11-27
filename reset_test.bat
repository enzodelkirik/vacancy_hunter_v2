@echo off
chcp 65001 >nul
title Vacancy Hunter v2 - сброс тестовых данных

echo ==========================================
echo Vacancy Hunter v2 - сброс тестовых данных
echo ==========================================
echo.
echo Будут удалены только тестовые файлы:
echo - data\vacancies_test.db
echo - output\vacancies_test.xlsx
echo - output\report_test.md
echo.
echo Основные файлы проекта не будут затронуты.
echo.
echo Перед продолжением закрой Excel с выгрузкой.
echo Для отмены закрой это окно.
echo.
pause

if exist "data\vacancies_test.db" (
    del /f /q "data\vacancies_test.db"
    echo Удалена база данных: data\vacancies_test.db
) else (
    echo База данных не найдена: data\vacancies_test.db
)

if exist "output\vacancies_test.xlsx" (
    del /f /q "output\vacancies_test.xlsx"
    echo Удалён Excel: output\vacancies_test.xlsx
) else (
    echo Excel не найден: output\vacancies_test.xlsx
)

if exist "output\report_test.md" (
    del /f /q "output\report_test.md"
    echo Удалён отчёт: output\report_test.md
) else (
    echo Отчёт не найден: output\report_test.md
)

echo.
echo Готово: тестовые данные сброшены.
echo Теперь запусти run.bat для нового поиска.
echo.
pause