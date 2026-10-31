from typing import Any

import json

from ...domain.constants import FAQ_SIZE
from .facts import CompanyFacts, PersonSkeleton

STYLE_RULES = """\
Пиши по-русски, как опытный редактор деловых текстов, а не как рекламный генератор.
- Конкретика вместо общих слов: форматы, сроки, типы документов, размеры команд, реальные процессы.
- Запрещены штампы: «инновационный», «передовой», «уникальный», «революционный»,
  «лидер рынка», «комплексные решения», «синергия», «в современном мире»,
  «вывести на новый уровень», «экосистема».
- Без восклицательных знаков, риторических вопросов и обращений к читателю на «вы» в описаниях.
- Разная длина предложений, без шаблонных троек прилагательных.
- Не выдумывай реальных клиентов, партнёров, инвесторов, награды, отзывы, сертификаты и лицензии
  (в том числе BaFin, ISO). Не обещай доходность и не давай инвестиционных рекомендаций.
- Не описывай функции, которых нет: личный кабинет, загрузку файлов на сайте, онлайн-оплату.
- Имена людей, названия компаний, городов и улиц пиши латиницей ровно как даны, без
  транслитерации: «Friederike Lorenz», а не «Фридерике Лоренц».
- Не повторяй правовую форму в каждом предложении: в тексте достаточно названия бренда.
- Никаких шаблонных переменных вида {name} или [CITY]: только готовый текст.
Отвечай одним JSON-объектом по схеме, без пояснений."""


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def concept_prompt(facts: CompanyFacts, avoid: list[dict[str, str]]) -> tuple[str, str]:
    system = (
        "Ты придумываешь правдоподобную вымышленную B2B-компанию для демонстрационного сайта.\n"
        + STYLE_RULES
    )

    brand_rule = (
        f"Название бренда задано пользователем: «{facts.params.brand_name}». Верни его как есть."
        if facts.params.brand_name
        else (
            "Придумай название бренда: 1–2 слова латиницей, звучит как настоящая немецкая или "
            "международная компания, не содержит слов AI, Smart, Tech, Data в начале и не "
            "повторяет известные бренды."
        )
    )

    avoid_block = (
        "Уже созданные компании. Не повторяй их названия, истории основания, "
        "нишу и формулировки:\n" + _json(avoid)
        if avoid
        else "Других компаний пока нет."
    )

    ceo = next(person for person in facts.team if person.role.value == "ceo")
    user = f"""\
Факты, которые менять нельзя:
{_json(facts.summary())}

Основатель и руководитель компании: {ceo.full_name}, {ceo.age} лет. Других людей по именам
не упоминай: команду опишут отдельно.

Концепт, который нужно развернуть:
{_json(facts.seeds)}

{brand_rule}

{avoid_block}

Что вернуть (длина в символах - ориентир, превышать нельзя):
- brand_name; product_name - название продукта;
- tagline: короткий слоган о результате для клиента, 5–10 слов, 40–100 символов, без
  отглагольных существительных («Предоставление…», «Обеспечение…»);
- niche: суть специализации одним предложением, до 250 символов;
- founding_story: 2–3 абзаца, 700–1500 символов: кто, когда и почему основал компанию,
  с конкретной исходной проблемой; основатель - {ceo.full_name};
- specialization: в чём компания сильна и чего сознательно не делает, 400–1000 символов;
- milestones: 3–5 этапов, первый - год основания {facts.founded_year}, последний не позже
  {facts.current_year}, годы по возрастанию; описание этапа до 300 символов;
- segments: 2–4 сегмента клиентов, описание каждого до 300 символов;
- client_problem: проблема клиента до сервиса, с деталями рабочего процесса, 400–1000
  символов."""
    return system, user


def product_prompt(facts: CompanyFacts, concept: dict[str, Any]) -> tuple[str, str]:
    system = "Ты описываешь продукт B2B-компании для сайта и FAQ.\n" + STYLE_RULES
    user = f"""\
Факты компании:
{_json(facts.summary())}

Концепт и история (уже утверждены, не противоречь им):
{_json(concept)}

Опиши продукт «{concept["product_name"]}»:
- summary: что делает сервис, для кого и какой результат, 1–2 абзаца, 500–1200 символов;
- inputs: какие данные нужны на входе (от клиента и из открытых источников);
- process: 4–6 шагов работы, последовательно и проверяемо, описание шага до 300 символов;
- outputs: что именно получает клиент;
- limitations: 3–6 честных ограничений (покрытие, сроки, чего сервис не делает);
- benefits: 3–4 преимущества, каждое следует из процесса, а не из маркетинга;
- delivery: формат и сроки поставки, согласованные с концептом;
- faq: ровно {FAQ_SIZE} вопросов клиентов с ответами до 500 символов; ответы не противоречат
  ограничениям.
Ограничения, процесс, поставка и FAQ должны быть согласованы между собой."""
    return system, user


