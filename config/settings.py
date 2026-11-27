import json
import os
from dataclasses import dataclass, field
from pathlib import Path


from dotenv import load_dotenv


@dataclass
class AppSettings:
    name: str = "Vacancy Hunter v2"
    version: str = "0.1.0"
    log_level: str = "INFO"


@dataclass
class SearchSettings:
    city: str = "Москва"
    area_id: int = 1
    experience: list[str] = field(default_factory=list)
    salary: int = 200000
    pages: int = 3
    per_page: int = 50
    schedule: str = "fullDay"
    employment: str = "full"
    professional_roles: list[str] = field(default_factory=list)


@dataclass
class FilesSettings:
    queries_sport: str = "config/queries_sport.txt"
    queries_corporate: str = "config/queries_corporate.txt"
    keywords_sport: str = "config/keywords_sport.txt"
    keywords_corporate: str = "config/keywords_corporate.txt"
    stopwords: str = "config/stopwords.txt"


@dataclass
class StorageSettings:
    db_path: str = "data/vacancies.db"


@dataclass
class OutputSettings:
    dir: str = "output"
    excel_file: str = "output/vacancies.xlsx"
    report_file: str = "output/report.md"


@dataclass
class ScoringSettings:
    sport_weight: float = 1.0
    corporate_weight: float = 1.0
    min_score: int = 2
    priority_high: int = 8
    priority_medium: int = 5
    priority_low: int = 3


@dataclass
class Settings:
    app: AppSettings = field(default_factory=AppSettings)
    search: SearchSettings = field(default_factory=SearchSettings)
    files: FilesSettings = field(default_factory=FilesSettings)
    storage: StorageSettings = field(default_factory=StorageSettings)
    output: OutputSettings = field(default_factory=OutputSettings)
    scoring: ScoringSettings = field(default_factory=ScoringSettings)


def load_settings(config_path: str = "config.json") -> Settings:
    load_dotenv()

    config_file = Path(config_path)

    if not config_file.exists():
        return Settings()

    with config_file.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    settings = Settings()

    app = data.get("app", {})

    settings.app = AppSettings(
        name=app.get(
            "name",
            settings.app.name,
        ),
        version=app.get(
            "version",
            settings.app.version,
        ),
        log_level=os.getenv(
            "LOG_LEVEL",
            app.get(
                "log_level",
                settings.app.log_level,
            ),
        ),
    )

    search = data.get("search", {})

    settings.search = SearchSettings(
        city=os.getenv(
            "SEARCH_CITY",
            search.get(
                "city",
                settings.search.city,
            ),
        ),
        area_id=int(
            os.getenv(
                "SEARCH_AREA_ID",
                search.get(
                    "area_id",
                    settings.search.area_id,
                ),
            )
        ),
        experience=os.getenv(
            "SEARCH_EXPERIENCE",
            ",".join(
                search.get(
                    "experience",
                    [],
                )
            ),
        ).split(","),
        salary=int(
            os.getenv(
                "SEARCH_SALARY",
                search.get(
                    "salary",
                    settings.search.salary,
                ),
            )
        ),
        pages=int(
            os.getenv(
                "SEARCH_PAGES",
                search.get(
                    "pages",
                    settings.search.pages,
                ),
            )
        ),
        per_page=int(
            os.getenv(
                "SEARCH_PER_PAGE",
                search.get(
                    "per_page",
                    settings.search.per_page,
                ),
            )
        ),
        schedule=search.get(
            "schedule",
            settings.search.schedule,
        ),
        employment=search.get(
            "employment",
            settings.search.employment,
        ),
        professional_roles=search.get(
            "professional_roles",
            settings.search.professional_roles,
        ),
    )

    files = data.get("files", {})

    settings.files = FilesSettings(
        queries_sport=os.getenv(
            "QUERIES_SPORT",
            files.get(
                "queries_sport",
                settings.files.queries_sport,
            ),
        ),
        queries_corporate=os.getenv(
            "QUERIES_CORPORATE",
            files.get(
                "queries_corporate",
                settings.files.queries_corporate,
            ),
        ),
        keywords_sport=os.getenv(
            "KEYWORDS_SPORT",
            files.get(
                "keywords_sport",
                settings.files.keywords_sport,
            ),
        ),
        keywords_corporate=os.getenv(
            "KEYWORDS_CORPORATE",
            files.get(
                "keywords_corporate",
                settings.files.keywords_corporate,
            ),
        ),
        stopwords=os.getenv(
            "STOPWORDS",
            files.get(
                "stopwords",
                settings.files.stopwords,
            ),
        ),
    )

    storage = data.get("storage", {})

    settings.storage = StorageSettings(
        db_path=os.getenv(
            "DB_PATH",
            storage.get(
                "db_path",
                settings.storage.db_path,
            ),
        ),
    )

    output = data.get("output", {})

    settings.output = OutputSettings(
        dir=os.getenv(
            "OUTPUT_DIR",
            output.get(
                "dir",
                settings.output.dir,
            ),
        ),
        excel_file=os.getenv(
            "EXCEL_FILE",
            output.get(
                "excel_file",
                settings.output.excel_file,
            ),
        ),
        report_file=os.getenv(
            "REPORT_FILE",
            output.get(
                "report_file",
                settings.output.report_file,
            ),
        ),
    )

    scoring = data.get("scoring", {})

    settings.scoring = ScoringSettings(
        sport_weight=scoring.get(
            "sport_weight",
            settings.scoring.sport_weight,
        ),
        corporate_weight=scoring.get(
            "corporate_weight",
            settings.scoring.corporate_weight,
        ),
        min_score=scoring.get(
            "min_score",
            settings.scoring.min_score,
        ),
        priority_high=scoring.get(
            "priority_high",
            settings.scoring.priority_high,
        ),
        priority_medium=scoring.get(
            "priority_medium",
            settings.scoring.priority_medium,
        ),
        priority_low=scoring.get(
            "priority_low",
            settings.scoring.priority_low,
        ),
    )

    return settings
