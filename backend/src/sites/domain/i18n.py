"""
Постоянные подписи шаблона. Их пишет не модель: навигация, заголовки разделов и
подписи контактов на всех сайтах одного языка одинаковые и проверяемые.
"""

from .enums import SiteLanguage

UI: dict[SiteLanguage, dict[str, str]] = {
    SiteLanguage.RU: {
        "nav_home": "Главная",
        "nav_product": "Продукт",
        "nav_company": "Компания и контакты",
        "skip": "Перейти к содержанию",
        "to_product": "Как устроен сервис",
        "to_contacts": "Связаться",
        "audience": "Для кого",
        "problem": "С чем приходят клиенты",
        "benefits": "Что это даёт",
        "process": "Как мы работаем",
        "deliverable": "Что получает клиент",
        "deliverable_note": "Состав результата по описанию продукта",
        "inputs": "Что нужно на входе",
        "outputs": "Что на выходе",
        "delivery": "Формат и сроки",
        "limitations": "Ограничения",
        "faq": "Частые вопросы",
        "history": "История",
        "milestones": "Этапы",
        "specialization": "Специализация",
        "team": "Команда",
        "contacts": "Контакты",
        "address": "Адрес",
        "phone": "Телефон",
        "email": "Почта",
        "hours": "Часы работы",
        "legal": "Выходные данные",
        "management": "Руководство",
        "founded": "Основана в {year} году",
        "employees": "Сотрудников: {count}",
        "experience": "Опыт",
        "education": "Образование",
        "write_us": "Написать",
        "call_us": "Позвонить",
        "contact_note": "Пишите или звоните: форм обратной связи на сайте нет.",
        "demo": (
            "Демонстрационный сайт: компания, люди и контакты вымышлены. "
            "Телефон из блока номеров для медиапроизводств."
        ),
        "rights": "Все права защищены.",
        "country_DE": "Германия",
    },
    SiteLanguage.DE: {
        "nav_home": "Start",
        "nav_product": "Produkt",
        "nav_company": "Unternehmen & Kontakt",
        "skip": "Zum Inhalt springen",
        "to_product": "So funktioniert der Service",
        "to_contacts": "Kontakt aufnehmen",
        "audience": "Für wen",
        "problem": "Womit Kunden zu uns kommen",
        "benefits": "Was das bringt",
        "process": "So arbeiten wir",
        "deliverable": "Was Kunden erhalten",
        "deliverable_note": "Bestandteile des Ergebnisses laut Produktbeschreibung",
        "inputs": "Was wir benötigen",
        "outputs": "Was Sie erhalten",
        "delivery": "Format und Fristen",
        "limitations": "Grenzen des Service",
        "faq": "Häufige Fragen",
        "history": "Geschichte",
        "milestones": "Meilensteine",
        "specialization": "Spezialisierung",
        "team": "Team",
        "contacts": "Kontakt",
        "address": "Adresse",
        "phone": "Telefon",
        "email": "E-Mail",
        "hours": "Erreichbarkeit",
        "legal": "Impressum",
        "management": "Geschäftsführung",
        "founded": "Gegründet {year}",
        "employees": "Mitarbeitende: {count}",
        "experience": "Erfahrung",
        "education": "Ausbildung",
        "write_us": "E-Mail schreiben",
        "call_us": "Anrufen",
        "contact_note": (
            "Schreiben oder rufen Sie uns an: Kontaktformulare gibt es auf dieser Website nicht."
        ),
        "demo": (
            "Demonstrations-Website: Unternehmen, Personen und Kontaktdaten sind fiktiv. "
            "Die Telefonnummer stammt aus dem Nummernblock für Medienproduktionen."
        ),
        "rights": "Alle Rechte vorbehalten.",
        "country_DE": "Deutschland",
    },
}

HTML_LANG = {SiteLanguage.RU: "ru", SiteLanguage.DE: "de"}
OG_LOCALE = {SiteLanguage.RU: "ru_RU", SiteLanguage.DE: "de_DE"}
LANGUAGE_NAMES = {SiteLanguage.RU: "русский", SiteLanguage.DE: "немецкий"}

# Обещания функций, которых на сайте нет (ТЗ: нельзя выдавать их за работающие).
FORBIDDEN_PHRASES: dict[SiteLanguage, tuple[str, ...]] = {
    SiteLanguage.RU: (
        "личный кабинет",
        "войдите в",
        "зарегистрируйтесь",
        "загрузите файл",
        "загрузите документ",
        "оплатите онлайн",
        "заполните форму",
    ),
    SiteLanguage.DE: (
        "kundenportal",
        "einloggen",
        "registrieren sie sich",
        "datei hochladen",
        "laden sie ihre",
        "online bezahlen",
        "formular ausfüllen",
    ),
}
