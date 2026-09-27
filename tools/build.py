#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сборка статического сайта АНО «Дирижабль».

Зачем нужен: раньше сайт был выгрузкой Craftum CMS, где шапка и подвал
физически дублировались в каждом из 11 HTML-файлов — правка навигации
означала правку всех файлов. Теперь общие части живут здесь, а страницы
описаны данными ниже.

Запуск:  python3 tools/build.py
Зависимостей нет. Пишет HTML в корень репозитория.
"""

from __future__ import annotations

import datetime
import hashlib
import html
import json
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_DIR = os.path.join(ROOT, "assets", "img", "media")

# --------------------------------------------------------------------------
# данные организации
# --------------------------------------------------------------------------

ORG = {
    "name": "АНО «Дирижабль»",
    "full_name": 'Автономная некоммерческая организация Центр развития социальных практик «Дирижабль»',
    "short": "АНО Центр развития социальных практик «Дирижабль»",
    "phone": "+7 (916) 925-91-74",
    "phone_href": "+79169259174",
    "email": "dirigible.community@mail.ru",
    "address": "129128, г. Москва, проспект Мира, д. 202А, кв. 40",
    "inn": "7716981773",
    "kpp": "771601001",
    "ogrn": "1237700318877",
    "director": "Татьяна Арчакова",
}

SOCIALS = [
    ("Telegram", "https://t.me/dirigible_community", "telegram"),
    ("RuTube", "https://rutube.ru/channel/40496484/", "rutube"),
    ("ВКонтакте", "https://vk.com/dirigible_community", "vk"),
]

NAV = [
    ("index.html", "Главная"),
    ("about.html", "О нас"),
    ("news.html", "Новости"),
    ("research.html", "Исследование"),
    ("reports.html", "Отчёты"),
    ("documents.html", "Документы"),
]

CDN = "https://274418.selcdn.ru/cv08300-33250f0d-0664-43fc-9dbf-9d89738d114e/uploads/720494/"

# --------------------------------------------------------------------------
# Внешние идентификаторы — только из окружения.
#
# Строго говоря, это не секреты: счётчики и виджет всё равно видны в HTML
# любому посетителю. Выносим их из репозитория по другой причине — чтобы форк,
# локальная сборка или чужой стенд не слали хиты в боевую статистику
# организации и не показывали её платёжную форму. Пусто → счётчики не
# подключаются, у формы показывается запасной блок с реквизитами.
#
# Локально:  YANDEX_METRIKA_ID=... python3 tools/build.py
# На GitHub: Settings → Secrets and variables → Actions (см. README).
# --------------------------------------------------------------------------

SITE_URL = os.environ.get("SITE_URL", "https://dirigible.community").rstrip("/")

ANALYTICS = {
    "yandex_metrika_id": os.environ.get("YANDEX_METRIKA_ID", "").strip(),
    "top_mail_ru_id": os.environ.get("TOP_MAIL_RU_ID", "").strip(),
}

DONATION = {
    "widget_id": os.environ.get("DONATION_WIDGET_ID", "").strip(),
    # Общая форма — используется везде, где не задана отдельная.
    "form_id": os.environ.get("DONATION_FORM_ID", "").strip(),
    # Отдельные формы под адресные сборы. Пока организация не заведёт их
    # в кабинете donation.ru, страницы Вани и братьев используют общую форму,
    # то есть пожертвование уходит в общий проект без привязки к адресату.
    "form_id_vanya": os.environ.get("DONATION_FORM_ID_VANYA", "").strip(),
    "form_id_brothers": os.environ.get("DONATION_FORM_ID_BROTHERS", "").strip(),
}

# --------------------------------------------------------------------------
# Страницы адресных сборов на конкретных детей временно сняты с сайта.
# Контент и вёрстка сохранены целиком — чтобы вернуть, достаточно собрать
# с SHOW_CASE_PAGES=1. Пока флаг выключен: страницы не генерируются, блоки
# «Адресная помощь» на главной и в разделе «Помочь» не выводятся,
# а старые адреса page2/page6 ведут на общую страницу пожертвований.
# --------------------------------------------------------------------------

CASE_SLUGS = ("help-vanya.html", "help-brothers.html")
SHOW_CASE_PAGES = os.environ.get("SHOW_CASE_PAGES", "").strip() == "1"

# Видео курса на RuTube. Не секрет — публичный идентификатор ролика,
# но держим в одном месте, чтобы не искать по разметке.
RUTUBE_COURSE_VIDEO = "537fad5738e2f361bfb9a5d0d5b16bf1"

# Магазин ЮKassa для оплаты курса. Форма SimplePay шлёт POST напрямую
# на yookassa.ru, бэкенд не нужен. Идентификатор — из окружения, чтобы
# чужая сборка не собирала платежи в кассу организации.
YOOKASSA_SHOP_ID = os.environ.get("YOOKASSA_SHOP_ID", "").strip()

# PDF-документы остались на CDN организации — это оригиналы, их не копируем.
PDF = {
    "privacy_policy": CDN + "d85b9857-8847-455f-8e4e-9f865642a14b.pdf",
    "personal_data": CDN + "b849d6e3-28e2-4eea-bc1b-6102c62569f5.pdf",
    "offer": CDN + "4bc5be66-e154-45ba-bb2f-7094e44986e2.pdf",
    "charter": CDN + "16f042a9-66f9-4773-81ee-72b2cd18157d.pdf",
    "report_2024": CDN + "60bdecb3-a7a0-4504-9414-dface3e9f00e.pdf",
    # Отчёт за 2025 лежит локально: в выгрузке Craftum он ошибочно ссылался
    # на файл 2024 года, поэтому берём загруженный заказчиком PDF.
    "report_2025": "assets/docs/otchet-2025.pdf",
    "prolong_2023": CDN + "ce0761c4-c3e5-4b10-b4c4-b89f200295f9.pdf",
    "prolong_2024": CDN + "232fed0a-db1e-4128-9f4a-349d77bd9db3.pdf",
    "edu_transfer": CDN + "bfb77bb3-174c-4e81-afe3-10b8db0b55de.pdf",
    "edu_schedule": CDN + "f4964e5b-9866-468d-8335-1279aea31b63.pdf",
    "edu_admission": CDN + "8529903b-527b-418c-be85-4e0bd991b6e1.pdf",
    "edu_unit": CDN + "64e2b154-9c71-4c91-969d-a76bc57666ed.pdf",
    "edu_control": CDN + "cbaa25c1-8c68-4d00-b952-6a4fc8adb75d.pdf",
    "edu_paid": CDN + "0d5edbec-4134-40a9-bf6c-326fa59117ba.pdf",
    "edu_dpo": CDN + "6cdada52-7af9-419e-8696-6a1692ba0d1d.pdf",
    "edu_distance": CDN + "b33c8781-9e40-461b-8505-3bbde872936a.pdf",
    "edu_license": CDN + "ee793381-0ca7-448b-a4c3-2a84532b85a5.pdf",
    "edu_program": CDN + "e17f7799-91c7-4e5b-b580-bb8bc1f042a4.pdf",
}

REPORT_2023 = "https://cloud.mail.ru/public/Ekqc/SHPEhBVc9"
CHECKED_CHARITY = ("https://checked.charity/organizations/nonprofit/"
                   "019f055f-95ae-72ab-9a62-648e1965a8b0/page/show")
GOV_RULES = "http://static.government.ru/media/files/41d484e6a542670e1f70.pdf"
def donation_loader_url() -> str:
    """Загрузчик виджета пожертвований. Идентификатор — из окружения."""
    return "https://widgets.donation.ru/wloader/%s/wloader.js" % DONATION["widget_id"]

# --------------------------------------------------------------------------
# утилиты
# --------------------------------------------------------------------------


def esc(text: str) -> str:
    return html.escape(text, quote=True)


_asset_cache: dict = {}


def asset(rel_path: str) -> str:
    """Путь к статике с ?v=<хеш содержимого> — чтобы браузер не отдавал
    из кэша старый CSS/JS после правок."""
    if rel_path in _asset_cache:
        return _asset_cache[rel_path]
    full = os.path.join(ROOT, rel_path)
    try:
        with open(full, "rb") as f:
            digest = hashlib.md5(f.read()).hexdigest()[:8]
        out = "%s?v=%s" % (rel_path, digest)
    except OSError:
        out = rel_path
    _asset_cache[rel_path] = out
    return out


def image_size(filename: str):
    """Размеры JPEG/PNG без внешних зависимостей — нужны для width/height и защиты от CLS."""
    path = os.path.join(MEDIA_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError("нет файла " + path)
    with open(path, "rb") as f:
        head = f.read(26)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            w, h = struct.unpack(">II", head[16:24])
            return w, h
        if head[:2] == b"\xff\xd8":
            f.seek(2)
            while True:
                byte = f.read(1)
                while byte and byte != b"\xff":
                    byte = f.read(1)
                marker = f.read(1)
                while marker == b"\xff":
                    marker = f.read(1)
                if not marker:
                    break
                if marker[0] in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                                 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    f.read(3)
                    h, w = struct.unpack(">HH", f.read(4))
                    return w, h
                length = struct.unpack(">H", f.read(2))[0]
                f.seek(length - 2, 1)
    raise ValueError("не удалось определить размер " + filename)


def img(filename: str, alt: str, cls: str = "", *, eager: bool = False,
        sizes: str = "", extra: str = "", focus: str = "") -> str:
    """focus — точка кадрирования для object-fit: cover (например "55% 20%").
    Нужна для вертикальных фото: по умолчанию cover берёт середину кадра,
    и в горизонтальной карточке вместо лица остаётся торс."""
    w, h = image_size(filename)
    attrs = [
        'src="assets/img/media/%s"' % filename,
        'alt="%s"' % esc(alt),
        'width="%d"' % w,
        'height="%d"' % h,
        'decoding="async"',
    ]
    if focus:
        attrs.append('style="object-position:%s"' % focus)
    if eager:
        attrs.append('fetchpriority="high"')
    else:
        attrs.append('loading="lazy"')
    if cls:
        attrs.insert(0, 'class="%s"' % cls)
    if sizes:
        attrs.append('sizes="%s"' % sizes)
    if extra:
        attrs.append(extra)
    return "<img " + " ".join(attrs) + ">"


ICONS = {
    "telegram": '<svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor" aria-hidden="true"><path d="M21.9 4.3 18.9 19c-.2 1-.8 1.2-1.7.8l-4.6-3.4-2.2 2.1c-.3.3-.5.5-1 .5l.3-4.8L18.5 6c.4-.3-.1-.5-.6-.2L6.9 12.4l-4.6-1.4c-1-.3-1-1 .2-1.5l18-6.9c.8-.3 1.6.2 1.4 1.7z"/></svg>',
    "rutube": '<svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor" aria-hidden="true"><path d="M3 4h13.2c2.4 0 3.8 1.4 3.8 3.7v2.1c0 2-1.1 3.3-3 3.6L21 20h-3.6l-3.6-6.4H6.2V20H3V4zm3.2 2.8v4h9.4c1 0 1.4-.4 1.4-1.3V8.1c0-.9-.4-1.3-1.4-1.3H6.2z"/></svg>',
    "vk": '<svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor" aria-hidden="true"><path d="M13 18c-5.4 0-8.9-3.8-9-10h2.8c.1 4.6 2.2 6.5 3.8 6.9V8h2.6v3.9c1.5-.2 3.1-2 3.6-3.9h2.6c-.4 2.3-2 4.1-3.2 4.9 1.2.6 3 2.2 3.7 5.1h-2.9c-.5-1.8-2-3.2-3.8-3.4V18H13z"/></svg>',
    "doc": '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 2H6.5A1.5 1.5 0 0 0 5 3.5v17A1.5 1.5 0 0 0 6.5 22h11a1.5 1.5 0 0 0 1.5-1.5V7z"/><path d="M14 2v5h5"/><path d="M9 13h6M9 17h6"/></svg>',
    "arrow-left": '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 5 8 12l7 7"/></svg>',
    "arrow-right": '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 5 7 7-7 7"/></svg>',
    "heart": '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M12 21s-7.5-4.7-9.4-9A5.3 5.3 0 0 1 12 6.6 5.3 5.3 0 0 1 21.4 12c-1.9 4.3-9.4 9-9.4 9z"/></svg>',
}


def yarn(cls: str) -> str:
    """Декоративный клубок. Инлайновый SVG, а не <img>: только так работает
    currentColor и клубок можно перекрашивать из CSS."""
    return (
        '<svg class="pompom %s" viewBox="0 0 120 120" width="120" height="120" aria-hidden="true" focusable="false">'
        '<circle cx="60" cy="60" r="46" fill="currentColor"/>'
        '<g fill="none" stroke="#FBF6EC" stroke-width="3" stroke-linecap="round" opacity=".7">'
        '<path d="M17 48c28 9 58 9 86 0"/><path d="M15 62c29 10 61 10 90 0"/>'
        '<path d="M20 76c26 9 54 9 80 0"/><path d="M44 16c-14 26-14 62 0 88"/>'
        '<path d="M64 15c16 27 16 63 0 90"/><path d="M84 24c10 23 10 49 0 72"/></g>'
        '<path d="M104 74c14 6 12 26-6 30" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>'
        "</svg>" % cls
    )


def doc_link(href: str, title: str, meta: str = "PDF") -> str:
    # Документы открываем в новой вкладке — и внешние, и локальные PDF:
    # иначе посетитель уходит с сайта в просмотрщик и теряет навигацию.
    new_tab = href.startswith("http") or href.lower().endswith(".pdf")
    rel = ' target="_blank" rel="noopener noreferrer"' if new_tab else ""
    hint = ' <span class="visually-hidden">(откроется в новой вкладке)</span>' if new_tab else ""
    return (
        '<a class="doc-link" href="%s"%s>'
        '<span class="doc-link__icon">%s</span>'
        '<span><span class="doc-link__meta">%s</span>%s%s</span>'
        "</a>" % (esc(href), rel, ICONS["doc"], esc(meta), esc(title), hint)
    )


def carousel(slides: list, label: str) -> str:
    items = "\n".join(slides)
    return """<div class="carousel" data-carousel role="group" aria-roledescription="карусель" aria-label="%s">
  <div class="carousel__track" data-carousel-track tabindex="0">
%s
  </div>
  <div class="carousel__nav">
    <button type="button" class="carousel__btn" data-carousel-prev aria-label="Предыдущий слайд">%s</button>
    <div class="carousel__dots" data-carousel-dots></div>
    <button type="button" class="carousel__btn" data-carousel-next aria-label="Следующий слайд">%s</button>
  </div>
