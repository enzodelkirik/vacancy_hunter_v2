from datetime import datetime, timezone
from pathlib import Path

from config import Settings


STATUS_LABELS = {
    "new": "Новые",
    "reviewed": "Просмотренные",
    "applied": "Отклик отправлен",
    "rejected": "Отклонённые",
}

PRIORITY_LABELS = {
    "high": "Высокий",
    "medium": "Средний",
    "low": "Низкий",
}

RESUME_LABELS = {
    "sport": "Спортивное",
    "corporate": "Корпоративное",
}


class ReportGenerator:
    def __init__(self, settings: Settings):
        self.settings = settings

    @staticmethod
    def _format_value(value: object) -> str:
        text = str(value or "").strip()

        return text if text else "Не указано / не извлечено"

    def _format_salary(self, vacancy: dict) -> str:
        salary = str(
            vacancy.get("salary") or ""
        ).strip()

        if not salary:
            return "Не указана / не извлечена"

        salary_from = vacancy.get("salary_from")
        salary_to = vacancy.get("salary_to")
        currency = str(
            vacancy.get("salary_currency") or ""
        ).strip()

        parts = []

        if salary_from:
            parts.append(f"от {salary_from}")

        if salary_to:
            parts.append(f"до {salary_to}")

        if parts:
            salary = " ".join(parts)

            if currency:
                salary = f"{salary} {currency}"

        gross = vacancy.get("salary_gross")

        if gross is True:
            salary = (
                f"{salary} до вычета налогов"
            )
        elif gross is False:
            salary = f"{salary} на руки"

        return salary

    def _format_date(self, value: object) -> str:
        text = str(value or "").strip()

        if not text:
            return "Не указана / не извлечена"

        return text[:10]

    def _count(
        self,
        vacancies: list[dict],
        field: str,
        value: object,
    ) -> int:
        return sum(
            1
            for vacancy in vacancies
            if vacancy.get(field) == value
        )

    def _count_with_description(
        self,
        vacancies: list[dict],
    ) -> int:
        return sum(
            1
            for vacancy in vacancies
            if str(
                vacancy.get("raw_text") or ""
            ).strip()
        )

    def _count_filled(
        self,
        vacancies: list[dict],
        field: str,
    ) -> int:
        return sum(
            1
            for vacancy in vacancies
            if str(
                vacancy.get(field) or ""
            ).strip()
        )

    def _vacancy_block(
        self,
        vacancy: dict,
        index: int,
    ) -> str:
        title = self._format_value(
            vacancy.get("title")
        )
        company = self._format_value(
            vacancy.get("company")
        )
        location = self._format_value(
            vacancy.get("area")
        )
        salary = self._format_salary(vacancy)
        employment = self._format_value(
            vacancy.get("employment")
        )
        published_at = self._format_date(
            vacancy.get("published_at")
        )
        priority = PRIORITY_LABELS.get(
            vacancy.get("priority", "low"),
            "Низкий",
        )
        resume = RESUME_LABELS.get(
            vacancy.get("recommended_resume"),
            "Корпоративное",
        )
        url = self._format_value(
            vacancy.get("url")
        )

        lines = [
            f"### {index}. {title}",
            "",
            f"- Компания: {company}",
            f"- Зарплата: {salary}",
            f"- Местоположение: {location}",
            f"- Занятость: {employment}",
            f"- Дата публикации: {published_at}",
            (
                "- Итоговый балл: "
                f"{vacancy.get('total_score', 0)}"
            ),
            (
                "- Баллы до штрафов: "
                f"спорт — "
                f"{vacancy.get('sport_score', 0)}, "
                f"проекты — "
                f"{vacancy.get('corporate_score', 0)}"
            ),
            f"- Приоритет: {priority}",
            f"- Резюме: {resume}",
            (
                "- Основания оценки: "
                f"{self._format_value(
                    vacancy.get('matched_keywords')
                )}"
            ),
            f"- [Открыть вакансию]({url})",
            "",
        ]

        return "\n".join(lines)

    def generate(self, vacancies: list[dict]) -> None:
        now = datetime.now(timezone.utc)
        generated_at = now.strftime(
            "%Y-%m-%d %H:%M UTC"
        )

        min_score = self.settings.scoring.min_score

        with_description = (
            self._count_with_description(vacancies)
        )

        above_threshold = [
            vacancy
            for vacancy in vacancies
            if with_description
            and vacancy.get("total_score", 0) >= min_score
            and vacancy.get("status") not in {
                "applied",
                "rejected",
            }
        ]

        below_threshold = [
            vacancy
            for vacancy in vacancies
            if vacancy.get("total_score", 0) < min_score
        ]

        above_threshold.sort(
            key=lambda vacancy: (
                vacancy.get("total_score", 0),
                vacancy.get("sport_score", 0),
                vacancy.get("corporate_score", 0),
                str(vacancy.get("title") or ""),
            ),
            reverse=True,
        )

        below_threshold.sort(
            key=lambda vacancy: (
                vacancy.get("total_score", 0),
                vacancy.get("sport_score", 0),
                vacancy.get("corporate_score", 0),
                str(vacancy.get("title") or ""),
            ),
            reverse=True,
        )

        lines = [
            "# Отчёт по вакансиям",
            "",
            f"Сформирован: {generated_at}",
            "",
            "## Общая статистика",
            "",
            f"- Всего записей в базе: {len(vacancies)}",
            (
                "- С описанием вакансии: "
                f"{with_description}"
            ),
            (
                "- Без описания вакансии: "
                f"{len(vacancies) - with_description}"
            ),
            (
                "- Текущий минимальный балл: "
                f"{min_score}"
            ),
            (
                "- С описанием и баллом не ниже порога: "
                f"{len(above_threshold)}"
            ),
            (
                "- Ниже порога: "
                f"{len(below_threshold)}"
            ),
            (
                "- Из подходящих без статуса "
                "applied/rejected: "
                f"{len(above_threshold)}"
            ),
            "",
            (
                "Статистика относится ко всей сохранённой "
                "базе, а не только к последнему запуску "
                "поиска."
            ),
            "",
            "## Полнота данных",
            "",
            (
                "- Компания: заполнено "
                f"{self._count_filled(vacancies, 'company')} "
                f"из {len(vacancies)}"
            ),
            (
                "- Зарплата: заполнено "
                f"{self._count_filled(vacancies, 'salary')} "
                f"из {len(vacancies)}"
            ),
            (
                "- Местоположение: заполнено "
                f"{self._count_filled(vacancies, 'area')} "
                f"из {len(vacancies)}"
            ),
            (
                "- Опыт: заполнено "
                f"{self._count_filled(vacancies, 'experience')} "
                f"из {len(vacancies)}"
            ),
            (
                "- Занятость: заполнено "
                f"{self._count_filled(vacancies, 'employment')} "
                f"из {len(vacancies)}"
            ),
            (
                "- Дата публикации: заполнено "
                f"{self._count_filled(vacancies, 'published_at')} "
                f"из {len(vacancies)}"
            ),
            (
                "- Описание: заполнено "
                f"{with_description} из {len(vacancies)}"
            ),
            "",
            (
                "Пустое поле означает, что данные не были "
                "извлечены или не указаны на странице. "
                "По одной выгрузке различить эти причины "
                "нельзя."
            ),
            "",
            "## По рекомендуемому резюме",
            "",
            (
                "- Спортивное: "
                f"{self._count(
                    vacancies,
                    'recommended_resume',
                    'sport',
                )}"
            ),
            (
                "- Корпоративное: "
                f"{self._count(
                    vacancies,
                    'recommended_resume',
                    'corporate',
                )}"
            ),
            "",
            "## По приоритету",
            "",
            (
                "- Высокий: "
                f"{self._count(vacancies, 'priority', 'high')}"
            ),
            (
                "- Средний: "
                f"{self._count(
                    vacancies,
                    'priority',
                    'medium',
                )}"
            ),
            (
                "- Низкий: "
                f"{self._count(vacancies, 'priority', 'low')}"
            ),
            "",
            "## По статусу",
            "",
            (
                "- Новые: "
                f"{self._count(vacancies, 'status', 'new')}"
            ),
            (
                "- Просмотренные: "
                f"{self._count(
                    vacancies,
                    'status',
                    'reviewed',
                )}"
            ),
            (
                "- Отклик отправлен: "
                f"{self._count(
                    vacancies,
                    'status',
                    'applied',
                )}"
            ),
            (
                "- Отклонённые: "
                f"{self._count(
                    vacancies,
                    'status',
                    'rejected',
                )}"
            ),
            "",
            "## Ограничения оценки",
            "",
            (
                "- Балл — результат правил подбора, "
                "а не процент соответствия опыту "
                "кандидата."
            ),
            (
                "- Выбор резюме и приоритет требуют "
                "ручной проверки требований вакансии."
            ),
            (
                "- Ранее сохранённые записи могут "
                "содержать старые оценки, если не "
                "встретились в новом поиске."
            ),
            (
                "- Наличие описания само по себе не "
                "гарантирует пересчёт по последней версии "
                "правил: версия оценки пока не хранится."
            ),
            (
                "- Указанная зарплата не подтверждает "
                "размер стабильного оклада."
            ),
            "",
            "## Топ вакансий для рассмотрения",
            "",
            (
                "До 20 записей с описанием и баллом не "
                f"ниже {min_score}, без статусов applied "
                "и rejected. Сортировка — по итоговому "
                "баллу с учётом штрафов."
            ),
            "",
        ]

        if above_threshold:
            for index, vacancy in enumerate(
                above_threshold[:20],
                start=1,
            ):
                lines.append(
                    self._vacancy_block(
                        vacancy,
                        index,
                    )
                )
        else:
            lines.append(
                "Подходящих вакансий не найдено."
            )
            lines.append("")

        lines.extend(
            [
                "## Вакансии ниже порога",
                "",
                (
                    "Эти записи сохранены в базе, но "
                    f"получили балл ниже {min_score}. "
                    "Они не удаляются и могут быть "
                    "пересмотрены после изменения правил."
                ),
                "",
            ]
        )

        if below_threshold:
            for index, vacancy in enumerate(
                below_threshold[:20],
                start=1,
            ):
                lines.append(
                    self._vacancy_block(
                        vacancy,
                        index,
                    )
                )
        else:
            lines.append(
                "Вакансий ниже порога нет."
            )
            lines.append("")

        report_path = Path(
            self.settings.output.report_file
        )
        report_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        report_path.write_text(
            "\n".join(lines),
            encoding="utf-8",
        )