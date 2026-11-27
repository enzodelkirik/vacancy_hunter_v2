import argparse
import logging
from pathlib import Path

from config import Settings, load_settings
from excel_export import ExcelExporter
from hh_search import HHSearcher
from report import ReportGenerator
from scoring import VacancyScorer
from storage import VacancyStorage


PROJECT_DIR = Path(__file__).resolve().parent


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(
            logging,
            level.upper(),
            logging.INFO,
        ),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def resolve_project_paths(settings: Settings) -> None:
    def resolve(value: str) -> str:
        path = Path(value).expanduser()

        if not path.is_absolute():
            path = PROJECT_DIR / path

        return str(path.resolve())

    settings.files.queries_sport = resolve(
        settings.files.queries_sport
    )
    settings.files.queries_corporate = resolve(
        settings.files.queries_corporate
    )
    settings.files.keywords_sport = resolve(
        settings.files.keywords_sport
    )
    settings.files.keywords_corporate = resolve(
        settings.files.keywords_corporate
    )
    settings.files.stopwords = resolve(
        settings.files.stopwords
    )

    settings.storage.db_path = resolve(
        settings.storage.db_path
    )

    settings.output.dir = resolve(
        settings.output.dir
    )
    settings.output.excel_file = resolve(
        settings.output.excel_file
    )
    settings.output.report_file = resolve(
        settings.output.report_file
    )


def require_database(settings: Settings) -> None:
    db_path = Path(settings.storage.db_path)

    if not db_path.is_file():
        raise FileNotFoundError(
            f"База не найдена: {db_path}. "
            "Сначала выполни поиск."
        )


def run_pipeline(settings: Settings) -> None:
    searcher = HHSearcher(settings)
    scorer = VacancyScorer(settings)

    logging.info("Начинаю поиск вакансий.")

    vacancies = searcher.search_all()

    logging.info(
        "Получено уникальных вакансий: %s",
        len(vacancies),
    )

    storage = VacancyStorage(
        Path(settings.storage.db_path)
    )

    added = 0
    updated = 0
    below_threshold = 0

    try:
        for vacancy in vacancies:
            vacancy_id = str(
                vacancy.get("vacancy_id") or ""
            ).strip()

            if not vacancy_id:
                logging.warning(
                    "Пропускаю вакансию без ID: %s",
                    vacancy.get("title", ""),
                )
                continue

            vacancy["vacancy_id"] = vacancy_id

            already_exists = storage.exists(
                vacancy_id
            )
            result = scorer.score(vacancy)

            passes_threshold = (
                result["total_score"]
                >= settings.scoring.min_score
            )

            if not passes_threshold:
                below_threshold += 1

                if not already_exists:
                    continue

            storage.upsert(
                {
                    **vacancy,
                    **result,
                }
            )

            if already_exists:
                updated += 1
            else:
                added += 1

    finally:
        storage.close()

    logging.info(
        "Добавлено новых вакансий: %s",
        added,
    )
    logging.info(
        "Обновлено существующих вакансий: %s",
        updated,
    )
    logging.info(
        "Ниже текущего порога релевантности: %s",
        below_threshold,
    )


def rescore_vacancies(settings: Settings) -> None:
    require_database(settings)

    scorer = VacancyScorer(settings)
    storage = VacancyStorage(
        Path(settings.storage.db_path)
    )

    updated = 0
    below_threshold = 0
    without_description = 0

    try:
        vacancies = storage.all_vacancies()

        logging.info(
            "Пересчёт без запросов к hh.ru. "
            "Записей в базе: %s",
            len(vacancies),
        )

        with storage.connection:
            for vacancy in vacancies:
                if not str(
                    vacancy.get("raw_text") or ""
                ).strip():
                    without_description += 1
                    continue

                result = scorer.score(vacancy)

                storage.connection.execute(
                    """
                    UPDATE vacancies
                    SET sport_score = ?,
                        corporate_score = ?,
                        total_score = ?,
                        recommended_resume = ?,
                        matched_keywords = ?,
                        stopwords = ?,
                        priority = ?
                    WHERE vacancy_id = ?
                    """,
                    (
                        result["sport_score"],
                        result["corporate_score"],
                        result["total_score"],
                        result["recommended_resume"],
                        result["matched_keywords"],
                        result["stopwords"],
                        result["priority"],
                        vacancy["vacancy_id"],
                    ),
                )

                updated += 1

                if (
                    result["total_score"]
                    < settings.scoring.min_score
                ):
                    below_threshold += 1

    finally:
        storage.close()

    logging.info(
        "Пересчитано вакансий: %s",
        updated,
    )
    logging.info(
        "Из пересчитанных ниже порога: %s",
        below_threshold,
    )
    logging.info(
        "Пропущено без описания: %s",
        without_description,
    )
    logging.info(
        "Записи не удалялись. "
        "Статусы и даты обработки не изменялись."
    )


def export_excel(settings: Settings) -> None:
    require_database(settings)

    storage = VacancyStorage(
        Path(settings.storage.db_path)
    )

    try:
        vacancies = storage.all_vacancies()
    finally:
        storage.close()

    exporter = ExcelExporter(settings)
    exporter.export(vacancies)

    logging.info(
        "Excel сохранён: %s | вакансий: %s",
        settings.output.excel_file,
        len(vacancies),
    )


def generate_report(settings: Settings) -> None:
    require_database(settings)

    storage = VacancyStorage(
        Path(settings.storage.db_path)
    )

    try:
        vacancies = storage.all_vacancies()
    finally:
        storage.close()

    generator = ReportGenerator(settings)
    generator.generate(vacancies)

    logging.info(
        "Отчёт сохранён: %s",
        settings.output.report_file,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Vacancy Hunter v2"
    )

    search_modes = parser.add_mutually_exclusive_group()

    search_modes.add_argument(
        "--run",
        action="store_true",
        help="Запустить поиск и оценку вакансий",
    )
    search_modes.add_argument(
        "--rescore",
        action="store_true",
        help="Пересчитать базу без запросов к hh.ru",
    )
    search_modes.add_argument(
        "--all",
        action="store_true",
        help="Полный цикл: поиск, Excel и отчёт",
    )

    parser.add_argument(
        "--export",
        action="store_true",
        help="Экспортировать базу в Excel",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Создать отчёт из базы",
    )

    args = parser.parse_args()

    if not any(
        (
            args.run,
            args.rescore,
            args.export,
            args.report,
            args.all,
        )
    ):
        parser.print_help()
        return 0

    setup_logging("INFO")

    try:
        config_path = PROJECT_DIR / "config.json"

        if not config_path.is_file():
            raise FileNotFoundError(
                f"Не найден файл настроек: {config_path}"
            )

        settings = load_settings(
            str(config_path)
        )

        resolve_project_paths(settings)

        logging.getLogger().setLevel(
            getattr(
                logging,
                settings.app.log_level.upper(),
                logging.INFO,
            )
        )

        logging.info(
            "Настройки загружены: %s",
            config_path,
        )
        logging.info(
            "База данных: %s",
            settings.storage.db_path,
        )
        logging.info(
            "Порог релевантности: %s",
            settings.scoring.min_score,
        )

        if args.all or args.run:
            run_pipeline(settings)

        if args.rescore:
            rescore_vacancies(settings)

        if args.all or args.export:
            export_excel(settings)

        if args.all or args.report:
            generate_report(settings)

    except PermissionError:
        logging.exception(
            "Нет доступа к файлу. Если открыт Excel "
            "с выгрузкой, закрой его и повтори запуск."
        )
        return 1

    except Exception:
        logging.exception(
            "Выполнение остановлено из-за ошибки."
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())