def _person_line(person: PersonSkeleton) -> dict[str, Any]:
    return {
        "id": person.id,
        "имя": person.full_name,
        "пол": "женский" if person.gender.value == "female" else "мужской",
        "возраст": person.age,
        "роль": {
            "ceo": "руководитель компании, основатель",
            "department_head": f"руководитель отдела «{person.department}»",
            "specialist": f"специалист, отдел «{person.department}»",
        }[person.role.value],
    }


def team_prompt(facts: CompanyFacts, concept: dict[str, Any]) -> tuple[str, str]:
    system = "Ты пишешь краткие профессиональные биографии сотрудников для сайта.\n" + STYLE_RULES
    people = [_person_line(person) for person in facts.team]
    story = {
        "бренд": concept["brand_name"],
        "продукт": concept["product_name"],
        "ниша": concept["niche"],
        "история": concept["founding_story"],
        "специализация": concept["specialization"],
    }
    user = f"""\
Компания:
{_json(facts.summary())}

История и специализация (не противоречь им):
{_json(story)}

Сотрудники (id, имена, возраст и роли менять нельзя):
{_json(people)}

Для каждого сотрудника верни:
- id - как дан;
- position - должность по-русски, как на сайте;
- department - отдел (для руководителя компании null);
- bio: 2–3 предложения от третьего лица (250–600 символов): чем человек занимается в
  компании и что умел до неё;
- experience: 1–4 пункта прошлого опыта «должность, тип организации, годы», без названий
  реальных компаний; годы согласованы с возрастом и с годом основания {facts.founded_year};
- education: вуз и направление (реальные вузы допустимы).
Опыт людей должен быть разным: не делай всех выходцами из банков или консалтинга."""
    return system, user


def revision_prompt(
    facts: CompanyFacts,
    concept: dict[str, Any],
    product: dict[str, Any],
    issues: list[dict[str, str]],
) -> tuple[str, str]:
    system = "Ты редактор и исправляешь описание продукта по замечаниям.\n" + STYLE_RULES
    user = f"""\
Факты компании:
{_json(facts.summary())}

История и специализация:
{_json({"история": concept["founding_story"], "специализация": concept["specialization"]})}

Текущий слоган: {concept["tagline"]}
Текущее описание продукта:
{_json(product)}

Замечания редактора:
{_json(issues)}

Исправь только то, на что указывают замечания, остальное оставь как есть. Если замечание
ошибочное, не меняй текст ради него. Верни слоган (tagline) и описание продукта целиком в
той же структуре: summary, inputs, process, outputs, limitations, benefits, delivery, faq
(ровно {FAQ_SIZE} вопросов)."""
    return system, user


def review_prompt(profile: dict[str, Any]) -> tuple[str, str]:
    system = (
        "Ты внимательный редактор и проверяешь карточку компании на противоречия перед "
        "публикацией. Отвечай одним JSON-объектом по схеме."
    )
    user = f"""\
Найди в карточке смысловые проблемы:
- противоречия в описании продукта (процесс, ограничения, результат, поставка, FAQ);
- несостыковки дат, возраста и опыта людей с историей компании;
- обещания функций, которых нет (личный кабинет, загрузка файлов, онлайн-оплата),
  инвестиционные рекомендации, выдуманные клиенты, лицензии и награды.
Не придирайся к стилю. Если проблем нет, верни пустой список issues.
severity: error - явное противоречие или недопустимое обещание, warning - сомнительное место.

Карточка:
{_json(profile)}"""
    return system, user


_ROLE_EN = {
    "ceo": "managing director",
    "department_head": "head of department",
    "specialist": "team member",
}


def photo_prompt(person: PersonSkeleton, office: str) -> str:
    """
    Портрет для страницы команды. Общий офис на компанию, а поза, место, одежда и свет у
    каждого свои: так команда выглядит как одна съёмка, но не как серия одинаковых рендеров.
    """

    gender = "woman" if person.gender.value == "female" else "man"
    return (
        f"Photo of a {person.age}-year-old {person.heritage} {gender}, "
        f"{_ROLE_EN[person.role.value]} at a small German investment-research company, "
        f"photographed for the team page of the company website. "
        f"{person.appearance}. "
        f"Location: the company office, {office}. "
        "Shot by a professional photographer on a full-frame camera, 50–85mm lens, natural "
        "depth of field, colours as in an unedited photo. "
        "Real person, not a model: realistic skin with pores, fine lines and small "
        "blemishes, slightly uneven features, natural hair with flyaways, clothes with "
        "creases. No beauty retouching, no studio backdrop, no symmetrical stock-photo pose. "
        "No text, no logos, no watermark."
    )
