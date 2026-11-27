import logging
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from config import Settings


class HHSearcher:
    BASE_URL = "https://hh.ru"

    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/126.0.0.0 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml," "application/xml;q=0.9,*/*;q=0.8"
                ),
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            }
        )

    def _sleep(self) -> None:
        time.sleep(2)

    def _request(
        self,
        url: str,
        params: dict | None = None,
    ) -> requests.Response:
        response = self.session.get(
            url,
            params=params,
            timeout=30,
        )

        if response.status_code == 429:
            raise RuntimeError(
                "hh.ru вернул 429 Too Many Requests. " "Повтори запуск позже."
            )

        if response.status_code >= 400:
            raise RuntimeError(f"Ошибка запроса {response.status_code}: {url}")

        return response

    def _extract_vacancy_id(
        self,
        link: str,
    ) -> str | None:
        match = re.search(
            r"/vacancy/(\d+)",
            link or "",
        )

        return match.group(1) if match else None

    def _extract_salary(
        self,
        container,
    ) -> tuple[str, int | None, int | None, bool | None]:
        if container is None:
            return "", None, None, None

        text = container.get_text(
            " ",
            strip=True,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        if not text:
            return "", None, None, None

        currency_match = re.search(
            r"(₽|руб\.?|RUB|USD|\$|EUR|€)",
            text,
            re.IGNORECASE,
        )

        currency = currency_match.group(1) if currency_match else None

        gross = None

        if re.search(
            r"до\s+вычета\s+налогов|gross",
            text,
            re.IGNORECASE,
        ):
            gross = True
        elif re.search(
            r"на\s+руки|net",
            text,
            re.IGNORECASE,
        ):
            gross = False

        numbers = re.findall(
            r"\d[\d\s]*(?:[.,]\d+)?",
            text,
        )

        numbers = [
            int(
                re.sub(
                    r"[\s,]",
                    "",
                    number,
                ).replace(
                    ".",
                    "",
                )
            )
            for number in numbers
        ]

        salary_from = None
        salary_to = None

        if "от" in text and numbers:
            salary_from = numbers[0]

        if "до" in text and len(numbers) >= 2:
            salary_to = numbers[-1]
        elif "до" in text and numbers:
            salary_to = numbers[0]

        if not salary_from and not salary_to and len(numbers) == 1:
            salary_from = numbers[0]

        return text, salary_from, salary_to, gross

    def _extract_experience(
        self,
        container,
    ) -> str:
        if container is None:
            return ""

        text = container.get_text(
            " ",
            strip=True,
        )

        return re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

    def _extract_employment(
        self,
        soup: BeautifulSoup,
    ) -> str:
        labels = soup.find_all(
            string=re.compile(
                r"Занятость",
                re.IGNORECASE,
            )
        )

        for label in labels:
            parent = label.find_parent(
                [
                    "p",
                    "div",
                    "li",
                    "span",
                ]
            )

            if parent:
                text = parent.get_text(
                    " ",
                    strip=True,
                )

                text = re.sub(
                    r"^Занятость\s*:?\s*",
                    "",
                    text,
                    flags=re.IGNORECASE,
                )

                return re.sub(
                    r"\s+",
                    " ",
                    text,
                ).strip()

        return ""

    def _extract_published_at(
        self,
        soup: BeautifulSoup,
    ) -> str:
        time_tag = soup.find(
            "time",
        )

        if time_tag:
            datetime_value = time_tag.get("datetime") or time_tag.get_text(
                " ",
                strip=True,
            )

            return str(datetime_value or "").strip()

        text = soup.get_text(
            " ",
            strip=True,
        )

        match = re.search(
            r"(?:Опубликована|Опубликовано)\s*:?\s*" r"(\d{1,2}\s+\w+\s+\d{4})",
            text,
            re.IGNORECASE,
        )

        return match.group(1) if match else ""

    def _extract_description(
        self,
        soup: BeautifulSoup,
    ) -> str:
        description = soup.select_one("[data-qa='vacancy-description']")

        if description:
            return description.get_text(
                "\n",
                strip=True,
            )

        return ""

    def _is_title_relevant(
        self,
        title: str,
        query: str,
    ) -> bool:
        title_lower = re.sub(
            r"\s+",
            " ",
            title.lower(),
        ).strip()

        manager_patterns = [
            r"менеджер",
            r"manager",
            r"руководитель",
            r"координатор",
            r"специалист",
            r"ассистент",
        ]

        has_manager = any(
            re.search(
                pattern,
                title_lower,
            )
            for pattern in manager_patterns
        )

        if not has_manager:
            return False

        query_lower = query.lower()

        if "спорт" in query_lower:
            topic_patterns = [
                r"спорт",
                r"физкульт",
                r"фитнес",
                r"олимп",
                r"event",
                r"ивент",
                r"мероприяти",
            ]

        elif "партнёр" in query_lower or "партнер" in query_lower:
            topic_patterns = [
                r"партнёр",
                r"партнер",
                r"спонсор",
                r"спонсорств",
                r"event",
                r"ивент",
                r"мероприяти",
                r"спорт",
            ]

        elif "мероприяти" in query_lower:
            topic_patterns = [
                r"мероприяти",
                r"event",
                r"ивент",
                r"спорт",
                r"конференц",
                r"форум",
            ]

        else:
            topic_patterns = []

        if not topic_patterns:
            return True

        has_topic = any(
            re.search(
                pattern,
                title_lower,
            )
            for pattern in topic_patterns
        )

        return has_topic

    def _parse_search_page(
        self,
        html: str,
        source_query: str,
    ) -> list[dict]:
        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        cards = soup.select("a[data-qa='serp-item__title']")

        vacancies = []

        for card in cards:
            link = card.get("href") or ""

            if link.startswith("/"):
                link = self.BASE_URL + link

            vacancy_id = self._extract_vacancy_id(link)

            if not vacancy_id:
                continue

            title = card.get_text(
                " ",
                strip=True,
            )

            if not self._is_title_relevant(
                title,
                source_query,
            ):
                logging.info(
                    "Отфильтровано по названию: %s",
                    title,
                )

                continue

            card_container = card.find_parent("[data-qa='vacancy-serp__vacancy']")

            if card_container is None:
                card_container = card.find_parent("article") or card.find_parent("div")

            salary_container = None
            experience_container = None

            if card_container:
                salary_container = card_container.select_one(
                    "[data-qa='vacancy-serp__vacancy-compensation']"
                )
                experience_container = card_container.select_one(
                    "[data-qa='vacancy-serp__vacancy-work-experience']"
                )

            salary_text, salary_from, salary_to, gross = self._extract_salary(
                salary_container
            )

            vacancies.append(
                {
                    "vacancy_id": vacancy_id,
                    "title": title,
                    "company": "",
                    "salary": salary_text,
                    "salary_from": salary_from,
                    "salary_to": salary_to,
                    "salary_currency": None,
                    "salary_gross": gross,
                    "area": "",
                    "experience": (self._extract_experience(experience_container)),
                    "employment": "",
                    "published_at": "",
                    "url": link,
                    "sport_score": 0,
                    "corporate_score": 0,
                    "total_score": 0,
                    "recommended_resume": "",
                    "matched_keywords": "",
                    "stopwords": "",
                    "priority": "",
                    "status": "new",
                    "source_query": source_query,
                    "raw_text": "",
                    "date_found": "",
                    "date_reviewed": "",
                }
            )

        return vacancies

    def _parse_vacancy_page(
        self,
        html: str,
    ) -> dict:
        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        company = ""

        company_element = soup.select_one("[data-qa='vacancy-company-name']")

        if company_element:
            company = company_element.get_text(
                " ",
                strip=True,
            )

        area = ""

        area_element = soup.select_one("[data-qa='vacancy-view-location']")

        if not area_element:
            area_element = soup.select_one("[data-qa='vacancy-view-raw-address']")

        if area_element:
            area = area_element.get_text(
                " ",
                strip=True,
            )

        salary_container = soup.select_one("[data-qa='vacancy-salary']")

        salary_text, salary_from, salary_to, gross = self._extract_salary(
            salary_container
        )

        experience = ""

        experience_element = soup.select_one("[data-qa='vacancy-experience']")

        if experience_element:
            experience = experience_element.get_text(
                " ",
                strip=True,
            )

        return {
            "company": company,
            "salary": salary_text,
            "salary_from": salary_from,
            "salary_to": salary_to,
            "salary_currency": None,
            "salary_gross": gross,
            "area": area,
            "experience": experience,
            "employment": self._extract_employment(soup),
            "published_at": self._extract_published_at(soup),
            "raw_text": self._extract_description(soup),
        }

    def _load_vacancy_details(
        self,
        vacancy: dict,
    ) -> dict:
        response = self._request(vacancy["url"])

        details = self._parse_vacancy_page(response.text)

        return {
            **vacancy,
            **details,
        }

    def search_query(
        self,
        query: str,
        resume_type: str,
    ) -> list[dict]:
        results = []

        for page in range(
            1,
            self.settings.search.pages + 1,
        ):
            params = {
                "text": query,
                "area": self.settings.search.area_id,
                "per_page": self.settings.search.per_page,
                "page": page,
            }

            experience = self.settings.search.experience

            if experience:
                params["experience"] = experience

            schedule = self.settings.search.schedule

            if schedule:
                params["schedule"] = schedule

            url = f"{self.BASE_URL}/search/vacancy"

            logging.info(
                "Запрос: %s | резюме: %s | страница: %s",
                query,
                resume_type,
                page,
            )

            response = self._request(
                url,
                params,
            )

            page_results = self._parse_search_page(
                response.text,
                source_query=query,
            )

            if not page_results:
                logging.info(
                    "На странице нет подходящих вакансий: %s",
                    query,
                )
                break

            results.extend(page_results)

            self._sleep()

        return results

    def search_all(self) -> list[dict]:
        queries = []

        for file_path in (
            self.settings.files.queries_sport,
            self.settings.files.queries_corporate,
        ):
            path = Path(file_path)

            if not path.is_file():
                raise FileNotFoundError(f"Не найден файл запросов: {path}")

            for line in path.read_text(encoding="utf-8-sig").splitlines():
                query = line.strip()

                if query and not query.startswith("#"):
                    queries.append(query)

        if not queries:
            raise ValueError("Не найдено ни одного поискового запроса.")

        vacancies_by_id: dict[str, dict] = {}

        for query in queries:
            for resume_type in (
                "sport",
                "corporate",
            ):
                found = self.search_query(
                    query,
                    resume_type,
                )

                for vacancy in found:
                    vacancy_id = vacancy["vacancy_id"]

                    if vacancy_id not in vacancies_by_id:
                        vacancies_by_id[vacancy_id] = vacancy

        vacancies = list(vacancies_by_id.values())

        logging.info(
            "Найдено уникальных вакансий после " "фильтрации по названию: %s",
            len(vacancies),
        )

        for index, vacancy in enumerate(
            vacancies,
            start=1,
        ):
            logging.info(
                "Загружаю описание %s из %s: %s",
                index,
                len(vacancies),
                vacancy["title"],
            )

            try:
                vacancies[index - 1] = self._load_vacancy_details(vacancy)
            except Exception:
                logging.exception(
                    "Не удалось загрузить вакансию: %s",
                    vacancy["url"],
                )

            self._sleep()

        vacancies = [
            vacancy
            for vacancy in vacancies
            if str(vacancy.get("raw_text") or "").strip()
        ]

        logging.info(
            "Вакансий с описанием: %s",
            len(vacancies),
        )

        return vacancies
