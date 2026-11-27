from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from config import Settings


HEADERS = [
    ("ID вакансии", "vacancy_id", 16),
    ("Название", "title", 45),
    ("Компания", "company", 30),
    ("Зарплата", "salary", 30),
    ("Зарплата от", "salary_from", 14),
    ("Зарплата до", "salary_to", 14),
    ("Валюта", "salary_currency", 12),
    ("До вычета налогов", "salary_gross", 18),
    ("Местоположение", "area", 40),
    ("Опыт", "experience", 20),
    ("Занятость", "employment", 25),
    ("Дата публикации", "published_at", 20),
    ("Ссылка", "url", 45),
    ("Спорт", "sport_score", 10),
    ("Проекты", "corporate_score", 12),
    ("Итоговый балл", "total_score", 14),
    ("Рекомендуемое резюме", "recommended_resume", 22),
    ("Основания оценки", "matched_keywords", 70),
    ("Стоп-слова", "stopwords", 25),
    ("Приоритет", "priority", 14),
    ("Статус", "status", 16),
    ("Исходный запрос", "source_query", 35),
    ("Описание", "raw_text", 80),
    ("Дата добавления", "date_found", 25),
    ("Дата обработки", "date_reviewed", 25),
]


class ExcelExporter:
    def __init__(self, settings: Settings):
        self.settings = settings

    @staticmethod
    def _format_value(value: object) -> object:
        if value is None:
            return ""

        if isinstance(value, bool):
            return "Да" if value else "Нет"

        return value

    def export(self, vacancies: list[dict]) -> None:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Вакансии"

        header_fill = PatternFill(
            start_color="D9EAF7",
            end_color="D9EAF7",
            fill_type="solid",
        )

        for column, (title, _, width) in enumerate(
            HEADERS,
            start=1,
        ):
            cell = sheet.cell(
                row=1,
                column=column,
                value=title,
            )

            cell.font = Font(
                bold=True,
            )
            cell.fill = header_fill
            cell.alignment = Alignment(
                horizontal="center",
                vertical="center",
                wrap_text=True,
            )

            sheet.column_dimensions[
                get_column_letter(column)
            ].width = width

        for row, vacancy in enumerate(
            vacancies,
            start=2,
        ):
            for column, (_, field, _) in enumerate(
                HEADERS,
                start=1,
            ):
                cell = sheet.cell(
                    row=row,
                    column=column,
                    value=self._format_value(
                        vacancy.get(field)
                    ),
                )

                cell.alignment = Alignment(
                    vertical="top",
                    wrap_text=True,
                )

        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = (
            f"A1:{get_column_letter(len(HEADERS))}"
            f"{max(len(vacancies) + 1, 2)}"
        )

        output_path = Path(
            self.settings.output.excel_file
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        workbook.save(output_path)