#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генерация SVG-тайлов «объёмной глади» для стиля амигуруми.

Зачем скрипт, а не один файл: SVG подключается из CSS через url(), где
currentColor не работает, поэтому окрасить один тайл переменной нельзя.
Плоские текстуры (резинка, жемчужная, соты) собраны на CSS-градиентах и
красятся переменными — им файлы не нужны. Объёмной глади нужны градиенты
вдоль пряди и тень под петлёй, поэтому для неё генерируем по файлу на цвет.

Запуск:  python3 tools/make_yarn.py
"""

from __future__ import annotations

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "img", "amigurumi")

# name -> (основной цвет пряжи, блик, тень)
YARNS = {
    "cobalt": ("#1B6FC9", "#5AA6EE", "#0E4585"),
    "azure":  ("#2E9BE0", "#7FCcF5", "#17679C"),
    "orange": ("#E8761E", "#FFB067", "#A84C08"),
    "cream":  ("#F1E4CE", "#FFF8EC", "#CBB595"),
    "sand":   ("#DCC7A6", "#F5E8D0", "#AE9370"),
    "berry":  ("#B4436B", "#E2839F", "#7A2846"),
    "sage":   ("#6E8F63", "#A8C79C", "#46603D"),
}

# Тайл 48×36. Колонки петель строго вертикальны — как в настоящей лицевой
# глади. Высота петли (44) больше шага ряда (36), поэтому ряды идут внахлёст:
# нижние концы предыдущего ряда уходят под следующий. Без нахлёста получается
# «черепица», а не вязание.
TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="48" height="26" viewBox="0 0 48 26">
  <defs>
    <linearGradient id="strand" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0"   stop-color="{lo}"/>
      <stop offset=".32" stop-color="{base}"/>
      <stop offset=".58" stop-color="{hi}"/>
      <stop offset="1"   stop-color="{base}"/>
    </linearGradient>
    <radialGradient id="hollow" cx=".5" cy=".25" r=".6">
      <stop offset="0" stop-color="{lo}" stop-opacity=".5"/>
      <stop offset="1" stop-color="{lo}" stop-opacity="0"/>
    </radialGradient>

    <!-- одна петля: пряди сходятся книзу в «V»; вверху расходятся и уходят
         под ряд, который лежит выше -->
    <g id="loop">
      <ellipse cx="12" cy="9" rx="8.5" ry="8" fill="url(#hollow)"/>
      <path d="M2 -7 C 3 6, 8 19, 12 30" fill="none" stroke="{lo}"
            stroke-width="9" stroke-linecap="round" opacity=".45"
            transform="translate(0.7 1.5)"/>
      <path d="M22 -7 C 21 6, 16 19, 12 30" fill="none" stroke="{lo}"
            stroke-width="9" stroke-linecap="round" opacity=".45"
            transform="translate(0.7 1.5)"/>
      <path d="M2 -7 C 3 6, 8 19, 12 30" fill="none" stroke="url(#strand)"
            stroke-width="8.5" stroke-linecap="round"/>
      <path d="M22 -7 C 21 6, 16 19, 12 30" fill="none" stroke="url(#strand)"
            stroke-width="8.5" stroke-linecap="round"/>
      <path d="M2.6 -5 C 3.6 6, 8.2 17, 11.7 27" fill="none" stroke="{hi}"
            stroke-width="1.9" stroke-linecap="round" opacity=".42"/>
      <path d="M21.4 -5 C 20.4 6, 15.8 17, 12.3 27" fill="none" stroke="{hi}"
            stroke-width="1.9" stroke-linecap="round" opacity=".42"/>
    </g>

    <!-- ряд петель, с запасом по краям для бесшовности -->
    <g id="row">
      <use href="#loop" x="-24"/>
      <use href="#loop" x="0"/>
      <use href="#loop" x="24"/>
      <use href="#loop" x="48"/>
    </g>
  </defs>

  <rect width="48" height="26" fill="{base}"/>
  <!-- порядок важен: ряд, лежащий выше, рисуется последним и прячет под собой
       верхние концы прядей нижнего ряда -->
  <use href="#row" y="52"/>
  <use href="#row" y="26"/>
  <use href="#row" y="0"/>
  <use href="#row" y="-26"/>
</svg>
"""


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    for name, (base, hi, lo) in YARNS.items():
        svg = TEMPLATE.format(base=base, hi=hi, lo=lo)
        path = os.path.join(OUT, "yarn-%s.svg" % name)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(svg)
        print("  yarn-%s.svg  %s" % (name, base))
    print("Готово: %d тайлов в assets/img/amigurumi/" % len(YARNS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
