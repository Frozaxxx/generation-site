"""Правдоподобная карточка для тестов: проходит все проверки без ошибок."""

from typing import Any

import copy

from src.companies.domain.entities import Company
from src.companies.domain.enums import CompanyScale
from src.companies.domain.profile import CompanyProfile
from src.companies.domain.serialization import profile_from_dict
from src.companies.domain.vo import GenerationInfo, GenerationParams

PROFILE_DATA: dict[str, Any] = {
    "brand": {
        "name": "Kestrel Data",
        "legal_form": "GmbH",
        "legal_name": "Kestrel Data GmbH",
        "tagline": "Разбор отчётности эмитентов за часы, а не за дни",
        "domain": "kestrel-data.de",
    },
    "contacts": {
        "address": {
            "street": "Mainzer Landstraße",
            "house_number": "47",
            "postal_code": "60329",
            "city": "Frankfurt am Main",
            "district": "Gallus",
            "state": "Hessen",
            "country_code": "DE",
        },
        "city_key": "frankfurt",
        "phone": "+496990009417",
        "phone_display": "+49 69 90009 417",
        "email": "kontakt@kestrel-data.de",
        "office_hours": "Пн–Пт, 9:00–18:00",
    },
    "history": {
        "founded_year": 2019,
        "employees": 18,
        "founding_story": (
            "Компанию основали два бывших аналитика франкфуртского управляющего фонда, которые "
            "каждый сезон отчётности тратили недели на ручное сравнение цифр с консенсусом."
        ),
        "specialization": (
            "Kestrel Data разбирает квартальную отчётность европейских эмитентов среднего "
            "размера и не занимается торговыми сигналами или инвестиционными рекомендациями."
        ),
        "milestones": [
            {"year": 2019, "title": "Основание", "description": "Первый пилот с семейным офисом."},
            {
                "year": 2022,
                "title": "Покрытие DAX и MDAX",
                "description": "Добавили 150 эмитентов.",
            },
        ],
    },
    "audience": {
        "segments": [
            {"name": "Фонды акций", "description": "Команды из 3–15 аналитиков."},
            {"name": "Семейные офисы", "description": "Без собственного отдела исследований."},
        ],
        "client_problem": (
            "В сезон отчётности аналитик успевает внимательно прочитать лишь часть отчётов, "
            "а расхождения с консенсусом замечает с опозданием."
        ),
    },
    "product": {
        "name": "Kestrel Brief",
        "summary": (
            "Сервис сравнивает свежую отчётность эмитента с прошлыми периодами и консенсусом и "
            "готовит краткий обзор с ссылками на страницы первоисточника."
        ),
        "inputs": ["Список эмитентов клиента", "Публичные отчёты и стенограммы звонков"],
        "process": [
            {"title": "Сбор", "description": "Забираем отчёт в день публикации."},
            {"title": "Разбор", "description": "Извлекаем показатели и комментарии менеджмента."},
            {"title": "Проверка", "description": "Аналитик сверяет спорные места вручную."},
        ],
        "outputs": ["Обзор на 2 страницы", "Таблица отклонений от консенсуса"],
        "limitations": [
            "Не даём рекомендаций покупать или продавать бумаги",
            "Покрываем только эмитентов, торгующихся в ЕС",
        ],
        "benefits": [
            {"title": "Скорость", "description": "Обзор готов в течение 6 часов после отчёта."},
            {"title": "Проверяемость", "description": "Каждая цифра со ссылкой на страницу."},
            {"title": "Фокус", "description": "Только отклонения, которые важны для модели."},
        ],
        "delivery": "Обзоры приходят на почту и в общую папку клиента в течение рабочего дня.",
    },
    "team": [
        {
            "id": "lena-hartmann",
            "first_name": "Lena",
            "last_name": "Hartmann",
            "gender": "female",
            "age": 41,
            "role": "ceo",
            "position": "Управляющий директор",
            "department": None,
            "bio": (
                "Двенадцать лет вела покрытие промышленных компаний в управляющем фонде во "
                "Франкфурте, отвечает за продукт и ключевых клиентов."
            ),
            "experience": ["Аналитик акций, управляющая компания, 2008–2019"],
            "education": "Университет Мангейма, экономика",
            "photo": None,
        },
        {
            "id": "jonas-weber",
            "first_name": "Jonas",
            "last_name": "Weber",
            "gender": "male",
            "age": 37,
            "role": "department_head",
            "position": "Руководитель разработки",
            "department": "Разработка",
            "bio": (
                "Строил конвейеры данных для банковского риск-менеджмента, теперь отвечает за "
                "извлечение показателей и качество модели."
            ),
            "experience": ["Инженер данных, банк, 2014–2019"],
            "education": "TU Darmstadt, информатика",
            "photo": None,
        },
        {
            "id": "miriam-koch",
            "first_name": "Miriam",
            "last_name": "Koch",
            "gender": "female",
            "age": 34,
            "role": "department_head",
            "position": "Руководитель аналитики",
            "department": "Аналитика",
            "bio": (
                "Отвечает за ручную проверку обзоров и методику сравнения с консенсусом, "
                "раньше работала в отделе исследований брокера."
            ),
            "experience": ["Аналитик sell-side, брокерская компания, 2015–2020"],
            "education": "Goethe-Universität Frankfurt, финансы",
            "photo": None,
        },
        {
            "id": "tobias-brandt",
            "first_name": "Tobias",
            "last_name": "Brandt",
            "gender": "male",
            "age": 29,
            "role": "specialist",
            "position": "ML-инженер",
            "department": "Разработка",
            "bio": (
                "Занимается разметкой таблиц из отчётов и оценкой качества извлечения, пришёл "
                "в компанию после магистратуры."
            ),
            "experience": ["Стажёр-исследователь, университетская лаборатория, 2021"],
            "education": "LMU München, статистика",
            "photo": None,
        },
        {
            "id": "sophie-lange",
            "first_name": "Sophie",
            "last_name": "Lange",
            "gender": "female",
            "age": 31,
            "role": "specialist",
            "position": "Менеджер по работе с клиентами",
            "department": "Клиенты",
            "bio": (
                "Помогает клиентам настроить список эмитентов и формат обзоров, собирает "
                "обратную связь для команды продукта."
            ),
            "experience": ["Менеджер проектов, финтех-стартап, 2018–2021"],
            "education": "Hochschule Fresenius, менеджмент",
            "photo": None,
        },
    ],
    "faq": [
        {"question": "Какие эмитенты покрываются?", "answer": "Компании, торгующиеся в ЕС."},
        {"question": "Как быстро готов обзор?", "answer": "В течение 6 часов после публикации."},
        {"question": "Даёте ли вы рекомендации?", "answer": "Нет, только анализ отчётности."},
        {"question": "Откуда берутся данные?", "answer": "Из публичных отчётов эмитентов."},
        {
            "question": "Можно ли проверить цифры?",
            "answer": "Да, у каждой есть ссылка на страницу.",
        },
    ],
}


def profile_data(**overrides: Any) -> dict[str, Any]:
    data = copy.deepcopy(PROFILE_DATA)
    data.update(overrides)
    return data


def make_profile(data: dict[str, Any] | None = None) -> CompanyProfile:
    return profile_from_dict(data or profile_data())


def make_company(profile: CompanyProfile | None = None) -> Company:
    return Company.create(
        params=GenerationParams(
            brand_name=None,
            country="DE",
            direction="ai_investment_research",
            service_type="earnings_analysis",
            scale=CompanyScale.SMALL,
            model="google/gemini-2.5-flash",
            randomized=("brand_name",),
        ),
        profile=profile or make_profile(),
        generation=GenerationInfo(model="google/gemini-2.5-flash", cost_usd=0.012, requests=4),
    )
