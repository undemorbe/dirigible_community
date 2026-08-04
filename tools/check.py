#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка собранного сайта: битые ссылки, отсутствующие файлы, дубли id,
структура заголовков, пустые alt, безопасность внешних ссылок.

Запуск:  python3 tools/check.py
Возвращает код 1, если есть ошибки (ERROR). Предупреждения (WARN) код не меняют.
"""

from __future__ import annotations

import glob
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VOID = {"img", "br", "hr", "input", "meta", "link", "source", "area",
        "col", "embed", "param", "track", "wbr", "path", "circle", "rect", "use"}

errors: list = []
warnings: list = []


def err(page: str, message: str) -> None:
    errors.append("%s: %s" % (page, message))


def warn(page: str, message: str) -> None:
    warnings.append("%s: %s" % (page, message))


class PageScan(HTMLParser):
    def __init__(self, page: str):
        super().__init__(convert_charrefs=True)
        self.page = page
        self.ids: dict = {}
        self.links: list = []
        self.imgs: list = []
        self.headings: list = []
        self.stack: list = []
        self.unbalanced: list = []
        self.in_heading = None
        self.heading_text = ""
        self.lang = None
        self.title = ""
        self.in_title = False
        self.labelled: list = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)

        if tag == "html":
            self.lang = a.get("lang")
        if tag == "title":
            self.in_title = True

        node_id = a.get("id")
        if node_id:
            if node_id in self.ids:
                err(self.page, "дубль id=%s" % node_id)
            self.ids[node_id] = True

        if tag == "a":
            href = a.get("href")
            if href is None:
                warn(self.page, "<a> без href")
            else:
                self.links.append((href, a))
            if not a.get("href") and not a.get("role"):
                pass

        if tag == "img":
            self.imgs.append(a)

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.in_heading = tag
            self.heading_text = ""

        if a.get("aria-labelledby"):
            self.labelled.append(a["aria-labelledby"])

        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, [a for a in attrs])
        if tag not in VOID and self.stack and self.stack[-1] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag in VOID:
            return
        if self.in_heading == tag:
            self.headings.append((tag, self.heading_text.strip()))
            self.in_heading = None
        if tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass
        else:
            self.unbalanced.append(tag)

    def handle_data(self, data):
        if self.in_heading:
            self.heading_text += data
        if self.in_title:
            self.title += data


def check_page(path: str) -> PageScan:
    page = os.path.basename(path)
    with open(path, encoding="utf-8") as f:
        html_text = f.read()

    scan = PageScan(page)
    scan.feed(html_text)

    if scan.unbalanced:
        err(page, "непарные закрывающие теги: %s" % ", ".join(sorted(set(scan.unbalanced))))
    if scan.stack:
        err(page, "незакрытые теги: %s" % ", ".join(scan.stack))

    if scan.lang != "ru":
        err(page, 'ожидался <html lang="ru">, получено %r' % scan.lang)
    if not scan.title.strip():
        err(page, "пустой <title>")

    # заголовки
    h1s = [t for t, _ in scan.headings if t == "h1"]
    is_redirect = "Страница переехала" in scan.title
    if len(h1s) != 1:
        (warn if is_redirect else err)(page, "h1 должен быть ровно один, найдено %d" % len(h1s))

    level = 0
    for tag, text in scan.headings:
        n = int(tag[1])
        if level and n > level + 1:
            warn(page, "перескок уровня заголовков %s → %s (%s)" % ("h%d" % level, tag, text[:40]))
        level = n

    # ссылки
    for href, attrs in scan.links:
        if not href or href.startswith(("mailto:", "tel:", "javascript:")):
            if href.startswith("javascript:"):
                err(page, "javascript:-ссылка %s" % href)
            continue
        parts = urlsplit(href)
        if parts.scheme in ("http", "https"):
            if attrs.get("target") == "_blank":
                rel = (attrs.get("rel") or "").split()
                if "noopener" not in rel:
                    err(page, "внешняя ссылка target=_blank без rel=noopener: %s" % href)
            continue
        if parts.scheme:
            continue
        if not parts.path:  # чистый якорь
            frag = unquote(parts.fragment)
            if frag and frag not in scan.ids:
                err(page, "якорь #%s не найден на странице" % frag)
            continue
        target = os.path.join(ROOT, unquote(parts.path))
        if not os.path.exists(target):
            err(page, "битая ссылка на файл: %s" % parts.path)
        elif parts.fragment:
            with open(target, encoding="utf-8") as f:
                if ('id="%s"' % unquote(parts.fragment)) not in f.read():
                    err(page, "якорь %s не найден в %s" % (parts.fragment, parts.path))

    # изображения
    for a in scan.imgs:
        src = a.get("src", "")
        if "alt" not in a:
            err(page, "img без alt: %s" % src)
        elif a["alt"].strip().lower() in ("image alt", "img", "картинка", "фото"):
            err(page, "мусорный alt %r у %s" % (a["alt"], src))
        if src and not src.startswith(("http", "data:")):
            target = os.path.join(ROOT, unquote(urlsplit(src).path))
            if not os.path.exists(target):
                err(page, "нет файла изображения: %s" % src)
        if not a.get("width") or not a.get("height"):
            warn(page, "img без width/height (риск скачков вёрстки): %s" % src)

    # aria-labelledby указывает на существующий id
    for ref in scan.labelled:
        for token in ref.split():
            if token not in scan.ids:
                err(page, "aria-labelledby указывает на несуществующий id=%s" % token)

    return scan


def check_assets() -> None:
    """Ссылки внутри CSS должны разрешаться."""
    css_path = os.path.join(ROOT, "assets", "css", "knit.css")
    with open(css_path, encoding="utf-8") as f:
        css = f.read()
    for url in set(re.findall(r'url\("([^"]+)"\)', css)):
        if url.startswith(("http", "data:")):
            continue
        target = os.path.normpath(os.path.join(os.path.dirname(css_path), url))
        if not os.path.exists(target):
            err("assets/css/knit.css", "нет файла: %s" % url)

    # CSS мотива «Амигуруми» — тоже с проверкой путей
    ami_path = os.path.join(ROOT, "assets", "css", "amigurumi.css")
    if os.path.exists(ami_path):
        with open(ami_path, encoding="utf-8") as f:
            ami = f.read()
        for url in set(re.findall(r'url\("([^"]+)"\)', ami)):
            if url.startswith(("http", "data:")):
                continue
            target = os.path.normpath(os.path.join(os.path.dirname(ami_path), url))
            if not os.path.exists(target):
                err("assets/css/amigurumi.css", "нет файла: %s" % url)


# Шаблоны «захардкоженных» идентификаторов. Ищем по форме записи, а не по
# конкретным значениям: иначе сами значения пришлось бы держать в этом файле.
SECRET_PATTERNS = (
    (r"widgets\.donation\.ru/wloader/[0-9a-fA-F-]{36}", "ID виджета пожертвований"),
    (r"<mixplat-[a-z]+[^>]*id=\"[0-9a-fA-F-]{36}\"", "ID платёжной формы"),
    (r"mc\.yandex\.ru/watch/\d{6,}", "ID Яндекс.Метрики"),
    (r"ym\(\s*\d{6,}", "ID Яндекс.Метрики"),
    (r"top-fwz1\.mail\.ru/counter\?id=\d{6,}", "ID Top.Mail.Ru"),
    (r"_tmr\.push\(\s*\{[^}]*id:\s*[\"']?\d{6,}", "ID Top.Mail.Ru"),
)

SECRET_SCAN_FILES = (
    "tools/build.py",
    "assets/js/analytics.js",
    "assets/js/app.js",
    "assets/js/articles.js",
    "README.md",
    "CLAUDE.md",
)


def check_secrets() -> None:
    """Идентификаторы не должны быть захардкожены в исходниках.

    Это не настоящие секреты — счётчики и виджет видны в HTML любому
    посетителю. Но если оставить их в репозитории, любая чужая сборка начнёт
    слать хиты в боевую статистику организации и показывать её платёжную форму.
    Значения подставляются при сборке из переменных окружения.
    """
    for rel in SECRET_SCAN_FILES:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            text = f.read()
        for pattern, label in SECRET_PATTERNS:
            if re.search(pattern, text):
                err(rel, "захардкожен %s — вынесите в переменную окружения" % label)


def main() -> int:
    pages = sorted(glob.glob(os.path.join(ROOT, "*.html")))
    if not pages:
        print("Не найдено ни одной страницы — сначала запустите tools/build.py")
        return 1

    for path in pages:
        check_page(path)
    check_assets()
    check_secrets()

    print("Проверено страниц: %d" % len(pages))
    if warnings:
        print("\nПредупреждения (%d):" % len(warnings))
        for w in warnings:
            print("  WARN  " + w)
    if errors:
        print("\nОшибки (%d):" % len(errors))
        for e in errors:
            print("  ERROR " + e)
        return 1
    print("\nОшибок нет.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