</div>""" % (esc(label), items, ICONS["arrow-left"], ICONS["arrow-right"])


# --------------------------------------------------------------------------
# каркас страницы
# --------------------------------------------------------------------------


def analytics_config() -> str:
    """Конфиг счётчиков для assets/js/analytics.js.

    Идентификаторы не хардкодятся: пустые значения (локальная сборка)
    оставляют analytics.js в режиме заглушки.
    """
    ym = ANALYTICS["yandex_metrika_id"]
    tmr = ANALYTICS["top_mail_ru_id"]
    if not ym and not tmr:
        return ""
    return ('<script>window.ANALYTICS_CONFIG={yandexMetrika:%s,topMailRu:%s};</script>\n'
            % (('"%s"' % esc(ym)) if ym else "null",
               ('"%s"' % esc(tmr)) if tmr else "null"))


def analytics_noscript() -> str:
    """Пиксели для случая, когда JavaScript отключён."""
    out = []
    ym = ANALYTICS["yandex_metrika_id"]
    tmr = ANALYTICS["top_mail_ru_id"]
    if ym:
        out.append('<noscript><div><img src="https://mc.yandex.ru/watch/%s" alt="" '
                   'style="position:absolute;left:-9999px" width="1" height="1"></div></noscript>' % esc(ym))
    if tmr:
        out.append('<noscript><div><img src="https://top-fwz1.mail.ru/counter?id=%s;js=na" '
                   'alt="" style="position:absolute;left:-9999px" width="1" height="1"></div></noscript>' % esc(tmr))
    return ("\n".join(out) + "\n") if out else ""


# Путь до страницы: (файл, подпись). Первый элемент — всегда главная.
BREADCRUMBS = {
    "program.html": [("index.html", "Главная"), ("education.html", "Обучение"),
                     ("program.html", "Программа повышения квалификации")],
    "effective.html": [("index.html", "Главная"), ("education.html", "Обучение"),
                       ("effective.html", "Инструменты повышения эффективности психотерапии")],
    "survey-clients.html": [("index.html", "Главная"), ("research.html", "Исследование"),
                            ("survey-clients.html", "Опросник для клиентов")],
    "survey-specialists.html": [("index.html", "Главная"), ("research.html", "Исследование"),
                                ("survey-specialists.html", "Опросник для специалистов")],
    "education.html": [("index.html", "Главная"), ("education.html", "Обучение")],
    "research.html": [("index.html", "Главная"), ("research.html", "Исследование")],
    "donate.html": [("index.html", "Главная"), ("donate.html", "Помочь")],
    "reports.html": [("index.html", "Главная"), ("reports.html", "Отчёты")],
    "documents.html": [("index.html", "Главная"), ("documents.html", "Документы")],
    "news.html": [("index.html", "Главная"), ("news.html", "Новости")],
    "about.html": [("index.html", "Главная"), ("about.html", "О нас")],
}


def json_ld(page: dict) -> str:
    """Структурированные данные Schema.org.

    Организация описана как NGO — так поисковики показывают карточку
    с контактами и логотипом. На странице курса дополнительно Course,
    на главной — WebSite. Пишем JSON вручную (json.dumps с ensure_ascii=False),
    чтобы не тянуть зависимости.
    """
    org = {
        "@type": "NGO",
        "@id": SITE_URL + "/#organization",
        "name": ORG["full_name"],
        "alternateName": ORG["name"],
        "url": SITE_URL + "/",
        "logo": SITE_URL + "/assets/img/media/logo.png",
        "image": SITE_URL + "/assets/img/media/hero-figures.jpg",
        "email": ORG["email"],
        "telephone": "+7" + ORG["phone_href"].lstrip("+7"),
        "taxID": ORG["inn"],
        "address": {
            "@type": "PostalAddress",
            "addressCountry": "RU",
            "addressLocality": "Москва",
            "streetAddress": "проспект Мира, д. 202А, кв. 40",
            "postalCode": "129128",
        },
        "sameAs": [url for _, url, _ in SOCIALS],
        "description": "Помогаем людям строить и укреплять «сеть поддержки» из родных, "
                       "друзей и помогающих специалистов.",
        "foundingDate": "2023-04-21",
        "areaServed": {"@type": "Country", "name": "Россия"},
        "knowsLanguage": "ru",
        "contactPoint": {
            "@type": "ContactPoint",
            "contactType": "customer support",
            "email": ORG["email"],
            "telephone": ORG["phone"],
            "availableLanguage": "Russian",
        },
    }

    graph = [org]

    if page["slug"] == "index.html":
        graph.append({
            "@type": "WebSite",
            "@id": SITE_URL + "/#website",
            "url": SITE_URL + "/",
            "name": ORG["name"],
            "inLanguage": "ru-RU",
            "publisher": {"@id": SITE_URL + "/#organization"},
        })

    if page["slug"] == "effective.html":
        graph.append({
            "@type": "Course",
            "name": "Инструменты повышения эффективности психотерапии",
            "description": page["description"],
            "url": SITE_URL + "/effective.html",
            "provider": {"@id": SITE_URL + "/#organization"},
            "inLanguage": "ru-RU",
            "offers": {
                "@type": "Offer",
                "price": "17500",
                "priceCurrency": "RUB",
                "category": "Повышение квалификации",
                "url": SITE_URL + "/effective.html#pay",
            },
            "hasCourseInstance": {
                "@type": "CourseInstance",
                "courseMode": "online",
                "courseWorkload": "PT32H",
                "instructor": {"@type": "Person", "name": "Михаил Пономарёв"},
            },
        })

    if page["slug"] == "program.html":
        graph.append({
            "@type": "Course",
            "name": "Методы и инструменты исследования и активизации социального окружения "
                    "детей и семей",
            "description": page["description"],
            "url": SITE_URL + "/program.html",
            "provider": {"@id": SITE_URL + "/#organization"},
            "inLanguage": "ru-RU",
            "hasCourseInstance": {
                "@type": "CourseInstance",
                "courseMode": "online",
                "courseWorkload": "PT72H",
            },
        })

    # Хлебные крошки: показываются в выдаче вместо голого URL и помогают
    # поисковику понять вложенность разделов.
    if page["slug"] in BREADCRUMBS:
        trail = BREADCRUMBS[page["slug"]]
        graph.append({
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": i + 1,
                    "name": name,
                    "item": SITE_URL + "/" + canonical_path(slug),
                }
                for i, (slug, name) in enumerate(trail)
            ],
        })

    data = {"@context": "https://schema.org", "@graph": graph}
    return ('<script type="application/ld+json">%s</script>\n'
            % json.dumps(data, ensure_ascii=False, separators=(",", ":")))


# Ключевые слова по страницам. Вес у meta keywords сегодня низкий (Google их
# игнорирует, Яндекс учитывает слабо), но для тематических агрегаторов и
# внутреннего поиска поле по-прежнему читают. Основную работу делают
# title, description, H1 и сам текст.
KEYWORDS = {
    "index.html": "сеть социальных контактов, сетевые встречи, помощь семьям в кризисе, "
                  "АНО Дирижабль, профилактика социального сиротства, поддержка семьи, НКО Москва",
    "about.html": "АНО Дирижабль, центр развития социальных практик, работа с сетью социальных "
                  "контактов, сетевая терапия, команда, история организации",
    "news.html": "новости НКО, работа с семьями, сетевые встречи, обучение специалистов, "
                 "Дирижабль новости",
    "research.html": "процедурная справедливость, совместное принятие решений, социальная работа "
                     "с детьми и семьями, исследование, семейные конференции, круги сообщества",
    "survey-clients.html": "опросник для родителей, опросник для подростков, процедурная "
                           "справедливость, исследование социальной работы",
    "survey-specialists.html": "опросник для специалистов, стиль работы, справедливый процесс "
                               "принятия решений, социальная работа",
    "donate.html": "пожертвование, помочь фонду, благотворительность, поддержать НКО, "
                   "помощь семьям, АНО Дирижабль реквизиты",
    "reports.html": "годовой отчёт НКО, отчётность, прозрачность, АНО Дирижабль отчёт",
    "documents.html": "реквизиты, устав, ИНН, ОГРН, документы НКО, персональные данные, оферта",
    "education.html": "повышение квалификации, обучение специалистов, лицензия на образовательную "
                      "деятельность, ДПО, ресурсный центр, социальная работа обучение",
    "program.html": "программа повышения квалификации, 72 часа, карта социальных контактов, "
                    "генограмма, социально-экологический подход, Бронфенбреннер",
    "effective.html": "эффективность психотерапии, шкалы ORS SRS, преднамеренная практика, "
                      "обратная связь в терапии, повышение квалификации психологов, "
                      "Михаил Пономарёв, курс для психологов",
}

# Подтверждение прав в Яндекс.Вебмастере и Google Search Console.
# Без них сайт индексируется медленно и нет данных по запросам.
YANDEX_VERIFICATION = os.environ.get("YANDEX_VERIFICATION", "").strip()
GOOGLE_VERIFICATION = os.environ.get("GOOGLE_VERIFICATION", "").strip()


def verification_meta() -> str:
    out = []
    if YANDEX_VERIFICATION:
        out.append('<meta name="yandex-verification" content="%s">' % esc(YANDEX_VERIFICATION))
    if GOOGLE_VERIFICATION:
        out.append('<meta name="google-site-verification" content="%s">' % esc(GOOGLE_VERIFICATION))
    return ("\n".join(out) + "\n") if out else ""


def keywords_meta(page: dict) -> str:
    kw = KEYWORDS.get(page["slug"])
    return ('<meta name="keywords" content="%s">\n' % esc(kw)) if kw else ""


# Картинка для соцсетей по страницам. Где не задано — общая с главной.
OG_IMAGES = {
    "effective.html": "course-banner.jpg",
    "research.html": "research-cover.jpg",
    "survey-clients.html": "survey-clients.jpg",
    "survey-specialists.html": "survey-specialists.jpg",
    "documents.html": "doc-registration.jpg",
    "news.html": "news-songbook.jpg",
}

# Служебные страницы, которые не должны попадать в поиск
NOINDEX_SLUGS = ("knit-demo.html",)


def robots_meta(page: dict) -> str:
    """Служебные страницы прячем от поиска, остальным — явное разрешение."""
    if page.get("noindex") or page["slug"] in NOINDEX_SLUGS:
        return '<meta name="robots" content="noindex, nofollow">\n'
    return '<meta name="robots" content="index, follow, max-image-preview:large">\n'


def canonical_path(slug: str) -> str:
    """Главная канонизируется на корень: / и /index.html — один и тот же
    документ, и без этого поисковик видит дубль."""
    return "" if slug == "index.html" else slug


def render_head(page: dict) -> str:
    title = page["title"]
    full_title = title if page["slug"] == "index.html" else title + " — " + ORG["name"]
    extra_css = page.get("head_extra", "")
    return """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<script>document.documentElement.classList.add("js")</script>
<title>%s</title>
<meta name="description" content="%s">
%s%s<meta name="theme-color" content="#FBF6EC">
<link rel="canonical" href="%s/%s">

<meta property="og:type" content="website">
<meta property="og:site_name" content="%s">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:url" content="%s/%s">
<meta property="og:image" content="%s/assets/img/media/%s">
<meta property="og:image:alt" content="%s">
<meta property="og:locale" content="ru_RU">
<meta name="twitter:card" content="summary_large_image">
%s
<link rel="icon" href="assets/img/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="assets/img/media/logo.png">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Comfortaa:wght@500;700&amp;family=Nunito:ital,wght@0,400;0,600;0,700;1,400&amp;display=swap&amp;subset=cyrillic,cyrillic-ext,latin">
<link rel="stylesheet" href="%s">
%s%s%s</head>
<body>
<a class="skip-link" href="#main">Перейти к содержимому</a>
%s""" % (
        esc(full_title), esc(page["description"]),
        keywords_meta(page), verification_meta(),
        SITE_URL, canonical_path(page["slug"]),
        esc(ORG["name"]), esc(full_title), esc(page["description"]),
        SITE_URL, canonical_path(page["slug"]),
        SITE_URL, OG_IMAGES.get(page["slug"], "hero-figures.jpg"), esc(page["description"]),
        robots_meta(page),
        asset("assets/css/knit.css"),
        json_ld(page), analytics_config(), extra_css, analytics_noscript(),
    )


def render_header(page: dict) -> str:
    links = []
    for href, label in NAV:
        current = ' aria-current="page"' if href == page["slug"] else ""
        links.append('        <li><a class="nav__link" href="%s"%s>%s</a></li>'
                     % (href, current, esc(label)))
    return """<header class="header">
  <div class="container header__inner">
    <a class="brand" href="index.html">
      <img class="brand__mark" src="assets/img/media/logo.png" alt="" width="1200" height="1200" fetchpriority="high" decoding="async">
      <span class="brand__text">
        <span class="brand__name">Дирижабль</span>
        <span class="brand__sub">Центр развития социальных практик</span>
      </span>
    </a>

    <button class="nav-toggle" type="button" data-nav-toggle aria-expanded="false"
            aria-controls="site-nav" aria-label="Открыть меню">
      <span></span><span></span><span></span>
    </button>

    <nav class="nav" id="site-nav" aria-label="Основная навигация">
      <ul class="nav__list">
%s
        <li class="nav__cta"><a class="btn btn--orange" href="donate.html">%s Помочь</a></li>
      </ul>
    </nav>
  </div>
</header>
<div class="nav-backdrop" data-nav-backdrop></div>
""" % ("\n".join(links), ICONS["heart"])


def render_footer() -> str:
    socials = "\n".join(
        '      <a class="social" href="%s" target="_blank" rel="noopener noreferrer" aria-label="%s">%s</a>'
        % (url, esc(name), ICONS[icon]) for name, url, icon in SOCIALS
    )
    nav_links = "\n".join(
        '        <li><a href="%s">%s</a></li>' % (href, esc(label)) for href, label in NAV
    )
    return """<footer class="footer">
  <div class="container">
    <div class="footer__grid">

      <div>
        <p class="footer__title">Контакты</p>
        <div class="footer__contact">
          <span><strong>%s</strong></span>
          <a href="tel:%s">%s</a>
          <a href="mailto:%s">%s</a>
          <span>%s</span>
        </div>
        <div class="socials">
%s
        </div>
      </div>

      <div>
        <p class="footer__title">Разделы</p>
        <ul class="footer__list">
%s
          <li><a href="donate.html">Помочь</a></li>
          <li><a href="education.html">Обучение</a></li>
          <li><a href="effective.html">Курс по эффективности психотерапии</a></li>
        </ul>
      </div>

      <div>
        <p class="footer__title">Документы</p>
        <ul class="footer__list">
          <li><a href="education.html">Образовательные услуги и лицензия</a></li>
          <li><a href="%s" target="_blank" rel="noopener noreferrer">Положение о защите персональных данных</a></li>
          <li><a href="%s" target="_blank" rel="noopener noreferrer">Политика о персональных данных</a></li>
          <li><a href="%s" target="_blank" rel="noopener noreferrer">Договор присоединения (оферта)</a></li>
          <li><a href="%s" target="_blank" rel="noopener noreferrer">Проверенная благотворительность</a></li>
        </ul>
      </div>

    </div>

    <p class="mt-3 muted" style="max-width:60ch">Мы работаем очно в Москве; обучение специалистов — онлайн или выезды по всей России.</p>

    <div class="footer__bottom">
      <span>© %s</span>
      <span>ИНН %s · ОГРН %s</span>
      <span>Делая пожертвование, вы соглашаетесь с <a href="%s" target="_blank" rel="noopener noreferrer">договором присоединения</a>.</span>
    </div>
  </div>
</footer>
""" % (
        esc(ORG["short"]), ORG["phone_href"], ORG["phone"], ORG["email"], ORG["email"],
        esc(ORG["address"]), socials, nav_links,
        PDF["privacy_policy"], PDF["personal_data"], PDF["offer"], CHECKED_CHARITY,
        esc(ORG["full_name"]), ORG["inn"], ORG["ogrn"], PDF["offer"],
    )


def render_scripts(page: dict) -> str:
    out = ['<script src="%s" defer></script>' % asset("assets/js/analytics.js"),
           '<script src="%s" defer></script>' % asset("assets/js/app.js")]
    if page.get("articles"):
        out.append('<script src="%s" defer></script>' % asset("assets/js/articles.js"))
    if page.get("donation") and DONATION["widget_id"]:
        out.append('<script src="%s" async></script>' % donation_loader_url())
    return "\n".join(out)


def render_page(page: dict) -> str:
    return (
        render_head(page)
        + render_header(page)
        + '<main id="main">\n'
        + page["body"].strip()
        + "\n</main>\n"
        + render_footer()
        + render_scripts(page)
        + "\n</body>\n</html>\n"
    )


# --------------------------------------------------------------------------
# переиспользуемые блоки
# --------------------------------------------------------------------------

TEAM = [
    ("team-indakova.jpg", "Елена Индакова", 'Учредитель АНО «Дирижабль», сетевой терапевт, социальный педагог'),
    ("team-archakova.jpg", "Татьяна Арчакова", "Директор АНО Центр развития социальных практик «Дирижабль»"),
    ("team-ponomarev.jpg", "Михаил Пономарёв", "Сетевой терапевт, клинический психолог, к. пс. н."),
    ("team-evsteshina.jpg", "Ольга Евстешина", "Сетевой терапевт, тренер и супервизор по технологии «Работа с сетью социальных контактов»"),
    ("team-romanova.jpg", "Васанта Романова", "Сетевой терапевт, тренер и супервизор по технологии «Работа с сетью социальных контактов», к. пс. н."),
    ("team-kuznetsova.jpg", "Мария Кузнецова", "Сетевой терапевт, тренер и супервизор по технологии «Работа с сетью социальных контактов»"),
    ("team-abakarova.jpg", "Фатима Абакарова", "Менеджер проектов"),
    ("team-mikhaylova.jpg", "Инна Михайлова", "Куратор семей, психолог"),
]

PARTNERS = [
    ("partner-potanin.png", "Благотворительный фонд Владимира Потанина", "https://fondpotanin.ru/"),
    ("partner-absolut.jpg", "БФ «Абсолют-Помощь»", "https://www.absolute-help.ru/"),
    ("partner-centervnl.png", "Центр помощи семьям им. священномученика Константина Верецкого", "https://centervnl.ru/"),
    ("partner-delasemeynye.jpg", "«Дела семейные»", "https://delasemeynye.ru/"),
    ("partner-otkazniki.jpg", "Фонд «Волонтёры в помощь детям-сиротам»", "https://otkazniki.ru/"),
    ("partner-victoria.jpg", "Благотворительный детский фонд «Виктория»", "https://victoriacf.ru/"),
]


def team_section() -> str:
    people = []
    for f, name, role in TEAM:
        people.append(
            '      <figure class="person reveal">\n'
            "        %s\n"
            '        <figcaption>\n'
            '          <span class="person__name">%s</span>\n'
            '          <span class="person__role">%s</span>\n'
            "        </figcaption>\n"
            "      </figure>" % (img(f, "Портрет: " + name, "person__photo"), esc(name), esc(role))
        )
    return """<section class="section section--wool" aria-labelledby="team-title">
  <div class="container">
    <div class="section-head section-head--center">
      <p class="eyebrow">Кто вяжет эту сеть</p>
      <h2 id="team-title"><span class="stitched-title">Наша команда</span></h2>
    </div>
    <div class="team-grid">
