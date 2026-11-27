import re
from pathlib import Path


from config import Settings

PROJECT_RULES = [
    (
        "проектная работа",
        r"\b(?:проект\w*|спецпроект\w*)\b",
        1,
    ),
    (
        "партнерские проекты",
        r"\bпартнерск\w+\s+проект\w*\b",
        4,
    ),
    (
        "реализация проектов",
        r"\bреализаци\w+\s+(?:\w+\s+){0,2}проект\w*\b",
        3,
    ),
    (
        "координация проектов",
        r"\b(?:координаци\w*|координатор\w*)\s+" r"(?:\w+\s+){0,2}проект\w*\b",
        3,
    ),
    (
        "сопровождение проектов",
        r"\bсопровождени\w+\s+" r"(?:\w+\s+){0,2}проект\w*\b",
        3,
    ),
    (
        "организация мероприятий",
        r"\bорганизаци\w+\s+" r"(?:\w+\s+){0,3}мероприят\w*\b",
        3,
    ),
    (
        "ведение партнерских контрактов",
        r"\b(?:ведени\w*|сопровождени\w*|реализаци\w*)"
        r"\s+(?:\w+\s+){0,3}"
        r"(?:контракт\w*|договор\w*)\b",
        2,
    ),
    (
        "контроль обязательств",
        r"\bконтрол\w+\s+(?:\w+\s+){0,3}" r"(?:обязательств\w*|исполнени\w*|срок\w*)\b",
        2,
    ),
    (
        "работа с подрядчиками",
        r"\bподрядчик\w*\b",
        1,
    ),
    (
        "работа с контрагентами",
        r"\bконтрагент\w*\b",
        1,
    ),
    (
        "документооборот",
        r"\b(?:документооборот\w*|" r"закрывающ\w+\s+документ\w*)\b",
        1,
    ),
    (
        "взаимодействие с партнерами",
        r"\b(?:работ\w*|взаимодейств\w*|коммуникаци\w*)"
        r"\s+(?:\w+\s+){0,3}партнер\w*\b",
        2,
    ),
    (
        "корпоративные проекты",
        r"\bкорпоративн\w+\s+(?:проект\w*|программ\w*)\b",
        3,
    ),
    (
        "координация дочерних обществ",
        r"\b(?:дзо|дочерн\w+\s+" r"(?:обществ\w*|компани\w*))\b",
        2,
    ),
]


SPORT_RULES = [
    (
        "спортивная сфера",
        r"\b(?:спорт|спортив\w*|киберспорт\w*|" r"физкультур\w*)\b",
        2,
    ),
    (
        "спортивные проекты",
        r"\bспортив\w+\s+проект\w*\b",
        4,
    ),
    (
        "спортивные мероприятия",
        r"\bспортив\w+\s+(?:мероприят\w*|событи\w*)\b",
        4,
    ),
    (
        "спортивные объекты",
        r"\bспортив\w+\s+(?:объект\w*|инфраструктур\w*|" r"сооружени\w*|комплекс\w*)\b",
        4,
    ),
    (
        "спортивная организация",
        r"\b(?:спортив\w+\s+(?:клуб\w*|центр\w*|"
        r"федераци\w*)|футбольн\w+\s+клуб\w*|"
        r"хоккейн\w+\s+клуб\w*)\b",
        2,
    ),
    (
        "соревнования и турниры",
        r"\b(?:соревновани\w*|турнир\w*|чемпионат\w*)\b",
        2,
    ),
]


STRONG_SPORT_LABELS = {
    "спортивные проекты",
    "спортивные мероприятия",
    "спортивные объекты",
    "соревнования и турниры",
}


WEAK_COMMERCIAL_RULES = [
    (
        "упоминание продаж",
        r"\bпродаж\w*\b",
        1,
    ),
    (
        "привлечение партнеров",
        r"\b(?:привлечени\w*|поиск\w*)\s+" r"(?:\w+\s+){0,2}партнер\w*\b",
        1,
    ),
    (
        "развитие партнерской сети",
        r"\bразвит\w+\s+(?:\w+\s+){0,2}" r"партнерск\w+\s+сет\w*\b",
        1,
    ),
]


