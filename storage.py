import sqlite3
from datetime import datetime, timezone
from pathlib import Path


VACANCY_FIELDS = [
    "vacancy_id",
    "title",
    "company",
    "salary",
    "salary_from",
    "salary_to",
    "salary_currency",
    "salary_gross",
    "area",
    "experience",
    "employment",
    "published_at",
    "url",
    "sport_score",
    "corporate_score",
    "total_score",
    "recommended_resume",
    "matched_keywords",
    "stopwords",
    "priority",
    "status",
    "source_query",
    "raw_text",
    "date_found",
    "date_reviewed",
]


TEXT_FIELDS = [
    field
    for field in VACANCY_FIELDS
    if field not in {
        "sport_score",
        "corporate_score",
        "total_score",
        "salary_from",
        "salary_to",
        "salary_gross",
    }
]


INTEGER_FIELDS = {
    "sport_score",
    "corporate_score",
    "total_score",
}

OPTIONAL_INTEGER_FIELDS = {
    "salary_from",
    "salary_to",
}

BOOLEAN_FIELDS = {
    "salary_gross",
}


VALID_STATUSES = {
    "new",
    "reviewed",
    "applied",
    "rejected",
}


class VacancyStorage:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.connection = sqlite3.connect(
            self.db_path,
            timeout=30,
        )
        self.connection.row_factory = sqlite3.Row

        try:
            self._create_tables()
        except Exception:
            self.connection.close()
            raise

    def _create_tables(self) -> None:
        with self.connection:
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS vacancies (
                    vacancy_id TEXT PRIMARY KEY,
                    title TEXT,
                    company TEXT,
                    salary TEXT,
                    salary_from INTEGER,
                    salary_to INTEGER,
                    salary_currency TEXT,
                    salary_gross INTEGER,
                    area TEXT,
                    experience TEXT,
                    employment TEXT,
                    published_at TEXT,
                    url TEXT,
                    sport_score INTEGER DEFAULT 0,
                    corporate_score INTEGER DEFAULT 0,
                    total_score INTEGER DEFAULT 0,
                    recommended_resume TEXT,
                    matched_keywords TEXT,
                    stopwords TEXT,
                    priority TEXT,
                    status TEXT DEFAULT 'new',
                    source_query TEXT,
                    raw_text TEXT,
                    date_found TEXT,
                    date_reviewed TEXT
                )
                """
            )

            columns = {
                row["name"]
                for row in self.connection.execute(
                    "PRAGMA table_info(vacancies)"
                ).fetchall()
            }

            migrations = {
                "total_score": (
                    "ALTER TABLE vacancies "
                    "ADD COLUMN total_score "
                    "INTEGER DEFAULT 0"
                ),
                "stopwords": (
                    "ALTER TABLE vacancies "
                    "ADD COLUMN stopwords "
                    "TEXT DEFAULT ''"
                ),
                "salary_from": (
                    "ALTER TABLE vacancies "
                    "ADD COLUMN salary_from INTEGER"
                ),
                "salary_to": (
                    "ALTER TABLE vacancies "
                    "ADD COLUMN salary_to INTEGER"
                ),
                "salary_currency": (
                    "ALTER TABLE vacancies "
                    "ADD COLUMN salary_currency TEXT"
                ),
                "salary_gross": (
                    "ALTER TABLE vacancies "
                    "ADD COLUMN salary_gross INTEGER"
                ),
                "employment": (
                    "ALTER TABLE vacancies "
                    "ADD COLUMN employment TEXT"
                ),
                "published_at": (
                    "ALTER TABLE vacancies "
                    "ADD COLUMN published_at TEXT"
                ),
            }

            for field, sql in migrations.items():
                if field not in columns:
                    self.connection.execute(sql)

            self.connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_vacancies_status_score
                ON vacancies(status, total_score DESC)
                """
            )

    @staticmethod
    def _now() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()

    def exists(self, vacancy_id: str) -> bool:
        row = self.connection.execute(
            """
            SELECT 1
            FROM vacancies
            WHERE vacancy_id = ?
            """,
            (str(vacancy_id),),
        ).fetchone()

        return row is not None

    @staticmethod
    def _prepare_value(
        field: str,
        value: object,
    ) -> object:
        if field in INTEGER_FIELDS:
            return int(value or 0)

        if field in OPTIONAL_INTEGER_FIELDS:
            if value in (None, ""):
                return None

            return int(value)

        if field in BOOLEAN_FIELDS:
            if value is None or value == "":
                return None

            return int(bool(value))

        return str(value or "")

    def upsert(self, vacancy: dict) -> None:
        values = {
            field: self._prepare_value(
                field,
                vacancy.get(field),
            )
            for field in VACANCY_FIELDS
        }

        values["vacancy_id"] = (
            values["vacancy_id"].strip()
        )

        if not values["vacancy_id"]:
            raise ValueError(
                "Нельзя сохранить вакансию "
                "без vacancy_id."
            )

        values["status"] = (
            values["status"].strip() or "new"
        )

        if values["status"] not in VALID_STATUSES:
            raise ValueError(
                "Недопустимый статус вакансии: "
                f"{values['status']}"
            )

        if not values["date_found"]:
            values["date_found"] = self._now()

        preserved_fields = {
            "vacancy_id",
            "status",
            "date_found",
            "date_reviewed",
        }

        update_fields = [
            field
            for field in VACANCY_FIELDS
            if field not in preserved_fields
        ]

        columns_sql = ", ".join(VACANCY_FIELDS)

        placeholders_sql = ", ".join(
            f":{field}"
            for field in VACANCY_FIELDS
        )

        updates_sql = ", ".join(
            f"{field} = excluded.{field}"
            for field in update_fields
        )

        with self.connection:
            self.connection.execute(
                f"""
                INSERT INTO vacancies (
                    {columns_sql}
                )
                VALUES (
                    {placeholders_sql}
                )
                ON CONFLICT(vacancy_id) DO UPDATE SET
                    {updates_sql}
                """,
                values,
            )

    def set_status(
        self,
        vacancy_id: str,
        status: str,
    ) -> None:
        if status not in VALID_STATUSES:
            raise ValueError(
                f"Недопустимый статус: {status}"
            )

        date_reviewed = (
            "" if status == "new" else self._now()
        )

        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE vacancies
                SET status = ?,
                    date_reviewed = ?
                WHERE vacancy_id = ?
                """,
                (
                    status,
                    date_reviewed,
                    str(vacancy_id),
                ),
            )

            if cursor.rowcount == 0:
                raise ValueError(
                    "Вакансия не найдена: "
                    f"{vacancy_id}"
                )

    def get_unreviewed(
        self,
        limit: int = 50,
    ) -> list[dict]:
        if limit <= 0:
            return []

        rows = self.connection.execute(
            """
            SELECT *
            FROM vacancies
            WHERE status = 'new'
            ORDER BY
                total_score DESC,
                date_found DESC,
                vacancy_id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    def all_vacancies(self) -> list[dict]:
        rows = self.connection.execute(
            """
            SELECT *
            FROM vacancies
            ORDER BY
                total_score DESC,
                date_found DESC,
                vacancy_id ASC
            """
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    def close(self) -> None:
        self.connection.close()