%s
    </div>
  </div>
</section>""" % ("\n".join(people))


def partners_section() -> str:
    cards = []
    for f, name, url in PARTNERS:
        cards.append(
            '      <a class="partner" href="%s" target="_blank" rel="noopener noreferrer" title="%s">\n'
            "        %s\n"
            '        <span class="visually-hidden">%s (откроется в новой вкладке)</span>\n'
            "      </a>" % (url, esc(name), img(f, name), esc(name))
        )
    return """<section class="section section--tight" aria-labelledby="partners-title">
  <div class="container">
    <div class="section-head section-head--center">
      <p class="eyebrow">Вяжем не в одиночку</p>
      <h2 id="partners-title">Наши партнёры</h2>
    </div>
    <div class="partners">
%s
    </div>
  </div>
</section>""" % ("\n".join(cards))


def case_help_section(eyebrow: str, heading_id: str, heading: str,
                      vanya_text: str, brothers_text: str) -> str:
    """Блок со ссылками на адресные сборы.

    Пока SHOW_CASE_PAGES выключен, возвращает пустую строку: сами страницы
    не собираются, и ссылки на них вели бы в никуда (check.py это ловит).
    """
    if not SHOW_CASE_PAGES:
        return ""

    return """<section class="section section--purl" aria-labelledby="%s">
  <div class="container">
    <div class="section-head section-head--center">
      <p class="eyebrow">%s</p>
      <h2 id="%s">%s</h2>
    </div>
    <div class="grid grid--2">
      <a class="card article-card card--link reveal" href="help-vanya.html">
        %s
        <div class="article-card__body">
          <h3 class="article-card__title">Помогите Ване и его близким</h3>
          <p class="article-card__text">%s</p>
        </div>
      </a>
      <a class="card article-card card--link reveal" href="help-brothers.html">
        %s
        <div class="article-card__body">
          <h3 class="article-card__title">Не прогулять своё будущее</h3>
          <p class="article-card__text">%s</p>
        </div>
      </a>
    </div>
  </div>
</section>
""" % (
        esc(heading_id), esc(eyebrow), esc(heading_id), esc(heading),
        img("vanya-main.jpg", "Ваня дома", "article-card__media", focus="50% 25%"),
        vanya_text,
        img("brothers-main.jpg", "Максим и Коля", "article-card__media", focus="55% 20%"),
        brothers_text,
    )


def donate_cta(title: str = "Поддержите «сеть поддержки»",
               text: str = "Любое пожертвование помогает семьям удержаться на плаву и найти опору среди близких.") -> str:
    return """<section class="section section--purl scallop-bottom" aria-labelledby="cta-title">
  <div class="container text-center">
    <h2 id="cta-title"><span class="stitched-title">%s</span></h2>
    <p class="lead center-x" style="max-width:56ch">%s</p>
    <p class="cluster cluster--center mt-2">
      <a class="btn btn--orange btn--lg" href="donate.html">%s Сделать пожертвование</a>
      <a class="btn btn--ghost btn--lg" href="documents.html">Реквизиты организации</a>
    </p>
  </div>
</section>""" % (esc(title), esc(text), ICONS["heart"])


def donate_widget_block(anchor_note: str = "", form: str = "") -> str:
    """Блок платёжной формы.

    Виджету donation.ru нужна точка монтирования <mixplat-form> с id формы —
    без неё загрузчик создаёт пустой <span> в конце <body>, и форма
    не появляется. Именно так форма была вставлена в выгрузке Craftum.
    """
    # form — ключ отдельной формы ("vanya", "brothers"); пусто → общая
    form_id = DONATION.get("form_id_" + form, "") if form else ""
    if not form_id:
        form_id = DONATION["form_id"]

    mount = ""
    if form_id:
        mount = ('\n  <mixplat-form data-type="mixplat-form" id="%s"></mixplat-form>'
                 % esc(form_id))

    loading = ('<p class="muted" data-donate-loading>Форма пожертвования загружается…</p>'
               if DONATION["widget_id"] else "")

    # Без идентификаторов (локальная сборка) запасной блок показываем сразу,
    # не дожидаясь таймаута в app.js.
    hidden = " hidden" if DONATION["widget_id"] else ""

    return """<div class="donate-widget" data-donate-widget data-donate-style="%s">
  %s%s
  <div class="donate-fallback" data-donate-fallback%s>
    <p><strong>Форма пожертвования сейчас недоступна.</strong> Так бывает при офлайн-просмотре
    или если внешний виджет заблокирован. Перевести помощь можно напрямую по реквизитам.</p>
    <p class="cluster">
      <a class="btn" href="documents.html#requisites">Открыть реквизиты</a>
      <a class="btn btn--ghost" href="mailto:%s">Написать нам</a>
    </p>
  </div>
</div>%s""" % (asset("assets/css/donate-widget.css"), loading, mount, hidden,
            ORG["email"], anchor_note)


# --------------------------------------------------------------------------
# страницы
# --------------------------------------------------------------------------

PAGES = []


def page(slug, title, description, body, **kw):
    entry = {"slug": slug, "title": title, "description": description, "body": body}
    entry.update(kw)
    PAGES.append(entry)


# ---------------------------------------------------------------- главная

page(
    "index.html",
    "АНО «Дирижабль» — сеть поддержки для семей в кризисе",
    "Помогаем людям строить и укреплять «сеть поддержки» из родных, друзей и помогающих "
    "специалистов. Сетевые встречи, обучение специалистов, адресная помощь семьям.",
    """
<section class="hero">
  <div class="container">
    %s
    %s
    <div class="hero__grid">
      <div>
        <p class="eyebrow">Центр развития социальных практик</p>
        <h1 class="hero__title">Мы вяжем <span class="stitched-title">страховочную сеть</span> для семей в кризисе</h1>
        <p class="lead">Наша миссия — помогать людям строить, укреплять и налаживать свою «сеть поддержки»
        из родных, друзей и помогающих специалистов.</p>
        <div class="hero__actions">
          <a class="btn btn--orange btn--lg" href="donate.html">%s Поддержать нас</a>
          <a class="btn btn--ghost btn--lg" href="about.html">Как это работает</a>
        </div>
      </div>
      <div class="knit-frame">
        %s
      </div>
    </div>
  </div>
</section>

<div class="container"><div class="cable-divider" role="presentation"></div></div>

<section class="section section--tight">
  <div class="container">
    <p class="lead center-x text-center" style="max-width:72ch">
      Мы помогаем людям представить себе хорошее будущее и идти туда, опираясь на свои сильные стороны.
      Собираем их родственников и друзей, учителей, врачей или соцработников, чтобы вместе решить
      реальные проблемы: от прогулов школы до угрозы попадания ребёнка под опеку государства.
    </p>
  </div>
</section>

<section class="section" aria-labelledby="what-title">
  <div class="container">
    <div class="section-head section-head--center">
      <p class="eyebrow">Три петли нашей работы</p>
      <h2 id="what-title">Что мы делаем</h2>
    </div>
    <div class="grid grid--3">
      <article class="card card--patch reveal">
        <span class="card__num">1</span>
        <h3 class="card__title">Проводим сетевые встречи</h3>
        <p class="card__text">Ведём сетевые встречи и похожие форматы по запросу коллег в Москве и Подмосковье.
        Разгружаем специалистов и помогаем взглянуть на сложный случай «изнутри круга».</p>
      </article>
      <article class="card card--patch reveal">
        <span class="card__num">2</span>
        <h3 class="card__title">Обучаем специалистов</h3>
        <p class="card__text">Учим команды в регионах, ведём сообщество в Telegram, проводим супервизии,
        интервизии и мероприятия по обмену опытом.</p>
      </article>
      <article class="card card--patch reveal">
        <span class="card__num">3</span>
        <h3 class="card__title">Внедряем и исследуем</h3>
        <p class="card__text">Помогаем закрепить технологию в организации и на территории. Исследуем
        результативность, собираем и описываем новые идеи из практики.</p>
      </article>
    </div>
  </div>
</section>

%s

%s

%s

%s
""" % (
        yarn("pompom--tr"), yarn("pompom--bl"), ICONS["heart"],
        img("hero-figures.jpg", "Разноцветные фигурки людей стоят кругом на столе во время сетевой встречи",
            eager=True, sizes="(min-width: 900px) 45vw, 92vw"),
        case_help_section(
            "Адресная помощь", "help-title", "Кому нужна помощь прямо сейчас",
            "Ване 7 лет, у него аутизм. Маме нужна передышка: няня, умеющая работать "
            "с «особыми» детьми, и поддержка психолога.",
            "Максиму 16, Коле 14. Братья перестали учиться. Нужны тьютор, психолог "
            "и репетиторы, чтобы Максим сдал ОГЭ."),
        team_section(), partners_section(), donate_cta(),
    ),
)

# ------------------------------------------------------------------ о нас

page(
    "about.html",
    "О нас",
    "История, миссия и команда АНО «Дирижабль»: технология работы с сетью социальных контактов "
    "и развитие практик поддержки семей.",
    """
<section class="section">
  <div class="container">
    <div class="section-head">
      <p class="eyebrow">О нас</p>
      <h1>Практикуем, распространяем и совершенствуем работу с окружением</h1>
      <p class="lead">Наша цель — практиковать, распространять и совершенствовать технологии работы
      с социальным окружением людей, которым нужна поддержка.</p>
    </div>

    <h2 class="visually-hidden">Направления работы</h2>
    <div class="grid grid--3">
      <article class="card card--patch reveal">
        <h3 class="card__title">Сетевые встречи</h3>
        <p class="card__text">Проводим сетевые встречи и другие похожие форматы по запросу наших коллег
        в Москве и Подмосковье. Разгружаем коллег, помогаем им посмотреть на сложные случаи новым
        взглядом — «изнутри круга».</p>
      </article>
      <article class="card card--patch reveal">
        <h3 class="card__title">Обучение и сообщество</h3>
        <p class="card__text">Обучаем команды специалистов в регионах, ведём сообщество в Telegram,
        проводим супервизии, интервизии и мероприятия по обмену опытом.</p>
      </article>
      <article class="card card--patch reveal">
        <h3 class="card__title">Внедрение и исследования</h3>
        <p class="card__text">Помогаем внедрять технологию, чтобы она сохранялась и развивалась
        в организации и на территории. Исследуем результативность, собираем и описываем новые идеи
        из практики.</p>
      </article>
    </div>
  </div>
</section>

<section class="section section--purl" aria-labelledby="history-title">
  <div class="container">
    <div class="grid grid--2" style="align-items:center">
      <div class="prose">
        <p class="eyebrow">Как всё начиналось</p>
        <h2 id="history-title">История</h2>
        <p>В 2003 году технология работы с сетью социальных контактов пришла из Швеции в Москву
        (в СРЦ «Отрадное») и стала распространяться по всей России. Многие участники нашей команды
        уже тогда начали проводить сетевые встречи, а чуть позже стали тренерами тренеров
        по этой технологии.</p>
        <p>С 2016 года мы проводили обучение для государственных и некоммерческих организаций
        из регионов на базе Благотворительного детского фонда «Виктория» и проводили сетевые
        встречи в Москве по запросу других организаций.</p>
        <p>Мы объединились, чтобы развивать практики работы с социальным окружением
        благополучателей — детей и семей.</p>
      </div>
      <div class="swatch" style="padding:clamp(1.5rem,4vw,2.5rem)">
        <p class="eyebrow">Наша цель</p>
        <p class="lead mb-0">Сделать социальную работу, образование и медицину пространством,
        где человек занимает активную позицию и создаёт поддерживающие горизонтальные связи.</p>
      </div>
    </div>
  </div>
</section>

%s

%s

%s
""" % (team_section(), partners_section(), donate_cta()),
)

# ---------------------------------------------------------------- новости

page(
    "news.html",
    "Новости",
    "Новости АНО «Дирижабль»: проекты, обучение специалистов и «не-истории» из практики "
    "работы с сетью социальных контактов.",
    """
<section class="section section--tight">
  <div class="container">
    <p class="eyebrow">Новости и не-истории</p>
    <h1>Что у нас происходит</h1>
    <p class="lead" style="max-width:62ch">Мы рассказываем о работе так, чтобы не раскрывать целиком
    истории людей, которым помогаем. Отсюда и «не-истории»: песенник, рецепт, буклет — любой формат,
    кроме прямого пересказа чужой жизни.</p>
  </div>
</section>

<section class="section section--tight" aria-labelledby="feed-title">
  <div class="container" data-articles data-articles-endpoint="assets/data/articles.json" data-articles-per-page="6">
    <h2 id="feed-title" class="visually-hidden">Лента материалов</h2>
    <div class="tags" data-articles-tags role="group" aria-label="Фильтр по темам"></div>
    <p class="feed-status" data-articles-status hidden></p>
    <noscript><p class="feed-status">Лента материалов подгружается скриптом. Включите JavaScript
    или откройте разделы ниже — все тексты доступны на странице.</p></noscript>
    <div class="grid grid--3" data-articles-list></div>
    <p class="cluster cluster--center mt-2">
      <button type="button" class="btn btn--ghost" data-articles-more hidden>Показать ещё</button>
    </p>
  </div>
</section>

<div class="container"><div class="cable-divider" role="presentation"></div></div>

