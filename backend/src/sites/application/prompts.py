from typing import Any

import json

from ..domain.enums import SiteLanguage

LANGUAGE_RULES = {
    SiteLanguage.RU: "Пиши по-русски.",
    SiteLanguage.DE: (
        "Schreibe auf Deutsch, in der Sie-Form, sachlich wie auf der Website eines deutschen "
        "B2B-Dienstleisters. Keine Anglizismen, wenn es ein übliches deutsches Wort gibt."
    ),
}

STYLE = """\
Тон: спокойный, конкретный, как у хорошего B2B-сайта, а не как у рекламного генератора.
- Без штампов: «инновационный», «передовой», «уникальный», «революционный», «лидер рынка»,
  «комплексные решения», «синергия», «в современном мире», «вывести на новый уровень».
- Без восклицательных знаков и риторических вопросов.
- Факты (имена, числа, сроки, форматы, ограничения) берутся только из карточки. Не придумывай
  клиентов, отзывы, награды, сертификаты, лицензии, доходность и статистику.
- Не обещай функций, которых нет: личного кабинета, загрузки файлов, онлайн-оплаты, форм.
  Связаться можно только по почте и телефону.
- Имена людей, бренд и продукт пиши латиницей как в карточке.
Отвечай одним JSON-объектом по схеме, без пояснений."""


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def copy_prompt(profile: dict[str, Any], language: SiteLanguage) -> tuple[str, str]:
    system = "Ты пишешь тексты подачи для сайта B2B-компании из 3 страниц.\n" + STYLE
    card = {
        "бренд": profile["brand"]["name"],
        "слоган": profile["brand"]["tagline"],
        "город": profile["contacts"]["address"]["city"],
        "год основания": profile["history"]["founded_year"],
        "сотрудников": profile["history"]["employees"],
        "специализация": profile["history"]["specialization"],
        "аудитория": profile["audience"],
        "продукт": {
            key: profile["product"][key]
            for key in ("name", "summary", "outputs", "limitations", "delivery")
        },
        "руководитель": next(
            (f"{p['first_name']} {p['last_name']}" for p in profile["team"] if p["role"] == "ceo"),
            "",
        ),
    }
    user = f"""\
{LANGUAGE_RULES[language]}

Карточка компании (единственный источник фактов):
{_json(card)}

Страницы сайта: главная (предложение, аудитория, преимущества, переход к продукту),
продукт (описание, процесс, ограничения, FAQ), компания и контакты (история, команда, адрес).

Что вернуть:
- home, product, company: title (до 60 символов, обязательно содержит бренд
  «{profile["brand"]["name"]}») и description (120–160 символов, называет бренд и суть
  услуги) для каждой страницы;
- hero_title: главный заголовок первого экрана, 4–9 слов, о результате для клиента;
- hero_lead: 1–2 предложения под заголовком: что делает компания и для кого;
- audience_lead, benefits_lead, process_lead: по одному предложению-подводке к разделам;
- cta_title и cta_text: приглашение изучить продукт или связаться по почте и телефону;
- product_lead: подводка страницы продукта;
- limitations_lead: честная подводка к ограничениям сервиса;
- company_lead: подводка страницы о компании;
- team_lead: одно предложение о команде.
Числа используй только те, что есть в карточке."""
    return system, user


def translation_prompt(texts: dict[str, str], brand: str) -> tuple[str, str]:
    system = (
        "Du übersetzt Website-Texte eines B2B-Unternehmens aus dem Russischen ins Deutsche. "
        "Antworte mit einem JSON-Objekt nach Schema, ohne Erklärungen."
    )
    user = f"""\
Übersetze jeden Text ins Deutsche, so wie ihn ein deutscher B2B-Dienstleister auf seiner
Website schreiben würde: sachlich, in der Sie-Form, natürliches Deutsch statt wörtlicher
Übersetzung. Regeln:
- Bedeutung, Fakten und Einschränkungen exakt beibehalten, nichts hinzufügen oder weglassen.
- Alle Zahlen unverändert übernehmen (gleiche Ziffern, auch Jahreszahlen).
- Namen von Personen, die Marke «{brand}», Produktnamen und lateinisch geschriebene Begriffe
  unverändert lassen.
- Schlüssel unverändert lassen. Für jeden Schlüssel genau eine Übersetzung.

Gib zurück: {{"items": {{"<schlüssel>": "<übersetzung>", ...}}}}

Texte:
{_json(texts)}"""
    return system, user