STRONG_COMMERCIAL_RULES = [
    (
        "продажа услуг или продуктов",
        r"\bпродаж\w+\s+"
        r"(?:услуг\w*|продукт\w*|пакет\w*|"
        r"реклам\w*|спонсорск\w*)\b",
        2,
    ),
    (
        "план продаж или воронка продаж",
        r"\b(?:план\w+\s+(?:\w+\s+){0,2}"
        r"(?:продаж\w*|выручк\w*)|"
        r"воронк\w+\s+продаж\w*)\b",
        2,
    ),
    (
        "привлечение клиентов или спонсоров",
        r"\b(?:привлечени\w*|поиск\w*)\s+"
        r"(?:\w+\s+){0,2}"
        r"(?:клиент\w*|спонсор\w*|рекламодател\w*)\b",
        2,
    ),
    (
        "фандрайзинг",
        r"\b(?:фандрайзинг\w*|фандрейзинг\w*)\b",
        2,
    ),
    (
        "привлечение финансирования",
        r"\bпривлечени\w+\s+(?:\w+\s+){0,2}"
        r"(?:финансировани\w*|денежн\w*|инвестици\w*)\b",
        2,
    ),
    (
        "холодное привлечение",
        r"\bхолодн\w+\s+(?:звон\w*|поиск\w*|" r"продаж\w*|контакт\w*)\b",
        2,
    ),
]


TITLE_COMMERCIAL_RULES = [
    (
        "продажи в названии",
        r"\bпродаж\w*\b",
        3,
    ),
    (
        "привлечение клиентов, спонсоров или финансирования " "в названии",
        r"\b(?:привлечени\w*|поиск\w*)\s+"
        r"(?:\w+\s+){0,2}"
        r"(?:клиент\w*|спонсор\w*|рекламодател\w*|"
        r"финансировани\w*)\b",
        3,
    ),
    (
        "фандрайзинг в названии",
        r"\b(?:фандрайзинг\w*|фандрейзинг\w*)\b",
        3,
    ),
]


TITLE_PENALTIES = [
    (
        "разработка или техническая архитектура",
        r"\b(?:программист\w*|разработчик\w*|" r"developer|архитектор\w*)\b",
        8,
    ),
    (
        "бухгалтерия или аудит",
        r"\b(?:бухгалтер\w*|аудитор\w*)\b",
        8,
    ),
    (
        "юридическая роль",
        r"\b(?:юрист\w*|юрисконсульт\w*)\b",
        8,
    ),
    (
        "подбор персонала",
        r"\b(?:рекрутер\w*|менеджер\s+по\s+персоналу)\b",
        8,
    ),
    (
        "технические проекты",
        r"\b(?:it|ит|crm|erp|гис|1с|" r"кибербезопасност\w*|строительств\w*)\b",
        4,
    ),
    (
        "массовая операционная роль",
        r"\b(?:кассир\w*|курьер\w*|водитель\w*|"
        r"грузчик\w*|комплектовщик\w*|кладовщик\w*)\b",
        8,
    ),
]


