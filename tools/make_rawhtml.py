#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает rawhtml/index.html — самодостаточную тестовую страницу
для блока «HTML-код» в Craftum.

SVG-тайлы вязки в основном сайте лежат отдельными файлами в assets/img/.
Внутри блока Craftum внешних файлов нет, поэтому тайлы встраиваются
как data: URI. Кодировать их руками легко испортить, поэтому файл
собирается скриптом.

Разметка и стили — в tools/rawhtml.tpl; правки идут туда, затем:

    python3 tools/make_rawhtml.py
"""
import os
import re
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(REPO, "rawhtml", "index.html")

CDN = ("https://274418.selcdn.ru/"
       "cv08300-33250f0d-0664-43fc-9dbf-9d89738d114e/uploads/720494/")


def tile(name):
    """SVG-тайл → data: URI для url() в CSS."""
    src = open(os.path.join(REPO, "assets/img", name), encoding="utf-8").read()
    src = re.sub(r"<!--.*?-->", "", src, flags=re.S)
    src = re.sub(r"\s+", " ", src).strip()
    src = src.replace("> <", "><")
    return "data:image/svg+xml," + quote(src, safe="/:=,;()'. -")


TEAM = [
    ("48f6e88a-9da6-44ee-a33d-707b2aca8512.jpg", "Елена Индакова",
     "Учредитель АНО «Дирижабль», сетевой терапевт, социальный педагог"),
    ("cc64f794-a318-4799-802d-35fe5e800f3b.jpg", "Татьяна Арчакова",
     "Директор АНО Центр развития социальных практик «Дирижабль»"),
    ("66741c08-a786-43fe-b6ca-4ffdee0f74a7.jpg", "Михаил Пономарёв",
     "Сетевой терапевт, клинический психолог, к. пс. н."),
    ("b5a85580-1b0a-4abf-99e5-c19fd3d4d9e5.jpg", "Ольга Евстешина",
     "Сетевой терапевт, тренер и супервизор по технологии "
     "«Работа с сетью социальных контактов»"),
    ("a834f929-922f-425e-94f7-e0c1a166231c.jpg", "Васанта Романова",
     "Сетевой терапевт, тренер и супервизор по технологии "
     "«Работа с сетью социальных контактов», к. пс. н."),
    ("3f73d44f-8d9e-4f7b-af34-3b7c185e15db.jpg", "Мария Кузнецова",
     "Сетевой терапевт, тренер и супервизор по технологии "
     "«Работа с сетью социальных контактов»"),
    ("52f2d795-45b8-4137-b20b-5c27452c867c.jpg", "Фатима Абакарова",
     "Менеджер проектов"),
    ("abfaa305-79ce-4541-9a2d-0f5c8292231e.jpg", "Инна Михайлова",
     "Куратор семей, психолог"),
]

people = "\n".join(
    '        <figure class="dzb-person">\n'
    '          <img class="dzb-person__photo" src="%s%s" alt="Портрет: %s"\n'
    '               loading="lazy" decoding="async">\n'
    '          <figcaption>\n'
    '            <span class="dzb-person__name">%s</span>\n'
    '            <span class="dzb-person__role">%s</span>\n'
    '          </figcaption>\n'
    '        </figure>' % (CDN, f, name, name, role)
    for f, name, role in TEAM
)

TPL = open(os.path.join(HERE, "rawhtml.tpl"), encoding="utf-8").read()

html = (TPL
        .replace("__STOCKINETTE__", tile("knit-stockinette.svg"))
        .replace("__SEED__", tile("knit-seed.svg"))
        .replace("__CABLE__", tile("knit-cable.svg"))
        .replace("__CDN__", CDN)
        .replace("__PEOPLE__", people))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print("записан %s — %.1f КБ" % (OUT, len(html.encode("utf-8")) / 1024))