<article class="section" id="absolut" aria-labelledby="absolut-title">
  <div class="container container--narrow prose">
    <p class="eyebrow">Проекты</p>
    <h2 id="absolut-title">Завершился проект с БФ «Абсолют-Помощь»</h2>
    <p>В январе завершился проект «Работа с сетью социальных контактов: сопровождение детей и семей
    с вовлечением их окружения», поддержанный БФ «Абсолют-Помощь». Мы очень благодарны коллегам
    и продолжаем работать.</p>
    <p>Вот что нам даётся сложно — так это рассказывать о наших успехах.</p>
    <p><strong>Во-первых</strong>, мы точно знаем, что наш вклад — только часть успеха. Изменения
    достигнуты благодаря огромным усилиям людей, которые получают у нас помощь, и их близких.</p>
    <p><strong>Во-вторых</strong>, герои историй могут быть узнаваемы даже под псевдонимами: мы работаем
    с социальными связями, а «конфигурация» родственников и друзей у всех уникальна, как отпечатки пальцев.</p>
    <p><strong>В-третьих</strong>, жизнь изменчива. Бывает, что история о сегодняшних успехах завтра
    превращается в историю о новых трудностях. Пусть ты согласился публично поделиться своей историей —
    но каково читать о том, какой ты молодец… был неделю назад.</p>
    <p>Мы решили обыграть третье возражение и сделали список того, как наши благополучатели умеют
    справляться в мире, где концовка «и жили они долго и счастливо» бывает только в сказках:</p>
    <ul class="knit-list">
      <li>Можно столкнуться с несправедливостью и снова обратиться за утешением к алкоголю — но
      остановиться, чтобы срыв не превратился в рецидив.</li>
      <li>Можно снизить планку требований к образованию ребёнка и обнаружить, что это для него
      не проигрыш, а первый опыт успеха.</li>
      <li>Можно обнаружить себя повторяющим старые поведенческие паттерны в отношениях — но заметить
      это и сразу обратиться за помощью.</li>
      <li>Можно признаться в своих ошибках не только близким, но даже официальным органам, и тебя
      не только не накажут, но и будут больше доверять.</li>
      <li>Можно не попасть на реабилитацию в «то самое место, где точно помогут», зато пойти работать,
      чтобы отвлечься от соблазнов, и в первый же месяц стать «работником месяца».</li>
    </ul>
    <p>Проблемы не кончаются, но люди всё лучше с ними справляются. Так выглядит устойчивость
    социальных результатов.</p>
    <p>Мы многому учимся у наших клиентов. Нам ценно наблюдать, как они преодолевают трудности
    и движутся к лучшему будущему. Но есть сомнения, как этично рассказывать их истории. Ими —
    сомнениями — мы уже делились и попробовали вместо истории сделать
    <a href="https://t.me/dirigible_community/48" target="_blank" rel="noopener noreferrer">Список умений</a>.</p>
    <p>Постепенно мы вошли во вкус и решили расширить рамки истории. Пусть это будет не повествование,
    а страничка из песенника, кулинарный рецепт или рекламный буклет. Всё сойдёт — будем делиться
    с вами не-историями.</p>
  </div>
</article>

<article class="section section--purl" id="songbook" aria-labelledby="songbook-title">
  <div class="container">
    <div class="grid grid--2" style="align-items:start">
      <div class="knit-frame knit-frame--flat">
        %s
      </div>
      <div class="prose">
        <p class="eyebrow">Не-история</p>
        <h2 id="songbook-title">Песенник</h2>
        <p><strong>Первый куплет.</strong> Почему соседи нашего офиса удивлены? Из окна первого этажа
        раздаются песни «Сектора Газа». Наш куратор Елена не вспоминает панковскую молодость — она
        работает с Валентиной*. Валентине 20 лет, у неё есть особенности развития, она живёт с мамой
        и бабушкой. Они работают над тем, чтобы дать Валентине капельку больше самостоятельности,
        а маме — найти больше поддержки. А Валентина… любит панк-рок.</p>
        <p><strong>Припев.</strong> Запоёшь тут, когда молодой девушке не хватает компании сверстников
        для тусовки. Ведь никакие особенности развития не отменяют этот жизненный этап. Поэтому нам
        так важно создать «сеть поддержки» — включая дружескую.</p>
        <p><strong>Второй куплет.</strong> Сейчас у семьи есть подвижки в общении с близкими
        родственниками. Специалисты из ЦЛП на оплаченных нами консультациях не только удачно
        скорректировали лечение, но и дали надежду, что однажды Валентина сможет жить почти сама,
        в формате сопровождаемого проживания.</p>
        <p><strong>Припев.</strong> Пусть воздух ядовит, как ртуть, и пусть не видно, где свернуть —
        но мы [вместе с «сетью поддержки»] пройдём опасный путь через туман.</p>
        <p class="full-bleed-note">* Имя изменено.</p>
      </div>
    </div>
  </div>
</article>

<article class="section" id="rostov" aria-labelledby="rostov-title">
  <div class="container">
    <div class="section-head">
      <p class="eyebrow">Обучение · 15–17 октября</p>
      <h2 id="rostov-title">Семинар в Ростове-на-Дону</h2>
      <p class="lead">Трёхдневный семинар собрал около тридцати специалистов из разных населённых
      пунктов региона. Семинар проходил в формате практической работы над конкретными кейсами.</p>
    </div>

    %s

    <div class="prose mt-3">
      <p>Наши партнёры — АНО «Центр помощи семьям в кризисной ситуации им. священномученика
      Константина Верецкого» — при поддержке Фонда Потанина реализуют проект «Сеть социальных
      контактов: Ростовская область». Часть нашей команды — Татьяна Арчакова и Мария Кузнецова —
      приглашённые тренеры на курсе.</p>
      <p>Проект начался в августе, и мы провели уже пять вебинаров. На них участники познакомились
      с тем, как исследовать социальное окружение клиентов и составлять «Карты социальных контактов».</p>
      <p>15–17 октября Мария Кузнецова провела три дня очного семинара для 30 специалистов
      в Ростове-на-Дону — приезжали и из других городов: Таганрога, Волгодонска, Новочеркасска.</p>
      <p>На очный семинар участники пришли уже с картами реальных клиентов и на материале их случаев
      моделировали проведение сетевой встречи. Часть участников брала на себя различные роли —
      родителя, подростка, бабушки или специалиста органов опеки, — а другие в это время тренировали
      навыки ведущих.</p>
      <p>Впечатления от процесса были яркими, потому что случаи подобрались непростые. Иногда хотелось
      всплеснуть руками: «Где же были родственники или соседи, когда люди поступали так необдуманно?»
      Но в этом и смысл: тренинг учил привлекать этих самых родственников и соседей к помощи семье,
      чтобы никто не оставался в стороне.</p>
    </div>
  </div>
</article>

%s
""" % (
        img("news-songbook.jpg", "Куратор Елена с гитарой на фоне разворота песенника с песней «Туман» группы «Сектор Газа»"),
        carousel([
            '    <div class="knit-frame knit-frame--flat">%s</div>'
            % img("rostov-1.jpg", "Участники семинара в Ростове-на-Дону за работой"),
            '    <div class="knit-frame knit-frame--flat">%s</div>'
            % img("rostov-2.jpg", "Работа над кейсом на семинаре в Ростове-на-Дону"),
            '    <div class="knit-frame knit-frame--flat">%s</div>'
            % img("rostov-3.jpg", "Специалисты на семинаре в Ростове-на-Дону"),
        ], "Фотографии с семинара в Ростове-на-Дону"),
        donate_cta(),
    ),
    articles=True,
)

# ----------------------------------------------------------- исследование

page(
    "research.html",
    "Исследование процедурной справедливости",
    "Исследуем процедурную справедливость при совместном принятии решений в социальной работе "
    "с детьми и семьями: как сделать нашу работу более справедливой.",
    """
<section class="section">
  <div class="container">
    <div class="grid grid--2" style="align-items:center">
      <div>
        <p class="eyebrow">Исследование</p>
        <h1>Процедурная справедливость при совместном принятии решений</h1>
        <p class="lead">Как сделать социальную работу с детьми и семьями более справедливой?</p>
      </div>
      <div class="knit-frame">
        %s
      </div>
    </div>
  </div>
</section>

<section class="section section--purl">
  <div class="container container--narrow prose">
    <p>В работе с семьями мы постоянно принимаем какие-то решения: сами лично, с коллегами
    или с клиентами. Но всегда ли мы понимаем, «как слово наше отзовётся»?</p>
    <h2>Мы проводим исследование, чтобы</h2>
    <ul class="knit-list">
      <li>узнать, как клиенты (родители и подростки) и специалисты определяют для себя, что такое
      «справедливый процесс» принятия решения;</li>
      <li>разработать и апробировать инструменты для оценки справедливости в сфере помощи семьям
      и детям;</li>
      <li>выяснить, как переживаемая «справедливость» процесса влияет на воплощение принятых
      решений в жизнь.</li>
    </ul>
    <p>Мы фокусируемся именно на процессах совместного принятия решений: сетевые встречи, семейные
    конференции, круги сообщества, семейная медиация, консилиумы с участием благополучателей,
    общие собрания клиентов, проживающих в кризисных центрах.</p>
    <p class="lead"><strong>Мы верим:</strong> чувство «со мной обращаются справедливо» — важный
    фактор благополучия детей в трудной жизненной ситуации.</p>
  </div>
</section>

<section class="section" aria-labelledby="research-surveys-title">
  <div class="container">
    <div class="section-head">
      <h2 id="research-surveys-title">Опросники</h2>
      <p class="muted">Помогите исследованию: пройдите опросник сами и перешлите его коллегам
      или клиентам.</p>
    </div>
    <div class="grid grid--2">
      <a class="card article-card card--link reveal" href="survey-clients.html">
        %s
        <div class="article-card__body">
          <span class="article-card__date">24 мая 2026</span>
          <h3 class="article-card__title">Опросник для родителей, подростков или молодых взрослых</h3>
          <p class="article-card__text">Пожалуйста, поделитесь опросником со своими клиентами,
          у которых был опыт участия в процессах совместного принятия решений.</p>
        </div>
      </a>
      <a class="card article-card card--link reveal" href="survey-specialists.html">
        %s
        <div class="article-card__body">
          <span class="article-card__date">24 мая 2026</span>
          <h3 class="article-card__title">Опросник для специалистов о стиле работы,
          обеспечивающем справедливый процесс принятия решений</h3>
          <p class="article-card__text">Пожалуйста, пройдите опросник и перешлите коллегам.</p>
        </div>
      </a>
    </div>
  </div>
</section>

<section class="section section--tight" id="participate">
  <div class="container container--narrow">
    <div class="swatch text-center" style="padding:clamp(1.75rem,5vw,3rem)">
      <h2 class="mt-0">Хотите участвовать?</h2>
      <p class="lead center-x" style="max-width:52ch">Если вы специалист или организация
      и вам близка тема — напишите нам, расскажем подробнее об участии в исследовании.</p>
      <p class="cluster cluster--center mt-2">
        <a class="btn" href="mailto:%s?subject=%s">Написать об исследовании</a>
        <a class="btn btn--ghost" href="https://t.me/dirigible_community" target="_blank" rel="noopener noreferrer">Сообщество в Telegram</a>
      </p>
    </div>
  </div>
</section>

%s
""" % (
        img("research-cover.jpg", "Вязаная иллюстрация: дерево «Справедливый процесс», люди собирают плоды, в кроне сердце с надписью «Качество решения»"),
        img("survey-clients.jpg",
            "Вязаная фигурка подростка заполняет анкету за столом рядом с вязаным ноутбуком",
            "article-card__media"),
        img("survey-specialists.jpg",
            "Вязаная фигурка психолога с блокнотом, на котором отмечен ответ о справедливости в работе",
            "article-card__media"),
        ORG["email"], "Исследование%20процедурной%20справедливости",
        donate_cta(),
    ),
)

# --------------------------------------------------------------- помочь

page(
    "donate.html",
    "Помочь",
    "Поддержите АНО «Дирижабль»: разовое или регулярное пожертвование, адресная помощь семьям.",
    """
<section class="section section--tight">
  <div class="container">
    <p class="eyebrow">Помочь</p>
    <h1>Сделать пожертвование</h1>
    <p class="lead" style="max-width:60ch">Ваша помощь оплачивает работу кураторов семей, психологов,
    нянь и репетиторов — и позволяет собирать вокруг ребёнка людей, которые останутся рядом
    и после того, как мы завершим работу.</p>
  </div>
</section>

<section class="section section--tight">
  <div class="container container--narrow">
    %s
  </div>
</section>

%s

<section class="section">
  <div class="container container--narrow">
    <h2>Другие способы помочь</h2>
    <div class="accordion mt-2">
      <details class="acc">
        <summary class="acc__summary">Перевести по банковским реквизитам</summary>
        <div class="acc__body">
          <p>Подойдёт, если вы переводите от организации или хотите указать назначение платежа.
          Полные реквизиты — на странице <a href="documents.html#requisites">Документы</a>.</p>
        </div>
      </details>
      <details class="acc">
        <summary class="acc__summary">Рассказать о нас</summary>
        <div class="acc__body">
          <p>Поделитесь ссылкой на сайт или нашим <a href="https://t.me/dirigible_community" target="_blank" rel="noopener noreferrer">каналом в Telegram</a>.
          Чем больше специалистов знают о работе с сетью социальных контактов, тем больше семей получат помощь.</p>
        </div>
      </details>
      <details class="acc">
        <summary class="acc__summary">Пригласить нас к сотрудничеству</summary>
        <div class="acc__body">
          <p>Мы проводим сетевые встречи по запросу коллег, обучаем команды в регионах и помогаем
          внедрять технологию. Напишите на <a href="mailto:%s">%s</a>.</p>
        </div>
      </details>
    </div>
  </div>
</section>
""" % (
        donate_widget_block(),
        case_help_section(
            "Адресная помощь", "address-help-title", "Конкретные сборы",
            "Няня для Вани и психолог для мамы Елены на 3 месяца.",
            "Тьютор, психолог и репетиторы для Максима и Коли."),
        ORG["email"], ORG["email"],
    ),
    donation=True,
)

# ------------------------------------------------------- адресная помощь

CASE_EXPERT = """<section class="section section--purl" aria-labelledby="expert-title">
  <div class="container container--narrow">
    <h2 id="expert-title" class="text-center">Мнение эксперта</h2>
    <div class="quote mt-2">
      <div class="quote__head">
        %s
        <div class="quote__who">
          <span class="quote__name">Ольга Ивановна Евстешина</span>
          <span class="quote__role">Медицинский психолог, дефектолог в ГБУЗ «Научно-практический центр
          психического здоровья детей и подростков им. Г. Е. Сухаревой»; сетевой терапевт в АНО «Дирижабль»</span>
        </div>
      </div>
      <div class="prose">%s</div>
    </div>
  </div>
</section>"""


def case_expert(body_html: str) -> str:
    return CASE_EXPERT % (
        img("team-evsteshina.jpg", "Портрет: Ольга Евстешина", "quote__avatar"),
        body_html,
    )


page(
    "help-vanya.html",
    "Помогите Ване и его близким",
    "Адресный сбор: няня для семилетнего Вани с аутизмом и психологическая поддержка "
    "для его мамы Елены.",
    """
<section class="section section--tight">
  <div class="container">
    <p class="eyebrow"><a href="donate.html">Адресная помощь</a></p>
    <h1>Помогите Ване и его близким</h1>
  </div>
</section>

<section class="section section--tight">
  <div class="container">
    <div class="case-header">
      <div class="knit-frame">
        %s
      </div>
      <div>
        <h2 class="mt-0">Ваня</h2>
        <dl class="case-facts">
          <div class="case-fact"><dt>Возраст</dt><dd>7 лет</dd></div>
          <div class="case-fact"><dt>Проблема</dt><dd>Аутизм</dd></div>
          <div class="case-fact"><dt>Ситуация в семье</dt><dd>Мать — вдова, родственники живут в другом регионе</dd></div>
        </dl>
        <div class="swatch mt-2" style="padding:1.4rem">
          <h3 class="mt-0">Что можно сделать?</h3>
          <p class="mb-0">Обеспечить помощь профессиональной няни, умеющей работать с «особыми» детьми,
          и психологическую поддержку для мамы. Тогда у Вани повысятся шансы адаптироваться в школе,
          а мама сможет заняться своим здоровьем.</p>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="container container--narrow prose">
    <p>Ване 7 лет, и у него аутизм. Когда его переполняют эмоции, он кусает маму и делает больно
    самому себе.</p>
    <p>Его мама Елена надеялась, что когда он пойдёт в специализированную школу и адаптируется там,
    ситуация наладится. Но уже в первом классе у Вани сменился любимый учитель, и всё стало ещё хуже.
    После уроков он сидит около охранника и ждёт маму — никто не может уговорить его подняться в класс.
    Потом кто-то из педагогов не выдерживает и звонит Елене. А когда грустно самой Елене, то ей звонить
    некому: несколько лет назад она овдовела.</p>
    <p>Елена была бы рада сосредоточиться на Ване, но у неё есть ещё проблемы. Во-первых, ей самой нужно
    срочно пройти медицинское обследование. Во-вторых, она не может работать, и семья живёт только
    на пособие по инвалидности.</p>
    <p>Что вообще можно сделать? Поддержать маму, чтобы она не свалилась с ног, а Ваня не попал
    в учреждение. Для этого нужна регулярная помощь психолога для мамы и работа няни, которая хотя бы
    отпустит маму к врачу.</p>
  </div>