class VacancyScorer:
    SECTION_PATTERNS = [
        (
            "duties",
            r"(?:ваши\s+задачи|твои\s+задачи|"
            r"основные\s+задачи|задачи\s+на\s+позиции|"
            r"чем\s+предстоит\s+заниматься|"
            r"чем\s+вам\s+предстоит\s+заниматься|"
            r"что\s+предстоит\s+делать|"
            r"чем\s+нужно\s+заниматься|"
            r"обязанности)",
        ),
        (
            "requirements",
            r"(?:требования\s+к\s+кандидату|"
            r"мы\s+ожидаем\s+от\s+вас|"
            r"мы\s+ожидаем|что\s+мы\s+ожидаем|"
            r"нам\s+важно|требования)",
        ),
        (
            "conditions",
            r"(?:мы\s+предлагаем|что\s+мы\s+предлагаем|"
            r"условия\s+работы|условия|"
            r"у\s+нас\s+есть)",
        ),
    ]

    def __init__(self, settings: Settings):
        self.settings = settings
        self.project_rules = self._compile(PROJECT_RULES)
        self.sport_rules = self._compile(SPORT_RULES)
        self.weak_commercial_rules = self._compile(WEAK_COMMERCIAL_RULES)
        self.strong_commercial_rules = self._compile(STRONG_COMMERCIAL_RULES)
        self.title_commercial_rules = self._compile(TITLE_COMMERCIAL_RULES)
        self.title_penalties = self._compile(TITLE_PENALTIES)

        self.section_patterns = [
            (
                name,
                re.compile(
                    rf"(?<!\w){pattern}(?!\w)\s*:?",
                    re.IGNORECASE,
                ),
            )
            for name, pattern in self.SECTION_PATTERNS
        ]

        self.stopwords = self._load_stopwords(settings.files.stopwords)

    @staticmethod
    def _normalize(value: object) -> str:
        text = str(value or "").casefold()
        text = text.replace("ё", "е")
        text = text.replace("\u200b", "")
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _compile(rules: list) -> list:
        return [
            (label, re.compile(pattern), weight) for label, pattern, weight in rules
        ]

    def _load_stopwords(self, path: str) -> list:
        file_path = Path(path)

        if not file_path.is_file():
            raise FileNotFoundError(f"Не найден файл стоп-слов: {file_path}")

        words = {
            self._normalize(line)
            for line in file_path.read_text(encoding="utf-8-sig").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }

        return [
            (
                word,
                re.compile(rf"(?<!\w){re.escape(word)}(?!\w)"),
            )
            for word in sorted(words)
        ]

    def _split_sections(self, text: str) -> dict:
        markers = []

        for name, pattern in self.section_patterns:
            for match in pattern.finditer(text):
                markers.append((match.start(), match.end(), name))

        markers.sort()

        sections = {
            "duties": [],
            "requirements": [],
            "conditions": [],
        }

        for index, (_, end, name) in enumerate(markers):
            next_start = (
                markers[index + 1][0] if index + 1 < len(markers) else len(text)
            )

            fragment = text[end:next_start].strip()

            if fragment:
                sections[name].append(fragment)

        return {name: " ".join(parts) for name, parts in sections.items()}

    @staticmethod
    def _evaluate(
        title: str,
        body: str,
        rules: list,
        body_factor: float,
    ) -> tuple[float, list[str]]:
        points = 0.0
        reasons = []

        for label, pattern, weight in rules:
            if pattern.search(title):
                points += weight
                reasons.append(f"{label} [название]")
            elif pattern.search(body):
                points += weight * body_factor
                reasons.append(f"{label} [текст роли]")

        return points, reasons

    def score(self, vacancy: dict) -> dict:
        title = self._normalize(vacancy.get("title"))
        description = self._normalize(vacancy.get("raw_text"))

        sections = self._split_sections(description)
        duties = sections["duties"]

        if duties:
            role_text = duties
            body_factor = 0.75
            section_note = (
                "оценка текста по распознанному разделу "
                "обязанностей; границы требуют проверки"
            )
        else:
            role_text = description
            body_factor = 0.25
            section_note = (
                "раздел обязанностей не распознан; " "вес полного описания снижен"
            )

        project_points, project_reasons = self._evaluate(
            title,
            role_text,
            self.project_rules,
            body_factor,
        )

        sport_points, sport_reasons = self._evaluate(
            title,
            role_text,
            self.sport_rules,
            body_factor,
        )

        weak_points, weak_reasons = self._evaluate(
            title,
            role_text,
            self.weak_commercial_rules,
            1.0 if duties else 0.5,
        )

        strong_points, strong_reasons = self._evaluate(
            title,
            role_text,
            self.strong_commercial_rules,
            1.0 if duties else 0.5,
        )

        title_commercial_points, (title_commercial_reasons) = self._evaluate(
            title,
            "",
            self.title_commercial_rules,
            0.0,
        )

        # Несколько слабых признаков не складываются
        # в сильный сигнал. Берём максимум, а не сумму.
        weak_signal = max(
            (
                weight
                for label, pattern, weight in self.weak_commercial_rules
                if pattern.search(title) or pattern.search(role_text)
            ),
            default=0.0,
        )

        commercial_points = weak_signal + strong_points + title_commercial_points

        operational_count = sum(
            bool(pattern.search(role_text))
            for label, pattern, _ in self.project_rules
            if label
            in {
                "реализация проектов",
                "координация проектов",
                "сопровождение проектов",
                "организация мероприятий",
                "ведение партнерских контрактов",
                "контроль обязательств",
            }
        )

        if commercial_points >= 4:
            if operational_count >= 2:
                role_type = (
                    "смешанная: заметная проектная часть " "и коммерческое привлечение"
                )
                commercial_penalty = 4
            else:
                role_type = "преимущественно коммерческое привлечение"
                commercial_penalty = 6
        elif commercial_points >= 2:
            if operational_count >= 2:
                role_type = "смешанная: проектная работа с " "коммерческими признаками"
                commercial_penalty = 2
            else:
                role_type = "есть заметные коммерческие признаки"
                commercial_penalty = 3
        elif commercial_points > 0:
            role_type = "есть отдельные коммерческие признаки"
            commercial_penalty = 1
        else:
            role_type = "коммерческое привлечение не выявлено правилами"
            commercial_penalty = 0

        sport_score = max(
            0,
            int(sport_points * self.settings.scoring.sport_weight + 0.5),
        )

        corporate_score = max(
            0,
            int(project_points * self.settings.scoring.corporate_weight + 0.5),
        )

        penalty = commercial_penalty
        penalty_reasons = []

        if commercial_penalty:
            penalty_reasons.append(
                f"коммерческая составляющая: " f"-{commercial_penalty}"
            )

        for label, pattern, weight in self.title_penalties:
            if pattern.search(title):
                penalty += weight
                penalty_reasons.append(f"{label}: -{weight}")

        stop_matched = [
            word for word, pattern in self.stopwords if pattern.search(title)
        ]

        if stop_matched and penalty == 0:
            penalty += 2
            penalty_reasons.append("стоп-слова в названии: -2")

        total_score = max(
            0,
            sport_score + corporate_score - penalty,
        )

        if total_score >= self.settings.scoring.priority_high:
            priority = "high"
        elif total_score >= self.settings.scoring.priority_medium:
            priority = "medium"
        else:
            priority = "low"

        if commercial_penalty >= 4 and priority == "high":
            priority = "medium"

        if sport_score > corporate_score:
            recommended_resume = "sport"
        elif corporate_score > sport_score:
            recommended_resume = "corporate"
        elif strong_sport_duties := bool(duties) and any(
            pattern.search(duties)
            for label, pattern, _ in self.sport_rules
            if label in STRONG_SPORT_LABELS
        ):
            recommended_resume = "sport"
        else:
            recommended_resume = "corporate"

        explanations = [
            f"характер роли: {role_type}",
            section_note,
            *sport_reasons,
            *project_reasons,
        ]

        if weak_reasons:
            explanations.append(
                "слабые коммерческие признаки: " + ", ".join(weak_reasons)
            )

        if strong_reasons:
            explanations.append(
                "сильные коммерческие признаки: " + ", ".join(strong_reasons)
            )

        if title_commercial_reasons:
            explanations.append(
                "коммерческие признаки в названии: "
                + ", ".join(title_commercial_reasons)
            )

        if penalty_reasons:
            explanations.append("штрафы: " + ", ".join(penalty_reasons))

        explanations.append(
            "требования к опыту и фиксированный оклад " "автоматически не подтверждены"
        )

        return {
            "sport_score": sport_score,
            "corporate_score": corporate_score,
            "total_score": total_score,
            "priority": priority,
            "recommended_resume": recommended_resume,
            "matched_keywords": "; ".join(explanations),
            "stopwords": ", ".join(stop_matched),
        }