</section>

<section class="section section--tight">
  <div class="container">
    <div class="gallery">
      %s
      %s
    </div>
  </div>
</section>

%s

<section class="section" id="donate">
  <div class="container container--narrow text-center">
    <h2>Помогите Ване остаться с мамой</h2>
    <p class="lead center-x" style="max-width:56ch">Для оплаты няни для Вани и психолога для мамы Елены
    на 3 месяца нужны 93 000 ₽. За это время мама восстановит своё здоровье и силы, а мы вместе
    с педагогами из школы поможем Ване адаптироваться в классе.</p>
  </div>
  <div class="container container--narrow mt-2">
    %s
  </div>
</section>
""" % (
        img("vanya-main.jpg", "Ваня дома", eager=True),
        img("vanya-1.jpg", "Ваня"),
        img("vanya-2.jpg", "Ваня"),
        case_expert(
            "<p>Воспитывать высокочувствительного ребёнка с трудным поведением без помощи расширенной "
            "семьи — это не просто «сложно». Это уровень стресса, который можно сравнить с тем, что "
            "человек испытывает в зоне боевых действий или на орбите в космосе.</p>"
            "<p>Куратор семьи в АНО «Дирижабль» вместе с Еленой исследует возможности привлекать "
            "поддержку родственников, но все её родные живут далеко. Пока она вынуждена справляться одна.</p>"
            "<p>Необходимо снизить уровень стресса хотя бы на время, чтобы не доводить до плачевных "
            "последствий здоровье мамы и дать опору ребёнку.</p>"
        ),
        donate_widget_block(form="vanya"),
    ),
    donation=True,
)

page(
    "help-brothers.html",
    "Не прогулять своё будущее",
    "Адресный сбор для братьев Максима и Коли: тьютор, психолог и репетиторы, чтобы вернуться "
    "к учёбе и сдать ОГЭ.",
    """
<section class="section section--tight">
  <div class="container">
    <p class="eyebrow"><a href="donate.html">Адресная помощь</a></p>
    <h1>Не прогулять своё будущее</h1>
  </div>
</section>

<section class="section section--tight">
  <div class="container">
    <div class="case-header">
      <div class="knit-frame">
        %s
      </div>
      <div>
        <h2 class="mt-0">Максим и Коля</h2>
        <dl class="case-facts">
          <div class="case-fact"><dt>Возраст</dt><dd>16 и 14 лет</dd></div>
          <div class="case-fact"><dt>Проблема</dt><dd>Систематический отказ ходить в школу</dd></div>
          <div class="case-fact"><dt>Ситуация в семье</dt><dd>Мать — вдова; взрослые дети не имеют
          возможности помогать; контакт со школой нарушен</dd></div>
        </dl>
        <div class="swatch mt-2" style="padding:1.4rem">
          <h3 class="mt-0">Что можно сделать?</h3>
          <p class="mb-0">Обеспечить помощь психолога и репетиторов по русскому языку и математике.
          Тогда Максим сможет подготовиться к сдаче ОГЭ, набрать хотя бы минимум баллов для получения
          аттестата и выбрать интересующий его колледж, не повторяя сценарий со школой — и послужит
          примером для младшего брата Коли.</p>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="container container--narrow prose">
    <p>Максим (16 лет) и Коля (14 лет) — два брата, которые «учатся» дома на семейной форме обучения,
    но… учиться не любят и абсолютно не хотят.</p>
    <p>Мальчики воспитываются в многодетной семье. Всего у мамы шесть сыновей, папа умер 11 лет назад.
    Старшие четверо живут отдельно и в жизни младших братьев участия не принимают.</p>
    <p>Мама Мария включена в обучение и воспитание сыновей. Ребята ходили в семейные классы, обучались
    в онлайн-школе, но чуда не происходит. Мама до мая 2025 года не работала, занималась Колей
    и Максимом. До этого времени она получала пенсию по потере кормильца. Но в связи с тяжёлым
    материальным положением пришлось выйти на работу, и мальчишки остались дома без взрослого.</p>
    <p>Отношения между братьями дружеские, они занимаются самокатным спортом, пытаются заработать
    деньги доступным им способом — моют фары.</p>
    <p>Максиму нужно в 2026 году сдавать ОГЭ. Чтобы ребята вернулись к учёбе и нашли своё место
    в этом мире, нам нужны средства на тьютора, психолога и репетитора по русскому языку и математике.</p>
  </div>
</section>

<section class="section section--tight">
  <div class="container">
    <div class="gallery">
      %s
      %s
    </div>
  </div>
</section>

%s

<section class="section" id="donate">
  <div class="container container--narrow text-center">
    <h2>Помогите Максиму и Коле найти путь к учёбе и будущему</h2>
  </div>
  <div class="container container--narrow mt-2">
    %s
  </div>
</section>
""" % (
        img("brothers-main.jpg", "Максим и Коля", eager=True),
        img("brothers-1.jpg", "Максим и Коля"),
        img("brothers-2.jpg", "Максим и Коля"),
        case_expert(
            "<p>Иногда прогулы — это просто прогулы. Но за несколько лет ситуация может зайти так "
            "далеко, что у наших зарубежных коллег для этого даже есть специальный термин — "
            "<em>school refusal</em>, «отказ от школы».</p>"
            "<p>И речь не о том, что подростку лень вставать к первому уроку, и не о том, что родители "
            "сами планируют домашнее обучение. Речь об образе жизни, построенном на избегании учебных "
            "заведений.</p>"
            "<p>Конечно, «отказ от школы» — не болезнь. Но социальные последствия могут быть очень "
            "негативными: ребята пропускают не только алгебру и химию, но и опыт общения со сверстниками, "
            "и выбор профессии. В таких случаях надо работать с семьёй и школой вместе, но педагоги уже "
            "разочаровались в возможностях что-то изменить…</p>"
        ),
        donate_widget_block(form="brothers"),
    ),
    donation=True,
)

# ---------------------------------------------------------------- отчёты

page(
    "reports.html",
    "Отчёты",
    "Годовые отчёты АНО «Дирижабль» и документы о продлении деятельности.",
    """
<section class="section section--tight">
  <div class="container">
    <p class="eyebrow">Прозрачность</p>
    <h1>Отчёты</h1>
    <p class="lead" style="max-width:58ch">Публикуем годовые отчёты с первого года работы
    организации — 2023-го. Новые сверху.</p>
  </div>
</section>

<section class="section section--tight">
  <div class="container">
    <div class="grid grid--2">
      <div class="card">
        <h2 class="card__title mt-0">Годовые отчёты</h2>
        <div class="stack" style="gap:.75rem">
          %s
          %s
          %s
        </div>
      </div>
      <div class="card">
        <h2 class="card__title mt-0">Продление деятельности</h2>
        <div class="stack" style="gap:.75rem">
          %s
          %s
        </div>
      </div>
    </div>
  </div>
</section>

%s
""" % (
        # обратный хронологический порядок: свежий отчёт первым
        doc_link(PDF["report_2025"], "Отчёт 2025"),
        doc_link(PDF["report_2024"], "Отчёт 2024"),
        doc_link(REPORT_2023, "Отчёт 2023", "Облако Mail.ru"),
        doc_link(PDF["prolong_2024"], "Продление деятельности 2024"),
        doc_link(PDF["prolong_2023"], "Продление деятельности 2023"),
        donate_cta("Помогите нам продолжать",
                   "Отчёты показывают, что уже сделано. Ваша поддержка определяет, что будет дальше."),
    ),
)

# ------------------------------------------------------------- документы

page(
    "documents.html",
    "Документы и реквизиты",
    "Уставные документы, реквизиты и соглашения АНО Центр развития социальных практик «Дирижабль».",
    """
<section class="section section--tight">
  <div class="container">
    <p class="eyebrow">Официально</p>
    <h1>Документы и реквизиты</h1>
  </div>
</section>

<section class="section section--tight" id="requisites">
  <div class="container">
    <div class="grid grid--2">
      <div class="card">
        <h2 class="card__title mt-0">Реквизиты организации</h2>
        <dl class="requisites">
          <dt>Полное наименование</dt><dd>%s</dd>
          <dt>Сокращённое наименование</dt><dd>АНО «Дирижабль»</dd>
          <dt>ИНН</dt><dd>%s</dd>
          <dt>КПП</dt><dd>%s</dd>
          <dt>ОГРН</dt><dd>%s</dd>
          <dt>Юридический адрес</dt><dd>%s</dd>
          <dt>Директор</dt><dd>%s, <a href="tel:%s">%s</a></dd>
          <dt>E-mail</dt><dd><a href="mailto:%s">%s</a></dd>
        </dl>
      </div>
      <div class="card">
        <h2 class="card__title mt-0">Банковские реквизиты</h2>
        <dl class="requisites">
          <dt>Расчётный счёт</dt><dd>40703810120000000645</dd>
          <dt>Банк</dt><dd>ООО «Банк Точка»</dd>
          <dt>БИК</dt><dd>044525104</dd>
          <dt>Корр. счёт</dt><dd>30101810745374525104</dd>
          <dt>Получатель</dt><dd>АВТОНОМНАЯ НЕКОММЕРЧЕСКАЯ ОРГАНИЗАЦИЯ ЦЕНТР РАЗВИТИЯ СОЦИАЛЬНЫХ ПРАКТИК «ДИРИЖАБЛЬ»</dd>
          <dt>ИНН / КПП</dt><dd>%s / %s</dd>
        </dl>
      </div>
    </div>
  </div>
</section>

<section class="section section--purl" aria-labelledby="docs-title">
  <div class="container">
    <div class="section-head">
      <h2 id="docs-title">Документы</h2>
    </div>
    <div class="grid grid--2" style="align-items:start">
      <div class="stack" style="gap:.75rem">
        %s
        %s
        %s
        %s
      </div>
      <div class="gallery">
        <figure class="knit-frame knit-frame--flat" style="margin:0">
          %s
          <figcaption class="full-bleed-note mt-1">Свидетельство о государственной регистрации НКО</figcaption>
        </figure>
        <figure class="knit-frame knit-frame--flat" style="margin:0">
          %s
          <figcaption class="full-bleed-note mt-1">Свидетельство о постановке на учёт в налоговом органе</figcaption>
        </figure>
      </div>
    </div>
  </div>
</section>

%s
""" % (
        esc(ORG["full_name"]), ORG["inn"], ORG["kpp"], ORG["ogrn"], esc(ORG["address"]),
        esc(ORG["director"]), ORG["phone_href"], ORG["phone"], ORG["email"], ORG["email"],
        ORG["inn"], ORG["kpp"],
        doc_link(PDF["charter"], "Устав организации"),
        doc_link(PDF["privacy_policy"], "Положение об обработке и защите персональных данных"),
        doc_link(PDF["personal_data"], "Политика о персональных данных"),
        doc_link(PDF["offer"], "Договор присоединения (публичная оферта)"),
        img("doc-registration.jpg", "Скан свидетельства о государственной регистрации некоммерческой организации"),
        img("doc-tax.jpg", "Скан свидетельства о постановке на учёт в налоговом органе"),
        donate_cta(),
    ),
)

# ---------------------------------------------------------------- обучение

page(
    "education.html",
    "Образовательная деятельность",
    "Сведения об образовательной деятельности АНО «Дирижабль»: лицензия, структура Ресурсного "
    "центра профессионального мастерства, программы и документы.",
    """
<section class="section section--tight">
  <div class="container">
    <p class="eyebrow">Ресурсный центр профессионального мастерства</p>
    <h1>Основные сведения об образовательной деятельности</h1>
  </div>
</section>

<section class="section section--tight">
  <div class="container">
    <div class="grid grid--2">
      <div class="card">
        <h2 class="card__title mt-0">О подразделении</h2>
        <p class="card__text">Специализированное структурное образовательное подразделение
        «Ресурсный центр профессионального мастерства» было создано в 2026 г. для реализации
        образовательной деятельности в АНО Центр развития социальных практик «Дирижабль».</p>
        <p class="card__text">Деятельность подразделения регламентируется Положением и утверждена
        Директором. Директор — Арчакова Татьяна Олеговна.</p>
      </div>
      <div class="card">
        <h2 class="card__title mt-0">Лицензия</h2>
        <p class="card__text">Лицензия на осуществление образовательной деятельности
        № Л035-01298-77/05015296, выдана 08.05.2026 Комитетом по образованию Правительства Москвы.</p>
        %s
      </div>
      <div class="card">
        <h2 class="card__title mt-0">Режим работы и контакты</h2>
        <p class="card__text">С 10:00 до 18:00 в рабочие дни (кроме субботы и воскресенья).</p>
        <p class="card__text">Телефон/факс: <a href="tel:%s">%s</a><br>
        Электронная почта: <a href="mailto:%s">%s</a></p>
      </div>
      <div class="card">
        <h2 class="card__title mt-0">Структура и работники</h2>
        <p class="card__text">Структура Ресурсного центра утверждается Директором Организации.
        Руководитель Ресурсного центра подчиняется Директору. Обязанности распределяются
        руководителем и конкретизируются в должностных инструкциях.</p>
        <ul class="knit-list">
          <li>Руководитель Ресурсного центра — Арчакова Татьяна Олеговна</li>
          <li>Преподаватели — Арчакова Татьяна Олеговна</li>
          <li>Приглашённые специалисты с высокой квалификацией и релевантным практическим опытом</li>
          <li>Администратор — Абакарова Фатима Гаджиевна</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="section section--purl" aria-labelledby="edu-org-title">
  <div class="container">
    <div class="section-head">
      <h2 id="edu-org-title">Организация обучения</h2>
    </div>
    <div class="accordion">
      <details class="acc" open>
        <summary class="acc__summary">Уровень образования, формы и сроки</summary>
        <div class="acc__body prose">
          <p>Уровень образования — дополнительное профессиональное образование, дополнительные
          профессиональные программы повышения квалификации.</p>
          <p>Форма обучения — дистанционная.</p>
          <p>Нормативные сроки: программы повышения квалификации 16, 24 и 72 академических часа,
          а также краткосрочные тематические семинары, тренинги и супервизии.</p>
        </div>
      </details>
      <details class="acc">
        <summary class="acc__summary">График образовательного процесса</summary>
        <div class="acc__body">
          <p>Обучение предоставляется по мере формирования групп и индивидуальным запросам.</p>
        </div>
      </details>
      <details class="acc">
        <summary class="acc__summary">Численность обучающихся и язык</summary>
        <div class="acc__body">
          <p>Группы формируются в соответствии с запросом, от 2 до 30 человек. Обучение по всем
          образовательным программам осуществляется на русском языке.</p>
        </div>
      </details>
      <details class="acc">
        <summary class="acc__summary">Методические материалы</summary>
        <div class="acc__body">
          <p>Методические и справочные материалы, разработанные Организацией, размещены в онлайн-курсах
          в системе Zenclass.</p>
        </div>
      </details>
      <details class="acc">
        <summary class="acc__summary">Материально-техническое обеспечение</summary>
        <div class="acc__body prose">
          <p>Посредством сети Интернет и интерактивного оборудования обеспечена возможность
          подключения к информационным системам и электронным образовательным ресурсам и проведения
          занятий дистанционно. В учебном процессе используются электронные образовательные ресурсы
          и мультимедиа-материалы; ресурсная библиотека доступна для скачивания с сайта.</p>
          <p>Оборудованные учебные кабинеты: учебное помещение — компьютер с аудиосистемой
          и видеокамерой (1 шт.), стол письменный (1 шт.), кресло офисное (1 шт.), МФУ
          копир/принтер/сканер (1 шт.).</p>
        </div>
      </details>
    </div>
  </div>
</section>

<section class="section" aria-labelledby="edu-programs-title">
  <div class="container">
    <div class="section-head">
      <h2 id="edu-programs-title">Реализуемые образовательные программы</h2>
    </div>
    <div class="grid grid--2" style="align-items:start">
      <a class="card card--link card--patch reveal" href="program.html">
        <h3 class="card__title">Методы и инструменты исследования и активизации социального
        окружения детей и семей</h3>
        <p class="card__text">Программа повышения квалификации, 72 академических часа.
        Описание программы, инструменты и условия обучения.</p>
        <p class="mb-0"><span class="btn btn--ghost">Смотреть описание</span></p>
      </a>
      <div class="stack" style="gap:.75rem">
        %s
        %s
      </div>
    </div>

    <a class="card card--link card--patch reveal mt-3" href="effective.html" style="display:block">
      <h3 class="card__title">Инструменты повышения эффективности психотерапии</h3>
      <p class="card__text">Курс-тренинг для консультирующих психологов: шкалы ORS и SRS,
      преднамеренная практика, фасилитативные навыки. 32 ак. часа, онлайн.</p>
      <p class="mb-0"><span class="btn btn--ghost">Открыть страницу курса</span></p>
    </a>
  </div>
</section>

<section class="section section--purl" aria-labelledby="edu-docs-title">
  <div class="container">
    <div class="section-head">
      <h2 id="edu-docs-title">Локальные нормативные акты</h2>
    </div>
    <div class="grid grid--2" style="align-items:start">
      <div class="stack" style="gap:.75rem">
        %s
        %s
        %s
        %s
      </div>
      <div class="stack" style="gap:.75rem">
        %s
        %s
        %s
        %s
      </div>
    </div>
  </div>
</section>

<section class="section" aria-labelledby="edu-paid-title">
  <div class="container container--narrow">
    <h2 id="edu-paid-title">Платные образовательные услуги</h2>
    <p>Платные образовательные услуги предоставляются в соответствии с Положением о порядке
    предоставления платных образовательных услуг. Для получения услуг оформляются договор
    об образовании по дополнительным профессиональным программам и заявление о зачислении
    (включая согласие на обработку персональных данных).</p>
    <div class="stack mt-2" style="gap:.75rem">
      %s
      %s
    </div>
  </div>
</section>
""" % (
        doc_link(PDF["edu_license"], "Лицензия на осуществление образовательной деятельности"),
        ORG["phone_href"], ORG["phone"], ORG["email"], ORG["email"],
        doc_link(PDF["edu_program"], "Образовательная программа"),
        doc_link(PDF["edu_dpo"], "Положение по организации образовательной деятельности по ДПП"),
        doc_link(PDF["edu_unit"], "Положение о специализированном структурном образовательном подразделении"),
        doc_link(PDF["edu_admission"], "Правила приёма обучающихся"),
        doc_link(PDF["edu_transfer"], "Положение о переводе, отчислении и восстановлении обучающихся"),
        doc_link(PDF["edu_schedule"], "Положение о режиме занятий обучающихся"),
        doc_link(PDF["edu_control"], "Положение о формах, периодичности и порядке текущего контроля"),
        doc_link(PDF["edu_paid"], "Положение о порядке предоставления платных образовательных услуг"),
        doc_link(PDF["edu_distance"], "Положение об электронном обучении и ДОТ"),
        doc_link(PDF["edu_dpo"], "Положение по организации образовательной деятельности по ДПП"),
        doc_link(PDF["edu_paid"], "Положение о порядке предоставления платных образовательных услуг"),
        doc_link(GOV_RULES, "Постановление Правительства РФ от 15.08.2013 № 706", "Документ"),
    ),
)

# --------------------------------------------------------------- программа

page(
    "program.html",
    "Программа повышения квалификации, 72 ак. ч.",
    "«Методы и инструменты исследования и активизации социального окружения детей и семей, "
    "находящихся в трудной жизненной ситуации» — программа повышения квалификации на 72 ак. часа.",
    """
<section class="section section--tight">
  <div class="container">
    <p class="eyebrow"><a href="education.html">Образовательная деятельность</a></p>
    <h1>Методы и инструменты исследования и активизации социального окружения детей и семей</h1>
    <p class="lead" style="max-width:64ch">Программа повышения квалификации, 72 академических часа —
    для специалистов, работающих с семьями и детьми в трудной жизненной ситуации.</p>
  </div>
</section>

<section class="section section--tight">
  <div class="container container--narrow prose">
    <h2>Описание программы</h2>
    <p>Программа разработана АНО «Центр развития социальных практик „Дирижабль“» на основе
    социально-экологического подхода (по У. Бронфенбреннеру), технологии «Работа с сетью социальных
    контактов», элементов нарративной практики и ориентированного на решение подхода в психологическом
    консультировании и социальной работе, а также многолетней практики работы с семьями в трудной
    жизненной ситуации.</p>
    <p>Она фокусируется на выявлении ресурсов в социальном окружении ребёнка и семьи для профилактики
    социального сиротства, эксклюзии и дезадаптации, с освоением визуальных инструментов
    картирования связей.</p>
  </div>
</section>

<section class="section section--purl" aria-labelledby="tools-title">
  <div class="container">
    <div class="grid grid--2" style="align-items:start">
      <div>
        <h2 id="tools-title">Инструменты, осваиваемые в программе</h2>
        <ul class="knit-list mt-2">
          <li>Карта социальных контактов и её модификации: прошлого и будущего, гипотетическая,
          географическая</li>
          <li>Круги поддержки и безопасности «Кокон» — для обсуждения поддержки в ситуации
          травматического опыта</li>
          <li>Ресурсная генограмма и тематически сфокусированная генограмма</li>
          <li>«Книга жизни» и биографическая карта</li>
          <li>Схемы беседы «восстановления участия»</li>
          <li>«Супергеройская терапия»</li>
        </ul>
      </div>
      <div>
        <h2>Вопросы, на которые отвечает программа</h2>
        <ul class="knit-list mt-2">
          <li>Как применять социально-экологический подход для исследования сети социальных контактов
          семьи и ребёнка?</li>
          <li>Как выявлять ресурсы и риски в окружении для мотивации изменений и выхода из трудной
          жизненной ситуации?</li>
          <li>Как вовлекать кровных родственников, символические фигуры и даже питомцев в поддержку
          ребёнка?</li>
          <li>Как восстанавливать связи для детей в интернатах или переживающих амбивалентную потерю?</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="section" aria-labelledby="format-title">
  <div class="container">
    <div class="section-head">
      <h2 id="format-title">Формат и условия</h2>
    </div>
    <div class="grid grid--3">
      <article class="card card--patch">
        <h3 class="card__title">Для кого</h3>
        <p class="card__text">Специалисты по социальной работе с семьями и детьми (среднее или высшее
        образование), включая профстандарты «Специалист по работе с семьёй» и «Специалист по социальной
        работе»; психологи и педагоги в системах профилактики сиротства, ООиП, КДНиЗП.</p>
      </article>
      <article class="card card--patch">
        <h3 class="card__title">Форма обучения</h3>
        <p class="card__text">Заочная с дистанционными технологиями (Zenclass): лекции — 31 ак. ч.,
        самостоятельная работа — 41 ак. ч., промежуточная и итоговая аттестации — по 3 ак. ч.
        (индивидуальные задания с реальными случаями из практики обучающихся).</p>
      </article>
      <article class="card card--patch">
        <h3 class="card__title">Нагрузка и документ</h3>
        <p class="card__text">6,6 ак. ч. в неделю, 12 недель. Промежуточная аттестация после модуля 1,
        итоговая — кейс. Доступ через Zoom и аналоги, браузеры Chrome или Firefox. Выдаётся
        удостоверение о повышении квалификации.</p>
      </article>
    </div>

    <div class="swatch mt-3" style="padding:clamp(1.4rem,4vw,2.2rem)">
      <h3 class="mt-0">Стоимость за одного обучающегося</h3>
      <ul class="knit-list">
        <li>Для специалистов социальной сферы — <strong>бесплатно</strong></li>
        <li>Для остальных желающих — <strong>15 000 ₽</strong></li>
      </ul>
      <p class="cluster mt-2 mb-0">
        <a class="btn" href="mailto:%s?subject=%s">Записаться на программу</a>
        %s
      </p>
    </div>
  </div>
</section>
""" % (
        ORG["email"], "Программа%20повышения%20квалификации%2072%20ак.%20ч.",
        doc_link(PDF["edu_program"], "Образовательная программа"),
    ),
)

# --------------------------------------------------------------- опросники

FORMS = {
    "parents": "https://forms.yandex.ru/cloud/69d61ef249af4711247bd910",
    "teens": "https://forms.yandex.ru/cloud/69d55b6f505690c1134f7798",
    "specialists": "https://forms.yandex.ru/cloud/69d561496d2d7319894b5616",
}

page(
    "survey-clients.html",
    "Опросник для родителей, подростков или молодых взрослых",
    "Приглашаем переслать короткие опросники клиентам, у которых был опыт участия "
    "в процессах совместного принятия решений.",
    """
<article class="section section--tight">
  <div class="container container--narrow">
    <p class="eyebrow"><a href="research.html">Исследование</a> · 24 мая 2026</p>
    <h1>Опросник для родителей, подростков или молодых взрослых</h1>
  </div>
</article>

<section class="section section--tight">
  <div class="container">
    <div class="knit-frame knit-frame--flat">
      %s
    </div>
  </div>
</section>

<section class="section section--tight">
  <div class="container container--narrow prose">
    <p class="lead">Дорогие коллеги!</p>
    <p>Приглашаем вас сделать вклад в исследование — переслать короткие и простые опросники
    вашим клиентам с просьбой их заполнить.</p>

    <h2>Как понять, что ваши клиенты — целевая аудитория опросника?</h2>
    <ul class="knit-list">
      <li>Они участвовали во встрече, где вместе со специалистами, а также с близкими или друзьями
      принимали решения о том, что им делать дальше. Это могла быть сетевая встреча, семейная
      конференция, круг сообщества, семейная медиация, консилиум с участием клиентов, общее
      собрание родителей, проживающих в кризисном центре, или молодых взрослых — на базе
      сопровождаемого проживания, или что-то подобное. Для подробностей есть место в опроснике.</li>
      <li>Клиенты участвовали в таком формате работы не очень давно — до 3 месяцев назад.</li>
      <li>У клиентов нет выраженных интеллектуальных ограничений — мы ещё не адаптировали опросник
      под особые потребности.</li>
      <li>Подростки — с 10 лет, молодые взрослые — до 23 лет.</li>
      <li>Родители, взрослые родственники, опекуны — любые взрослые, которые несут правовую или
      неформальную «человеческую» ответственность за благополучие подростка или молодого взрослого.</li>
    </ul>
  </div>
</section>

<section class="section section--purl" aria-labelledby="forms-title">
  <div class="container container--narrow">
    <h2 id="forms-title">Ссылки на опросники</h2>
    <div class="stack mt-2" style="gap:.75rem">
      %s
      %s
    </div>
  </div>
</section>

<section class="section">
  <div class="container container--narrow">
    <h2>Примерный текст для рассылки</h2>
    <p class="muted">Изменения и уточнения — на ваше усмотрение.</p>

    <div class="accordion mt-2">
      <details class="acc" open>
        <summary class="acc__summary">Подросткам и молодым взрослым</summary>
        <div class="acc__body prose">
          <p>Коллеги из дружественной нам организации хотят лучше понять, как подростки и молодые
          взрослые относятся к поддержке от специалистов. Их волнует, какие способы принимать решения
          кажутся вам справедливыми. Твой опыт важен! Пожалуйста, удели 10 минут на опросник.
          Там нет философских вопросов и не надо писать много текста. Надо просто выбрать варианты
          ответа про то, что было в нашей с тобой работе. Опрос полностью анонимный — можешь отвечать
          так, как думаешь.</p>
          <p>Опросник: <a href="%s" target="_blank" rel="noopener noreferrer">%s</a></p>
        </div>
      </details>

      <details class="acc">
        <summary class="acc__summary">Родителям и другим взрослым</summary>
        <div class="acc__body prose">
          <p>Коллеги из дружественной нам организации хотят лучше понять, как родители, которые
          получают поддержку от специалистов, относятся к этой поддержке. Их волнует, какие способы
          принимать решения кажутся вам справедливыми. Ваш опыт важен, даже если вы раньше
          не задумывались об этом. Пожалуйста, уделите 10 минут на опросник. Там нет философских
          вопросов и не надо писать много текста. Надо просто выбрать варианты ответа про то,
          что было в нашей с вами работе. Опрос полностью анонимный — можете отвечать так,
          как думаете.</p>
          <p>Опросник: <a href="%s" target="_blank" rel="noopener noreferrer">%s</a></p>
        </div>
      </details>
    </div>

    <p class="cluster mt-3">
      <a class="btn btn--ghost" href="research.html">Вернуться к исследованию</a>
      <a class="btn" href="survey-specialists.html">Опросник для специалистов</a>
    </p>
  </div>
</section>
""" % (
        img("survey-clients.jpg",
            "Вязаная фигурка подростка заполняет анкету за столом рядом с вязаным ноутбуком и лампой",
            eager=True),
        doc_link(FORMS["parents"], "Вариант для родителей и взрослых родственников", "Яндекс.Формы"),
        doc_link(FORMS["teens"], "Вариант для подростков и молодых взрослых (до 23 лет)", "Яндекс.Формы"),
        FORMS["teens"], FORMS["teens"],
        FORMS["parents"], FORMS["parents"],
    ),
)

page(
    "survey-specialists.html",
    "Опросник для специалистов",
    "Опросник для специалистов о стиле работы, обеспечивающем справедливый процесс "
    "принятия решений. Занимает не более 20 минут.",
    """
<article class="section section--tight">
  <div class="container container--narrow">
    <p class="eyebrow"><a href="research.html">Исследование</a> · 24 мая 2026</p>
    <h1>Опросник для специалистов о стиле работы, обеспечивающем справедливый процесс принятия решений</h1>
  </div>
</article>

<section class="section section--tight">
  <div class="container">
    <div class="knit-frame knit-frame--flat">
      %s
    </div>
  </div>
</section>

<section class="section section--tight">
  <div class="container container--narrow prose">
    <p class="lead">Дорогие коллеги!</p>
    <p>Приглашаем вас сделать вклад в исследование — заполнить опросник о стиле работы,
    обеспечивающем справедливый процесс принятия решений. Занимает не более 20 минут.</p>

    <h2>Как понять, что вы — целевая аудитория опросника?</h2>
    <ul class="knit-list">
      <li>Вы хотя бы иногда проводите встречи с клиентами и их окружением, где вместе принимаете
      решения о том, что делать. Это могут быть сетевые встречи, семейные конференции, круги
      сообщества, семейная медиация, консилиумы с участием клиентов, общие собрания родителей,
      проживающих в кризисном центре, или молодых взрослых — на базе сопровождаемого проживания,
      или что-то подобное. Для подробностей есть место в опроснике.</li>
      <li>Вы практикуете такие форматы работы сейчас или активно делали это раньше и хорошо помните
      прошлый опыт.</li>
      <li>Базовое образование и должность в организации подходят любые. Если вам удаётся работать
      в таком формате в частной практике — это тоже подходит.</li>
    </ul>
  </div>
</section>

<section class="section section--purl" aria-labelledby="form-spec-title">
  <div class="container container--narrow">
    <h2 id="form-spec-title">Опросник</h2>
    <div class="stack mt-2" style="gap:.75rem">
      %s
    </div>
  </div>
</section>

<section class="section">
  <div class="container container--narrow">
    <h2>Что дальше?</h2>
    <p>Мы будем очень благодарны вам, если вы поделитесь этой страницей или просто ссылкой
    на опросник с вашими коллегами, которые подходят под целевую аудиторию опросника.</p>

    <div class="swatch mt-3" style="padding:clamp(1.4rem,4vw,2.2rem)">
      <h3 class="mt-0">Обратите внимание</h3>
      <ul class="knit-list">
        <li>Мы точно <strong>не будем</strong> делать выводы о том, насколько справедливо вы работаете,
        и «ставить оценки» за справедливость.</li>
        <li>Мы точно <strong>будем</strong> делиться результатами исследования и апробированными
        инструментами.</li>
      </ul>
    </div>

    <p class="cluster mt-3">
      <a class="btn btn--ghost" href="research.html">Вернуться к исследованию</a>
      <a class="btn" href="survey-clients.html">Опросник для клиентов</a>
    </p>
  </div>
</section>
""" % (
        img("survey-specialists.jpg",
            "Вязаная фигурка психолога с блокнотом, на котором отмечен ответ «Очень важна» "
            "на вопрос о справедливости в работе",
            eager=True),
        doc_link(FORMS["specialists"], "Опросник для специалистов", "Яндекс.Формы"),
    ),
)


# ------------------------------------------------------------------ курс


def video_embed(video_id: str, poster: str, alt: str, label: str) -> str:
    """Видео с постером и ленивой загрузкой плеера.

    Iframe подставляется только по клику (см. initVideo в app.js): до этого
    сторонний плеер и его куки не загружаются, а страница не тянет лишние
    сотни килобайт. Постер — обычная картинка, поэтому виден и без JS.
    """
    return """<div class="video knit-frame knit-frame--flat" data-video
     data-video-src="https://rutube.ru/play/embed/%s?autoplay=1">
      %s
      <button class="video__play" type="button" data-video-play aria-label="%s">
        <svg viewBox="0 0 24 24" width="34" height="34" fill="currentColor" aria-hidden="true">
          <path d="M8 5.2c0-.9 1-1.5 1.8-1l9.1 5.5c.7.5.7 1.5 0 2l-9.1 5.5c-.8.5-1.8-.1-1.8-1z"/>
        </svg>
      </button>
      <noscript><p class="full-bleed-note mt-1"><a href="https://rutube.ru/video/%s/"
      target="_blank" rel="noopener noreferrer">Смотреть видео на RuTube</a></p></noscript>
    </div>""" % (esc(video_id), poster, esc(label), esc(video_id))


def yookassa_form() -> str:
    """Форма оплаты курса (ЮKassa SimplePay).

    Самодостаточна: POST уходит прямо на yookassa.ru, свой бэкенд не нужен.
    Счётчик количества из оригинала убран — он работал их скриптом, которого
    в выгрузке нет, и неработающие кнопки «+/−» только путали бы.
    Без YOOKASSA_SHOP_ID форма не выводится, показывается запасной блок.
    """
    if not YOOKASSA_SHOP_ID:
        return """<div class="swatch" style="padding:clamp(1.4rem,4vw,2.2rem)">
      <p class="mb-0"><strong>Онлайн-оплата сейчас недоступна.</strong> Так бывает при офлайн-просмотре
      или локальной сборке без ключей. Напишите нам — пришлём ссылку на оплату:
      <a href="mailto:%s">%s</a>.</p>
    </div>""" % (ORG["email"], ORG["email"])

    return """<link rel="stylesheet" href="https://yookassa.ru/integration/simplepay/css/yookassa_construct_form.css?v=1.34.0">
    <form class="yoomoney-payment-form" action="https://yookassa.ru/integration/simplepay/payment" method="post" accept-charset="utf-8">
      <div class="ym-products">
        <div class="ym-block-title ym-products-title">Товары</div>
        <div class="ym-product">
          <div class="ym-product-line">
            <span class="ym-product-description">Курс ПК «Инструменты повышения эффективности психотерапии в действии»</span>
            <span class="ym-product-price" data-price="17500" data-id="771" data-count="1">17&nbsp;500,00&nbsp;₽</span>
          </div>
          <input type="hidden" name="text" value="Курс ПК Инструменты повышения эффективности психотерапии в действии">
          <input type="hidden" name="price" value="17500">
          <input type="hidden" name="quantity" value="1">
          <input type="hidden" name="paymentSubjectType" value="commodity">
          <input type="hidden" name="paymentMethodType" value="full_prepayment">
          <input type="hidden" name="tax" value="1">
        </div>
      </div>
      <input type="hidden" name="ym_merchant_receipt" value="">
      <div class="ym-customer-info">
        <div class="ym-block-title">О покупателе</div>
        <label class="visually-hidden" for="yoo-email">Email</label>
        <input id="yoo-email" name="cps_email" class="ym-input" placeholder="Email" type="email" required>
        <label class="visually-hidden" for="yoo-name">ФИО</label>
        <input id="yoo-name" name="custName" class="ym-input" placeholder="ФИО" type="text" required>
      </div>
      <div class="ym-payment-btn-block ym-before-line ym-align-space-between">
        <div class="ym-input-icon-rub ym-display-none">
          <input name="sum" class="ym-input ym-sum-input ym-required-input" type="number" step="any" value="17500">
        </div>
        <button type="submit" data-text="Заплатить" class="ym-btn-pay ym-result-price">
          <span class="ym-text-crop">Заплатить</span> <span class="ym-price-output">17&nbsp;500,00&nbsp;₽</span>
        </button>
        <img src="https://yookassa.ru/integration/simplepay/img/iokassa-gray.svg?v=1.34.0" class="ym-logo" width="114" height="27" alt="ЮKassa">
      </div>
      <input type="hidden" name="shopId" value="%s">
    </form>""" % esc(YOOKASSA_SHOP_ID)


page(
    "effective.html",
    "Инструменты повышения эффективности психотерапии",
    "Курс-тренинг для консультирующих психологов: технологии с доказанной эффективностью, "
    "шкалы ORS и SRS, преднамеренная практика. 32 ак. часа, онлайн, удостоверение о ПК.",
    """
<section class="section section--tight">
  <div class="container">
    <div class="grid grid--2" style="align-items:center">
      <div>
        <p class="eyebrow">Курс повышения квалификации</p>
        <h1>Инструменты повышения эффективности психотерапии</h1>
        <p class="lead">Что делает консультирующего психолога эффективным? Что вообще представляет
        собой «эффективность» в консультативной работе? Как достичь стабильности в организации
        практики, уменьшив количество преждевременных «выпадений» клиентов из терапии?</p>
      </div>
      <div class="knit-frame">
        %s
      </div>
    </div>

    <p class="prose mt-3" style="max-width:none">Наш курс-тренинг поможет вам найти свои ответы
    на эти вопросы. На нём мы дадим технологии с доказанной эффективностью, которые помогут
    укрепить ваши профессиональные навыки. Эти технологии используют универсальный «язык»,
    который будет понятен независимо от того, в каких подходах вы работаете.</p>

    <div class="grid grid--4 mt-3">
      <div class="card card--patch"><h2 class="card__title">17 500 ₽</h2><p class="card__text mb-0">Стоимость обучения</p></div>
      <div class="card card--patch"><h2 class="card__title">2 дня</h2><p class="card__text mb-0">Продолжительность</p></div>
      <div class="card card--patch"><h2 class="card__title">Онлайн</h2><p class="card__text mb-0">Формат обучения</p></div>
      <div class="card card--patch"><h2 class="card__title">Удостоверение</h2><p class="card__text mb-0">О повышении квалификации установленного образца</p></div>
    </div>
  </div>
</section>

<section class="section section--purl" aria-labelledby="course-what-title">
  <div class="container">
    <div class="section-head">
      <h2 id="course-what-title">На курсе вы</h2>
    </div>
    <div class="grid grid--3">
      <article class="card card--patch reveal">
        <span class="card__num">1</span>
        <p class="card__text mb-0">Сразу тренируете навыки и пробуете использовать инструменты
        в работе в парах с обратной связью тренера.</p>
      </article>
      <article class="card card--patch reveal">
        <span class="card__num">2</span>
        <p class="card__text mb-0">Получаете теоретическую базу, записи лекционных частей
        и дополнительные материалы для чтения.</p>
      </article>
      <article class="card card--patch reveal">
        <span class="card__num">3</span>
        <p class="card__text mb-0">После двух дней интенсивной работы получаете месяц сопровождения
        в чате, два созвона и ответы на вопросы.</p>
      </article>
    </div>

    <div class="swatch mt-3" style="padding:clamp(1.4rem,4vw,2.2rem)">
      <h3 class="mt-0">Организационные вопросы</h3>
      <ul class="knit-list">
        <li>Онлайн-интенсив — 4 и 5 июля (суббота и воскресенье) с 11:00 до 19:00 по Москве, в Zoom.</li>
        <li>Сопровождение и задания для самостоятельной работы после тренинга — весь июль.</li>
        <li>Доступ к материалам — навсегда.</li>
        <li>Общая продолжительность — 32 академических часа.</li>
      </ul>
    </div>
  </div>
</section>

<section class="section" aria-labelledby="course-result-title">
  <div class="container">
    <div class="section-head">
      <h2 id="course-result-title">После курса вы сможете</h2>
    </div>
    <div class="grid grid--2">
      <article class="card card--patch reveal">
        <span class="card__num">1</span>
        <p class="card__text mb-0">В партнёрстве с клиентом анализировать и оценивать качество
        терапевтического альянса и результатов психотерапии.</p>
      </article>
      <article class="card card--patch reveal">
        <span class="card__num">2</span>
        <p class="card__text mb-0">Определять «проблемные» зоны в работе с клиентами уже на ранних
        стадиях и предпринимать действия по исправлению ситуации.</p>
      </article>
      <article class="card card--patch reveal">
        <span class="card__num">3</span>
        <p class="card__text mb-0">Создавать предпосылки для более эффективной терапии и большей
        приверженности ей уже на первой сессии.</p>
      </article>
      <article class="card card--patch reveal">
        <span class="card__num">4</span>
        <p class="card__text mb-0">Самостоятельно выявлять и совершенствовать профессиональные
        «зоны развития».</p>
      </article>
    </div>
  </div>
</section>

<section class="section section--purl" aria-labelledby="course-program-title">
  <div class="container container--narrow">
    <h2 id="course-program-title">Программа обучения</h2>
    <div class="accordion mt-2">
      <details class="acc" open>
        <summary class="acc__summary">Исследования факторов и эффективности психотерапии</summary>
        <div class="acc__body">
          <p>Факторы и предикторы эффективности психотерапии, концепция общих факторов, модели
          и траектории изменений в психотерапии, исследования дропаутов.</p>
        </div>
      </details>
      <details class="acc">
        <summary class="acc__summary">Преднамеренная практика как методология совершенствования</summary>
        <div class="acc__body">
          <p>Преднамеренная практика как ключевой фактор более высокой эффективности одних
          психотерапевтов относительно других; цикл и таксономия ПП; терапевтические навыки
          как ключевой фокус ПП.</p>
        </div>
      </details>
      <details class="acc">
        <summary class="acc__summary">Фасилитативные межличностные навыки</summary>
        <div class="acc__body">
          <p>Ключевые исследования и практическая отработка навыков как фактора эффективности
          психотерапии.</p>
        </div>
      </details>
      <details class="acc">
        <summary class="acc__summary">Предикторы эффективности и инструменты их оценки</summary>
        <div class="acc__body">
          <p>Основные характеристики, функции, области применения и ограничения шкал SRS и ORS;
          показатели, указывающие на проблемы в терапевтическом альянсе и результатах терапии;
          действия психотерапевта в ответ на выявленные затруднения.</p>
        </div>
      </details>
    </div>
  </div>
</section>

<section class="section" aria-labelledby="course-teacher-title">
  <div class="container container--narrow">
    <h2 id="course-teacher-title" class="text-center">Преподаватель</h2>
    <div class="quote mt-2">
      <div class="quote__head">
        %s
        <div class="quote__who">
          <span class="quote__name">Михаил Пономарёв</span>
          <span class="quote__role">Клинический психолог, ориентированный на решение практик,
          кандидат психологических наук</span>
        </div>
      </div>
      <div class="prose">
        <p>Доцент кафедры нейро- и патопсихологии, руководитель магистерской программы
        «Психологическое консультирование» Института психологии им. Л. С. Выготского
        ФГАОУ ВО «Российский государственный гуманитарный университет».</p>
        <p>Уже апробировал свой курс «Инструменты повышения эффективности психотерапии» очно
        в НИУ ВШЭ — повторы пока в листе ожидания.</p>
      </div>
    </div>
  </div>
</section>

<section class="section section--tight" aria-labelledby="course-video-title">
  <div class="container">
    <h2 id="course-video-title" class="visually-hidden">Видео о курсе</h2>
    %s
  </div>
</section>

<section class="section" id="signup" aria-labelledby="course-signup-title">
  <div class="container container--narrow">
    <h2 id="course-signup-title">Записаться на курс</h2>
    <p class="lead">«Инструменты повышения эффективности психотерапии», 4–5 июля 2026 года.</p>
    <div class="swatch mt-2" style="padding:clamp(1.4rem,4vw,2.2rem)">
      <p>Напишите нам — администратор свяжется с вами и уточнит детали.</p>
      <p class="cluster mb-0">
        <a class="btn" href="https://t.me/archakova84" target="_blank" rel="noopener noreferrer">Написать в Telegram</a>
        <a class="btn btn--ghost" href="mailto:%s?subject=%s">Написать на почту</a>
      </p>
    </div>
    <p class="full-bleed-note mt-2">Отправляя заявку, вы соглашаетесь на
    <a href="%s" target="_blank" rel="noopener noreferrer">обработку персональных данных</a>.</p>
  </div>
</section>

<section class="section section--purl" id="pay" aria-labelledby="course-pay-title">
  <div class="container container--narrow">
    <h2 id="course-pay-title">Оплатить курс</h2>
    <div class="donate-widget mt-2">
      %s
    </div>
    <p class="cluster mt-2">
      <a class="btn btn--ghost" href="https://t.me/archakova84" target="_blank" rel="noopener noreferrer">Договориться о рассрочке</a>
    </p>
  </div>
</section>

<section class="section" aria-labelledby="course-article-title">
  <div class="container container--narrow">
    <div class="swatch" style="padding:clamp(1.4rem,4vw,2.2rem)">
      <h2 id="course-article-title" class="mt-0">Использование шкал обратной связи в индивидуальной психотерапии</h2>
      <p>Подробная статья на основе мастер-класса Михаила Пономарёва для Нарративной мастерской.</p>
      <p class="mb-0"><a class="btn" href="https://narrative.team/scala_oaf_fedback" target="_blank" rel="noopener noreferrer">Читать статью</a></p>
    </div>
  </div>
</section>

<section class="section section--purl" aria-labelledby="course-review-title">
  <div class="container container--narrow">
    <h2 id="course-review-title" class="text-center">Отзыв участницы</h2>
    <div class="quote mt-2">
      <div class="quote__head">
        %s
        <div class="quote__who">
          <span class="quote__name">Наталья Литвинова</span>
          <span class="quote__role">Участница курса «Инструменты повышения эффективности
          психотерапии», который Михаил проводил на базе НИУ ВШЭ</span>
        </div>
      </div>
      <div class="prose">
        <p>Я под большим впечатлением от двухдневного тренинга «Инструменты повышения эффективности
        психотерапии». По соотношению затраченных усилий, ресурсов, полученной информации,
        отработанных навыков и инсайтов — 10 из 10!</p>
        <p>Было много науки и много практики. Вся информация научно обоснована и статистически
        проверена, но при этом супер полезна, нужна и применима в работе. В общем, всё как я люблю —
        бери и делай.</p>
      </div>
    </div>
  </div>
</section>
""" % (
        img("course-cover.jpg",
            "Михаил Пономарёв выступает с микрофоном перед аудиторией, чёрно-белое фото",
            eager=True),
        img("course-ponomarev.jpg", "Портрет: Михаил Пономарёв", "quote__avatar"),
        video_embed(
            RUTUBE_COURSE_VIDEO,
            img("course-banner.jpg",
                "Кадр из видео о курсе: шкала оценки результата и Михаил Пономарёв",
                "video__poster"),
            "", "Смотреть видео о курсе"),
        ORG["email"], "Запись%20на%20курс%20«Инструменты%20повышения%20эффективности%20психотерапии»",
        PDF["privacy_policy"],
        yookassa_form(),
        img("course-review.png", "Фотография участницы курса Натальи Литвиновой", "quote__avatar"),
    ),
)


# ----------------------------------------------------------------- 404

page(
    "404.html",
    "Страница не найдена",
    "Такой страницы на сайте нет. Возможно, она переехала — вернитесь на главную "
    "или выберите раздел.",
    """
<section class="section">
  <div class="container container--narrow text-center">
    <p class="eyebrow">Ошибка 404</p>
    <h1>Похоже, здесь спустилась петля</h1>
    <p class="lead center-x" style="max-width:52ch">Такой страницы на сайте нет. Возможно,
    она переехала или адрес набран с опечаткой.</p>
    <p class="cluster cluster--center mt-2">
      <a class="btn btn--lg" href="index.html">На главную</a>
      <a class="btn btn--ghost btn--lg" href="donate.html">Помочь</a>
    </p>

    <div class="cable-divider mt-3" role="presentation"></div>

    <h2>Куда можно перейти</h2>
    <ul class="knit-list mt-2" style="text-align:left;max-width:40ch;margin-inline:auto">
      <li><a href="about.html">О нас</a> — миссия, история и команда</li>
      <li><a href="news.html">Новости</a> — проекты и «не-истории»</li>
      <li><a href="research.html">Исследование</a> — процедурная справедливость и опросники</li>
      <li><a href="education.html">Обучение</a> — программы и лицензия</li>
      <li><a href="documents.html">Документы</a> — реквизиты и уставные документы</li>
    </ul>
  </div>
</section>
""",
    noindex=True,
)


# ------------------------------------------------- демо мотива «амигуруми»

_AMI_YARNS = [
    ("cobalt", "Кобальт", "wool--cobalt"),
    ("azure", "Лазурь", "wool--azure"),
    ("orange", "Мандарин", "wool--orange"),
    ("cream", "Сливки", "wool--cream"),
    ("sand", "Песок", "wool--sand"),
    ("wine", "Вишня", "wool--wine"),
    ("moss", "Мох", "wool--moss"),
]


def _skeins() -> str:
    out = []
    for _, title, cls in _AMI_YARNS:
        out.append(
            '      <figure style="margin:0;text-align:center">\n'
            '        <div class="skein %s" role="img" aria-label="Моток пряжи «%s»"></div>\n'
            '        <figcaption class="swatch-label">%s</figcaption>\n'
            "      </figure>" % (cls, esc(title), esc(title))
        )
    return "\n".join(out)


page(
    "knit-demo.html",
    "Мотив «Амигуруми» — демонстрация стиля",
    "Демонстрация более объёмного вязаного мотива: толстая пряжа, обвязка крючком, "
    "пуговицы и вышитые галочки. Экспериментальная страница поверх основной дизайн-системы.",
    """
<div class="ami">

<section class="section">
  <div class="container">
    <div class="ami-hero">
      <div class="wool wool--cobalt ami-panel crochet-edge" style="--edge:var(--yarn-tangerine)">
        <p class="patch">Демонстрация стиля</p>
        <div class="ink-plate" style="margin-top:.9rem">
          <h1 style="margin-top:0">Мотив «Амигуруми»</h1>
          <p class="lead mb-0">Здесь вязка — не фоновая текстура, а материал самих элементов:
          блоки связаны из толстой пряжи, края обвязаны крючком, кнопки застёгиваются
          на пуговицу, а галочки вышиты.</p>
        </div>
        <p class="cluster" style="margin-top:1.5rem">
          <a class="btn-button" href="#components"><span class="button-dot button-dot--four"></span>Смотреть компоненты</a>
          <a class="btn-button btn-button--cream" href="index.html"><span class="button-dot button-dot--wood"></span>Вернуться на сайт</a>
        </p>
      </div>

      <div class="wool-frame">
        %s
      </div>
    </div>
  </div>
</section>

<section class="section section--tight">
  <div class="container">
    <div class="cord" style="--cord-color:var(--yarn-tangerine)" role="presentation"></div>
  </div>
</section>

<section class="section section--tight" aria-labelledby="ami-yarn-title">
  <div class="container">
    <h2 id="ami-yarn-title">Пряжа</h2>
    <p class="muted" style="max-width:60ch">Палитра наследует фирменные синий и оранжевый
    из логотипа-дирижабля. Каждый моток — та же петельная фактура, что и у блоков.</p>
    <div class="ami-grid ami-grid--4" style="margin-top:1.5rem">
%s
    </div>
  </div>
</section>

<section class="section section--tight" aria-labelledby="ami-tex-title">
  <div class="container">
    <h2 id="ami-tex-title">Фактуры</h2>
    <div class="ami-grid ami-grid--3" style="margin-top:1.5rem">
      <figure style="margin:0">
        <div class="wool wool--cobalt wool--fine swatch-tile"></div>
        <figcaption class="swatch-label">Гладь, тонкая пряжа</figcaption>
      </figure>
      <figure style="margin:0">
        <div class="wool wool--cobalt swatch-tile"></div>
        <figcaption class="swatch-label">Гладь, обычная</figcaption>
      </figure>
      <figure style="margin:0">
        <div class="wool wool--cobalt wool--chunky swatch-tile"></div>
        <figcaption class="swatch-label">Гладь, толстая</figcaption>
      </figure>
      <figure style="margin:0">
        <div class="tex-rib swatch-tile" style="--tex:#1B6FC9"></div>
        <figcaption class="swatch-label">Резинка 2×2</figcaption>
      </figure>
      <figure style="margin:0">
        <div class="tex-seed swatch-tile" style="--tex:#DCC7A6"></div>
        <figcaption class="swatch-label">Жемчужная вязка</figcaption>
      </figure>
      <figure style="margin:0">
        <div class="tex-waffle swatch-tile" style="--tex:#E8761E"></div>
        <figcaption class="swatch-label">Плетёнка</figcaption>
      </figure>
    </div>
  </div>
</section>

<section class="section" id="components" aria-labelledby="ami-comp-title">
  <div class="container">
    <h2 id="ami-comp-title">Компоненты</h2>

    <div class="ami-grid" style="grid-template-columns:1fr;margin-top:1.5rem">
      <div class="ami-grid ami-grid--3" style="align-items:start">

        <div class="wool wool--cream ami-panel">
          <div class="ink-plate ink-plate--light">
            <h3 style="margin-top:0">Кнопки</h3>
            <p class="mb-0">Застёгиваются на пуговицу, вдавливаются при нажатии.</p>
          </div>
          <p class="cluster" style="margin-top:1rem">
            <a class="btn-button" href="#buttons"><span class="button-dot button-dot--pearl"></span>Оранжевая</a>
            <a class="btn-button btn-button--blue" href="#buttons"><span class="button-dot button-dot--wood"></span>Синяя</a>
          </p>
        </div>

        <div class="wool wool--moss ami-panel crochet-edge" style="--edge:var(--yarn-cream)">
          <div class="ink-plate">
            <h3 style="margin-top:0">Панель с обвязкой</h3>
            <p class="mb-0">Нижний край обвязан крючком — полукруглые «рачьи шаги».
            Цвет обвязки задаётся переменной.</p>
          </div>
        </div>

        <div class="wool wool--sand ami-panel">
          <div class="ink-plate ink-plate--light">
            <h3 style="margin-top:0">Нашивки</h3>
            <p class="mb-0">Ярлычки с прошитым краем.</p>
          </div>
          <p class="cluster" style="margin-top:1rem">
            <span class="patch">Сетевая встреча</span>
            <span class="patch">Супервизия</span>
            <span class="patch">Обучение</span>
          </p>
        </div>

      </div>
    </div>

    <div class="wool wool--cream ami-panel" id="buttons" style="margin-top:2rem">
      <div class="ink-plate ink-plate--light">
        <h3 style="margin-top:0">Пуговицы</h3>
        <p class="mb-0">Разные виды застёжки: две и четыре дырочки, кольцо, фигурная с насечками,
        деревянная и перламутровая. Дырочки рисуются градиентами, поэтому вариантов может быть
        сколько угодно.</p>
      </div>
      <div class="button-row" style="margin-top:1.4rem">
        <span class="button-sample"><span class="button-dot"></span><span>2 дырочки</span></span>
        <span class="button-sample"><span class="button-dot button-dot--four"></span><span>4 дырочки</span></span>
        <span class="button-sample"><span class="button-dot button-dot--ring"></span><span>Кольцо</span></span>
        <span class="button-sample"><span class="button-dot button-dot--flower"></span><span>Фигурная</span></span>
        <span class="button-sample"><span class="button-dot button-dot--wood"></span><span>Дерево</span></span>
        <span class="button-sample"><span class="button-dot button-dot--pearl"></span><span>Перламутр</span></span>
        <span class="button-sample"><span class="button-dot button-dot--cobalt"></span><span>Кобальт</span></span>
        <span class="button-sample"><span class="button-dot button-dot--orange"></span><span>Мандарин</span></span>
      </div>
    </div>

    <div class="ami-grid" style="grid-template-columns:1fr;margin-top:2.5rem">
      <div class="wool wool--azure knit-form">
        <p class="knit-form__title ink-plate" style="padding:.7rem 1rem">Насколько для вас важна справедливость в работе?</p>
        <label class="knit-option">
          <input type="radio" name="ami-fairness">
          <span class="knit-check"></span>
          <span>Очень важна</span>
        </label>
        <label class="knit-option">
          <input type="radio" name="ami-fairness">
          <span class="knit-check"></span>
          <span>Важна</span>
        </label>
        <label class="knit-option">
          <input type="radio" name="ami-fairness">
          <span class="knit-check"></span>
          <span>Скорее важна</span>
        </label>
        <label class="knit-option">
          <input type="radio" name="ami-fairness">
          <span class="knit-check"></span>
          <span>Не очень важна</span>
        </label>
        <p class="ink-plate" style="font-size:.9rem;margin-top:.6rem;padding:.7rem 1rem">Галочка
        вышивается при выборе. Это демонстрация оформления — ответы никуда не отправляются.</p>
      </div>
    </div>
  </div>
</section>

<section class="section section--tight">
  <div class="container">
    <div class="wool wool--cream ami-panel">
      <div class="ink-plate ink-plate--light">
        <h2 style="margin-top:0">Чем это отличается от основного сайта</h2>
        <p class="mb-0" style="max-width:66ch">На боевых страницах вязка работает фоном: тонкая
        фактура, спокойный контраст, текст читается легко на длинных материалах. Здесь тот же мотив
        доведён до предметного уровня — так оформляют обложки, промо-блоки и отдельные акции,
        где важнее характер, чем плотность текста.</p>
      </div>
      <p class="cluster" style="margin-top:1.25rem">
        <a class="btn-button btn-button--blue" href="index.html"><span class="button-dot button-dot--ring"></span>Открыть основной сайт</a>
      </p>
    </div>
  </div>
</section>

</div>
""" % (
        img("research-cover.jpg",
            "Вязаная иллюстрация: дерево «Справедливый процесс», люди собирают плоды, "
            "в кроне сердце с надписью «Качество решения»"),
        _skeins(),
    ),
    head_extra='<link rel="stylesheet" href="%s">\n' % asset("assets/css/amigurumi.css"),
)


# --------------------------------------------------------------------------
# редиректы со старых адресов Craftum
# --------------------------------------------------------------------------

REDIRECTS = {
    "page2.html": "help-brothers.html",
    "page3.html": "about.html",
    "page4.html": "news.html",
    "page6.html": "help-vanya.html",
    "page7.html": "documents.html",
    "page9.html": "donate.html",
    "page10.html": "reports.html",
    "page11.html": "education.html",
    "page12.html": "program.html",
    "justice_research.html": "research.html",
}

REDIRECT_TMPL = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Страница переехала — %s</title>
<link rel="canonical" href="%s/%s">
<meta http-equiv="refresh" content="0; url=%s">
<meta name="robots" content="noindex, follow">
<link rel="icon" href="assets/img/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="%s">
</head>
<body>
<main id="main" class="section">
  <div class="container container--narrow text-center">
    <h1>Страница переехала</h1>
    <p class="lead">Этот адрес остался от старой версии сайта. Сейчас перенаправим на новую страницу.</p>
    <p class="cluster cluster--center mt-2"><a class="btn btn--lg" href="%s">Перейти сейчас</a></p>
  </div>
</main>
<script>location.replace(%s);</script>
</body>
</html>
"""


# --------------------------------------------------------------------------
# запись
# --------------------------------------------------------------------------


def main() -> int:
    written = []

    pages = [p for p in PAGES if SHOW_CASE_PAGES or p["slug"] not in CASE_SLUGS]
    removed = [p["slug"] for p in PAGES if p["slug"] not in [q["slug"] for q in pages]]

    # Старые адреса Craftum не должны вести на несуществующие страницы
    redirects = dict(REDIRECTS)
    if not SHOW_CASE_PAGES:
        for old, new in list(redirects.items()):
            if new in CASE_SLUGS:
                redirects[old] = "donate.html"

    for p in pages:
        out = render_page(p)
        path = os.path.join(ROOT, p["slug"])
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(out)
        written.append((p["slug"], len(out)))

    # убираем файлы отключённых страниц, чтобы в сборке не осталось старых копий
    for slug in removed:
        stale = os.path.join(ROOT, slug)
        if os.path.exists(stale):
            os.remove(stale)

    for old, new in redirects.items():
        body = REDIRECT_TMPL % (ORG["name"], SITE_URL, new, new,
                                asset("assets/css/knit.css"), new,
                                '"' + new + '"')
        with open(os.path.join(ROOT, old), "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
        written.append((old, len(body)))

    # sitemap + robots
    # В карту сайта не попадают служебные страницы (404, демо мотива).
    # lastmod берём из даты сборки — для статики это честнее, чем выдумывать
    # даты правок отдельных страниц.
    today = datetime.date.today().isoformat()
    indexable = [p for p in pages
                 if not p.get("noindex") and p["slug"] not in NOINDEX_SLUGS]

    def priority(slug):
        if slug == "index.html":
            return "1.0"
        if slug in ("donate.html", "about.html", "effective.html"):
            return "0.9"
        if slug in ("news.html", "research.html", "education.html"):
            return "0.8"
        return "0.6"

    urls = "\n".join(
        '  <url><loc>%s/%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>'
        % (SITE_URL, canonical_path(p["slug"]), today, priority(p["slug"]))
        for p in indexable
    )
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               + urls + "\n</urlset>\n")
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(sitemap)

    robots = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /knit-demo.html\n"
        "Disallow: /404.html\n"
        "\n"
        "Sitemap: %s/sitemap.xml\n" % SITE_URL
    )
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(robots)

    # CNAME нужен GitHub Pages, чтобы отдавать сайт на своём домене.
    # На github.io-адресе файл только мешает, поэтому пишем его лишь
    # когда SITE_URL указывает на собственный домен.
    host = SITE_URL.split("//", 1)[-1].split("/", 1)[0]
    cname_path = os.path.join(ROOT, "CNAME")
    if host and not host.endswith("github.io"):
        with open(cname_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(host + "\n")
    elif os.path.exists(cname_path):
        os.remove(cname_path)

    # GitHub Pages иначе прогоняет вывод через Jekyll
    with open(os.path.join(ROOT, ".nojekyll"), "w", encoding="utf-8") as f:
        f.write("")

    print("Собрано страниц: %d, редиректов: %d" % (len(pages), len(redirects)))
    if removed:
        print("Отключены (SHOW_CASE_PAGES=1 вернёт): %s" % ", ".join(removed))
    print("Адрес сайта: %s" % SITE_URL)
    print("Счётчики: Яндекс.Метрика — %s, Top.Mail.Ru — %s" % (
        "задан" if ANALYTICS["yandex_metrika_id"] else "нет (заглушка)",
        "задан" if ANALYTICS["top_mail_ru_id"] else "нет (заглушка)"))
    print("Платёжная форма: %s" % (
        "подключена" if DONATION["widget_id"] and DONATION["form_id"]
        else "нет ID — показывается запасной блок"))
    for name, size in written:
        print("  %-24s %6.1f КБ" % (name, size / 1024))
    print("  sitemap.xml, robots.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
