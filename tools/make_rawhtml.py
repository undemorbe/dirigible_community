#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Переносит сайт в Craftum двумя частями — сквозной код и блоки страниц.

Craftum даёт вставлять свой HTML на двух уровнях, и это ровно то, как
устроен обычный сайт: общая обвязка отдельно, содержимое страниц отдельно.

    rawhtml/site-html.html   → «Настройки сайта» → вкладка «HTML» →
                               «Пользовательский HTML». Один раз на весь сайт:
                               шрифты, весь knit.css, весь app.js.

    rawhtml/pages/<имя>.html → блок «HTML-код» на соответствующей странице
                               («+» → «Другое» → «HTML-код»). Только разметка,
                               без стилей и скриптов — они уже сквозные.

Страницы не верстаются заново: разметка берётся из собранного сайта,
стили — из assets/css/knit.css, поведение — из assets/js/app.js. Поэтому
результат совпадает с сайтом один в один, а правки дизайна попадают сюда
при обычной пересборке.

Что скрипт меняет при переносе:

1. Скоупит весь CSS под `.dzb`. `:root`, `html` и `body` становятся самим
   блоком, остальные селекторы получают префикс. Специфичность сдвигается
   одинаково у всех правил, поэтому расстановка приоритетов внутри
   knit.css не меняется — это и даёт совпадение.
2. Переписывает относительные пути на абсолютные: внутри блока нет ни
   `assets/`, ни соседних страниц.
3. Добавляет два защитных слоя — сброс чужих правил конструктора и
   фиксацию цвета кнопок. Больше ничего своего в стилях нет.

Запуск (после обычной сборки сайта):

    python3 tools/build.py
    python3 tools/make_rawhtml.py
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT_DIR = os.path.join(REPO, "rawhtml")
PAGES_DIR = os.path.join(OUT_DIR, "pages")

# Адрес сайта — туда ведут ссылки меню, подвала и перекрёстные ссылки
# внутри страниц.
SITE = "https://dirigible.community/"

# Хранилище файлов — это НЕ адрес сайта. Картинки, SVG-тайлы вязки,
# articles.json и тема виджета пожертвований в медиатеку Craftum не
# загружены, поэтому тянутся с нашей сборки. Когда файлы окажутся на
# самом домене — поменять здесь и пересобрать.
ASSETS = "https://undemorbe.github.io/dirigible_community/"

# Соответствие наших страниц адресам в Craftum. Взято из таблицы REDIRECTS
# в build.py — это те самые старые адреса, с которых мы делаем редиректы,
# то есть реальные URL страниц на домене.
#
# ПРОВЕРИТЬ перед публикацией: адреса могли измениться, а страниц,
# которых в выгрузке не было (опросники), на домене может не быть вовсе.
# Чего нет в этой таблице — ссылается на нашу сборку, чтобы ссылка
# хотя бы работала.
CRAFTUM_PATHS = {
    "index.html": "",
    "about.html": "page3",
    "news.html": "page4",
    "documents.html": "page7",
    "donate.html": "page9",
    "reports.html": "page10",
    "education.html": "page11",
    "program.html": "page12",
    "research.html": "justice_research",
    "effective.html": "effective",
    # Опросников в выгрузке не было, адреса назвал заказчик
    "survey-clients.html": "survey-clients",
    "survey-specialists.html": "survey-specialists",
}

PAGE_URLS = {name: SITE + path for name, path in CRAFTUM_PATHS.items()}

SCOPE = ".dzb"

# knit-demo.html — у него свой CSS (amigurumi.css), он не сквозной.
# 404.html — страницу «не найдено» конструктор отдаёт свою.
# Редирект-заглушки старых адресов Craftum отсеиваются отдельно, по
# meta refresh: в конструкторе у страниц свои URL, переносить их незачем.
SKIP = {"knit-demo.html", "404.html"}


# --------------------------------------------------------------- CSS

def _skip_comment(css, i):
    """Если в позиции i начинается комментарий — вернуть позицию за ним."""
    if css.startswith("/*", i):
        end = css.find("*/", i + 2)
        return len(css) if end < 0 else end + 2
    return i


def scope_selector(sel):
    """Один селектор → тот же селектор внутри блока."""
    sel = sel.strip()
    if not sel:
        return sel
    # :root, html и body — это сам блок, а не что-то внутри него
    sel = re.sub(r"^:root\b", SCOPE, sel)
    sel = re.sub(r"^html\s+body\b", SCOPE, sel)
    sel = re.sub(r"^body\b", SCOPE, sel)
    sel = re.sub(r"^html\b", SCOPE, sel)
    if sel.startswith(SCOPE):
        return sel
    return SCOPE + " " + sel


def scope_selectors(prelude):
    """Селекторы через запятую. Запятые внутри :is()/:not() не разделяют
    селекторы, поэтому режем с учётом вложенности."""
    parts = []
    depth = 0
    buf = ""
    for ch in prelude:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    parts.append(buf)
    return ", ".join(scope_selector(p) for p in parts if p.strip())


# at-правила, внутри которых лежат обычные селекторы
NESTED_AT = ("@media", "@supports", "@container", "@layer")

# Свойства, которые тема конструктора задаёт глобально по тегам
# (a, p, h2, img, button) и нередко с !important. Важность бьёт
# специфичность, поэтому без ответного !important наши правила
# проигрывают даже при более точном селекторе: пункты меню, например,
# красились акцентом конструктора вместо своего цвета.
#
# Список намеренно узкий. Эти свойства в разметке инлайном не задаются
# (там только align-items, display, gap, margin, max-width, padding),
# так что инлайновые стили ничего не теряют.
def scope_css(css):
    """Переписывает таблицу стилей так, чтобы она действовала только
    внутри блока."""
    out = []
    i = 0
    n = len(css)
    while i < n:
        j = _skip_comment(css, i)
        if j != i:
            i = j
            continue
        if css[i].isspace():
            out.append(css[i])
            i += 1
            continue

        # прелюдия правила — до '{' или ';'
        k = i
        while k < n and css[k] not in "{;}":
            nk = _skip_comment(css, k)
            k = nk if nk != k else k + 1
        if k >= n:
            out.append(css[i:])
            break
        if css[k] in ";}":
            # @charset/@import и прочие правила без тела
            out.append(css[i:k + 1])
            i = k + 1
            continue

        prelude = css[i:k].strip()

        # парная закрывающая скобка
        depth = 1
        m = k + 1
        while m < n and depth:
            nm = _skip_comment(css, m)
            if nm != m:
                m = nm
                continue
            if css[m] == "{":
                depth += 1
            elif css[m] == "}":
                depth -= 1
            m += 1
        body = css[k + 1:m - 1]

        if prelude.startswith("@"):
            at = prelude.split(None, 1)[0].lower()
            if at in NESTED_AT:
                out.append(prelude + " {" + scope_css(body) + "}")
            else:
                # @keyframes, @font-face, @page — селекторов внутри нет
                out.append(prelude + " {" + body + "}")
        else:
            out.append(scope_selectors(prelude) + " {" + body + "}")
        i = m
    return "".join(out)


def absolutize_css(css):
    """url(../img/...) и прочие относительные пути → абсолютные."""
    def repl(m):
        quote, path = m.group(1), m.group(2)
        if path.startswith(("http:", "https:", "data:", "#", "//")):
            return m.group(0)
        path = re.sub(r"^(\.\./)+", "", path)
        if not path.startswith("assets/"):
            path = "assets/" + path
        return "url(%s%s%s%s)" % (quote, ASSETS, path, quote)

    return re.sub(r"url\((['\"]?)([^)'\"]+)\1\)", repl, css)


# -------------------------------------------------------------- HTML

def absolutize_html(html):
    """Пути к ассетам и ссылки на страницы сайта → абсолютные."""
    def attr(m):
        name, quote, value = m.group(1), m.group(2), m.group(3)
        if value.startswith(("http:", "https:", "//", "data:", "#",
                             "mailto:", "tel:")):
            return m.group(0)
        # Ссылка на страницу сайта: если её адрес в Craftum известен —
        # ведём туда, иначе на нашу сборку (см. PAGE_URLS).
        if name == "href":
            file, _, tail = value.partition("#")
            if file in PAGE_URLS:
                return "%s=%s%s%s%s" % (name, quote, PAGE_URLS[file],
                                        ("#" + tail) if tail else "", quote)
        return "%s=%s%s%s%s" % (name, quote, ASSETS, value.lstrip("/"), quote)

    # Кроме src/href/poster путь лежит и в data-атрибутах: виджет
    # пожертвований забирает тему из data-donate-style, лента материалов —
    # адрес данных из data-articles-endpoint. Относительными они здесь
    # не работают, за пределами сайта их некуда разрешать.
    html = re.sub(
        r'\b(src|href|poster|data-donate-style|data-articles-endpoint)'
        r'=(["\'])((?:assets/|[a-z0-9_\-]+\.html)[^"\']*)\2',
        attr, html)

    # Карточки ленты рисует articles.js из articles.json, а пути к картинкам
    # и страницам там относительные. Разрешать их внутри блока не от чего,
    # поэтому отдаём ленте и базу для файлов, и карту адресов страниц:
    # лежат они на разных хостах.
    html = re.sub(
        r"\bdata-articles(?=[\s>])",
        'data-articles data-articles-base="%s" data-articles-links=\'%s\''
        % (ASSETS, json.dumps(PAGE_URLS, ensure_ascii=False)),
        html, count=1)
    return html


# ------------------------------------------------------- защитные слои

# Сброс чужих правил конструктора. На странице Craftum висят свои стили
# на p/h2/img/button, и они бьют наследование от блока — сбрасывать
# приходится явно. :where() даёт нулевую специфичность, иначе этот слой
# победил бы сам knit.css.
GUARD_RESET = """
/* --- защита от стилей страницы-хозяина --- */
%(s)s :where(h1,h2,h3,h4,h5,h6,p,li,dt,dd,span,a,b,strong,em,i,small,
             figcaption,button,label,time,blockquote,figure,ul,ol,dl) {
  font-family: inherit; font-size: inherit; font-weight: inherit;
  font-style: inherit; line-height: inherit; letter-spacing: normal;
  text-transform: none; text-align: inherit; color: inherit; margin: 0;
}
%(s)s :where(ul,ol) { padding: 0; list-style: none; }
%(s)s :where(img,svg,video) { border: 0; border-radius: 0; box-shadow: none; }
%(s)s :where(button) { margin: 0; padding: 0; background: transparent;
  border: 0; border-radius: 0; box-shadow: none; text-transform: none; }
""" % {"s": SCOPE}

# Тема конструктора красит ссылки своим акцентом, и правило может быть
# с !important. Заметно это только на кнопках: белая надпись на оранжевой
# кнопке сливается с фоном.
GUARD_BTN = """
/* --- защита цвета от темы конструктора ---
   Тема Craftum красит ссылки своим акцентом, и правило может стоять
   с !important. Важность бьёт специфичность, поэтому без ответного
   !important наши цвета проигрывают при любом селекторе.

   Список намеренно короткий — только места, где цвет задаёт knit.css,
   а не наследование. Пробовали ставить !important всем свойствам
   подряд: сокращённая запись начинала бить длинную, и пропадали
   обводка активного пункта меню (border против border-color)
   и пунктирный стежок на светлых кнопках (.btn::after против
   .btn--ghost::after). */
%(s)s a.btn, %(s)s a.btn:hover, %(s)s a.btn:focus, %(s)s a.btn:visited {
  color: var(--btn-fg) !important;
  text-decoration: none !important;
}
%(s)s .nav__link, %(s)s .nav__link:visited { color: var(--ink) !important; }
%(s)s .nav__link[aria-current="page"] { color: var(--accent-deep) !important; }
%(s)s .brand, %(s)s .brand:visited, %(s)s .brand__name, %(s)s .brand__sub {
  color: var(--ink) !important;
}
%(s)s .footer__list a, %(s)s .footer__list a:visited { color: var(--ink) !important; }
%(s)s .footer__list a:hover { color: var(--accent-deep) !important; }

/* --- поправки на то, что .dzb это блок, а не <body> --- */
%(s)s {
  /* у body было min-height: 100svh — на блоке это растянуло бы каждый
     кусок страницы на целый экран, а шапку особенно */
  min-height: 0;
  /* body прятал горизонтальное переполнение через overflow-x: hidden.
     На блоке это делает его скролл-контейнером, и position: fixed/sticky
     внутри начинает вести себя иначе. clip обрезает так же, но
     скролл-контейнер не создаёт. */
  overflow-x: clip;
  /* Конструктор центрирует содержимое своих блоков. Наследование
     пробивало сброс насквозь (там text-align: inherit), и по центру
     уезжали тексты карточек, ссылки на документы и опросники.
     Заземляем выравнивание на самом блоке — дальше внутри всё
     наследуется уже от него, а .text-center работает как и работал. */
  text-align: left;
  /* сюда же: чужие отступы и выравнивание блока целиком */
  padding: 0;

  /* Блок лежит внутри контейнера конструктора, у которого свои поля по
     бокам, — полотно не доходило до краёв экрана. Растягиваем блок на
     всю ширину окна: отрицательный отступ считается от собственной
     ширины, поэтому приём безвреден и там, где полей нет (тогда
     50%% - 50vw даёт ноль). Боковые поля самого содержимого никуда
     не деваются — их держит .container. */
  width: var(--dzb-vw, 100vw);
  max-width: var(--dzb-vw, 100vw);
  /* литеральный процент в %%-строке пишется как %%%% */
  margin-inline: calc(50%% - var(--dzb-vw, 100vw) / 2);
  margin-block: 0;
}

/* Клубки лежат на z-index: -1 — на сайте они уходили за фон <body>,
   который рисуется на канвасе и ничего не перекрывает. У блока фон
   обычный, и клубки прятались под ним. Возвращаем в поток: в разметке
   они идут раньше контента, поэтому всё равно остаются под текстом. */
%(s)s .pompom { z-index: auto; }

/* Подвал отбивается от контента внешним отступом — на сайте в этом
   просвете видно полотно и фестоны последней секции. Отдельным блоком
   тот же отступ показывал белый фон страницы конструктора. Поэтому
   отступ делаем внутренним, а блоку даём то же полотно, что и у body:
   просвет остаётся, но он наш. */
%(s)s.dzb-chrome--footer {
  margin-top: 0;
  padding-top: clamp(2rem, 6vw, 4rem);
  background-color: var(--wool-50);
  background-image: url("%(stock)s");
  background-size: 44px 33px;
}
%(s)s.dzb-chrome--footer .footer { margin-top: 0; }

/* Шапка.
   position: sticky здесь не годится: липкий элемент держится в пределах
   своего родителя, а конструктор заворачивает блок «HTML-код» в свой
   контейнер высотой ровно с шапку — прилипать некуда, она уезжает вверх
   вместе с ним. Поэтому fixed, а место под неё освобождает скрипт
   сквозного кода: он измеряет высоту и ставит body padding-top. */
%(s)s.dzb-chrome--header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  overflow: visible;
}
%(s)s.dzb-chrome--header .header { position: static; }

/* Высота шапки известна заранее (--header-h), поэтому отступ под неё
   задаём сразу стилями. Скрипт потом уточнит его по факту, но контент
   уже не прыгает на величину шапки при загрузке. */
body:has(> %(s)s.dzb-chrome--header) { padding-top: 80px; }

/* Плавное появление.
   Блоки конструктор вставляет не одновременно: шапка, содержимое и
   подвал встают по очереди, плюс дорисовка шрифтов. Без этого страница
   на глазах дёргается. Показываем её одним движением, когда разметка
   на месте — класс ставит скрипт. */
.dzb-js %(s)s { opacity: 0; }
%(s)s.dzb-shown { animation: dzb-fade-in .45s var(--ease) both; }
@keyframes dzb-fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: none; }
}
/* Шапку не сдвигаем: она fixed, трансформация создала бы containing
   block и выдвижная панель .nav (position: fixed) схлопнулась бы
   под шапку — грабли, на которые уже наступали в knit.css. */
%(s)s.dzb-chrome--header.dzb-shown { animation-name: dzb-fade-in-flat; }
@keyframes dzb-fade-in-flat {
  from { opacity: 0; }
  to   { opacity: 1; }
}
@media (prefers-reduced-motion: reduce) {
  %(s)s.dzb-shown { animation-duration: .001ms; }
}

/* --- лейбл платформы под подвалом ---
   Конструктор дорисовывает свою подпись «Конструктор сайтов Craftum»
   после всех блоков. Разметки её в выгрузке нет, поэтому скрипт находит
   её по ссылке на craftum.com и вешает класс. Убирать подпись нечем —
   это условие тарифа; приводим к виду сайта, чтобы не выбивалась.

   Цвета заданы литералами: токены шерсти и чернил объявлены на самих
   блоках, а подпись лежит вне них и ничего не наследует. */
.dzb-platform {
  background-color: #F4EADA !important;
  background-image: url("%(seed)s") !important;
  background-size: 26px 26px !important;
  border-top: 2px dashed rgba(51, 41, 31, .22) !important;
  color: #927E67 !important;
  font-family: "Nunito", "Segoe UI", system-ui, sans-serif !important;
  font-size: .875rem !important;
  text-align: center !important;
  padding: 1rem !important;
}
.dzb-platform a {
  color: #146189 !important;
  text-underline-offset: .22em;
}
.dzb-platform img, .dzb-platform svg { opacity: .75; }
""" % {"s": SCOPE,
       "seed": ASSETS + "assets/img/knit-seed.svg",
       "stock": ASSETS + "assets/img/knit-stockinette.svg"}


SITE_HEAD = """<!-- =====================================================================
     АНО «Дирижабль» — сквозной код сайта для Craftum.

     Куда вставлять: «Настройки сайта» → вкладка «HTML» →
     поле «Пользовательский HTML». Один раз на весь сайт, затем
     «Опубликовать все страницы».

     Что внутри: шрифты, весь assets/css/knit.css (заскоупленный под .dzb),
     весь assets/js/app.js и assets/js/articles.js. Разметка страниц сюда
     не входит — она лежит отдельными блоками «HTML-код», см. rawhtml/pages/.

     Аналитики здесь нет: счётчики в Craftum ставятся его собственными
     средствами, в том же поле «Пользовательский HTML».

     Файл собран скриптом tools/make_rawhtml.py. Руками не править:
     правки идут в knit.css / app.js, затем пересборка.
     ===================================================================== -->
<!-- Блоки прячутся до плавного появления только при работающем JS:
     иначе при отключённых скриптах страница осталась бы пустой. -->
<script>document.documentElement.classList.add("dzb-js")</script>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Comfortaa:wght@500;700&amp;family=Nunito:wght@400;600;700;800&amp;display=swap">
<style>
"""

SITE_SCRIPT = """</style>
<script>
/* Поведенческий слой сайта. Запускается один раз на страницу, даже если
   сквозной код по недосмотру окажется вставлен дважды. */
(function () {
  "use strict";
  if (window.__dirigibleBooted) { return; }
  window.__dirigibleBooted = true;

%(app)s

%(articles)s

  /* app.js инициализирует то, что уже есть в документе. Блоки «HTML-код»
     конструктор может дорисовать позже (предпросмотр, ленивые секции),
     поэтому следим за появлением новых .dzb и доинициализируем их.

     Первый проход только помечает блоки: их app.js уже обработал.
     Инициализировать их второй раз нельзя — initCarousels добавил бы
     карусели второй комплект точек. */
  var firstSweep = true;

  function claim(root) {
    if (!root || root.getAttribute("data-dzb-ready") === "1") { return; }
    root.setAttribute("data-dzb-ready", "1");
    var api = window.Dirigible;
    if (firstSweep || !api) { return; }
    api.initCarousels(root);
    api.initReveal(root);
    api.initVideo(root);
  }

  function reveal() {
    Array.prototype.forEach.call(document.querySelectorAll(".dzb"),
      function (el) { el.classList.add("dzb-shown"); });
  }

  function sweep() {
    Array.prototype.forEach.call(document.querySelectorAll(".dzb"), claim);
    firstSweep = false;
    /* Ленту материалов зовём всегда: её boot() отрабатывает раньше, чем
       конструктор вставит блок. Повторов не будет — articles.js помечает
       контейнер флагом data-articles-ready. */
    if (window.DirigibleArticles) { window.DirigibleArticles.boot(); }
  }

  /* Активный пункт меню.
     markCurrentNav() из app.js сравнивает последний сегмент пути, и на
     главной это не работает: её адрес заканчивается слешем, а в ссылке
     стоит полный URL. Сравниваем нормализованные пути целиком. */
  function norm(href) {
    try {
      var p = new URL(href, location.href);
      if (p.host !== location.host) { return null; }
      return p.pathname.replace(/\\/index\\.html$/, "/").replace(/\\/+$/, "/");
    } catch (e) { return null; }
  }

  function markNav() {
    var here = norm(location.href);
    if (!here) { return; }
    var links = document.querySelectorAll(".dzb .nav__link, .dzb .footer__list a");
    Array.prototype.forEach.call(links, function (a) {
      if (norm(a.getAttribute("href")) === here) {
        a.setAttribute("aria-current", "page");
      } else {
        a.removeAttribute("aria-current");
      }
    });
  }

  /* Шапка-блок стоит position: fixed и места в потоке не занимает —
     без компенсации содержимое страницы уехало бы под неё. Высоту
     меряем по факту: она зависит от ширины окна и от шрифта. */
  /* 100vw считается вместе с полосой прокрутки, и растянутый блок
     оказался бы шире страницы — появился бы горизонтальный скролл.
     Поэтому ширину окна отдаём скриптом, уже без полосы. */
  function measureViewport() {
    document.documentElement.style.setProperty(
      "--dzb-vw", document.documentElement.clientWidth + "px");
  }

  function offsetHeader() {
    var header = document.querySelector(".dzb-chrome--header");
    if (!header) { return; }
    var h = Math.round(header.getBoundingClientRect().height);
    if (!h) { return; }
    document.body.style.paddingTop = h + "px";
    /* Переменную --header-h не трогаем: из неё растёт min-height самой
       шапки (.header__inner), и подстановка измеренной высоты даёт
       обратную связь — шапка раздувается до нескольких тысяч пикселей. */
  }

  /* Подпись конструктора под подвалом. Её разметка нам неизвестна —
     в выгрузке сайта её нет, она появляется только на публикации.
     Ищем по ссылке на craftum.com за пределами наших блоков и помечаем
     ближайшего прямого потомка body, чтобы оформить его как часть сайта. */
  function markPlatform() {
    var links = document.querySelectorAll('a[href*="craftum.com"]');
    Array.prototype.forEach.call(links, function (a) {
      if (a.closest(".dzb")) { return; }
      var box = a;
      while (box.parentElement && box.parentElement !== document.body) {
        box = box.parentElement;
      }
      box.classList.add("dzb-platform");
    });
  }

  function watch() {
    sweep();
    markNav();
    markPlatform();
    measureViewport();
    offsetHeader();
    window.addEventListener("resize", function () {
      measureViewport();
      offsetHeader();
    }, { passive: true });
    /* Первый замер случается до того, как применится шрифт и дорисуется
       рамка шапки, — перемеряем после загрузки. */
    window.addEventListener("load", offsetHeader);
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(offsetHeader);
    }

    /* Показываем следующим кадром — к этому моменту отступ под шапку
       уже выставлен, и появление идёт без скачка. Страховка на случай,
       если шрифты или наблюдатели почему-то не отработают. */
    window.requestAnimationFrame(reveal);
    window.setTimeout(reveal, 1200);
    if (window.ResizeObserver) {
      var header = document.querySelector(".dzb-chrome--header");
      if (header) { new ResizeObserver(offsetHeader).observe(header); }
    }
    if (!window.MutationObserver) { return; }
    new MutationObserver(function () {
      sweep(); markNav(); markPlatform(); offsetHeader(); reveal();
    })
      .observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", watch);
  } else {
    watch();
  }
})();
</script>
"""

PAGE_TPL = """<!-- =====================================================================
     АНО «Дирижабль» — %(title)s (%(slug)s).

     Куда вставлять: блок «HTML-код» на соответствующей странице
     («+» под блоком → вкладка «Другое» → «HTML-код» → «Настроить»).

     Здесь только разметка. Стили и скрипты — в сквозном коде сайта,
     см. rawhtml/site-html.html; без него блок будет без оформления.

     Фрагмент намеренно без <!doctype>, <html>, <head> и <body>:
     Craftum вставляет его внутрь своей страницы.

     Собрано скриптом tools/make_rawhtml.py, руками не править.
     ===================================================================== -->
<section class="dzb">
%(body)s
</section>
"""


CHROME_TPL = """<!-- =====================================================================
     АНО «Дирижабль» — %(what)s сайта.

     Куда вставлять: блок «HTML-код» («+» → вкладка «Другое» → «HTML-код»),
     %(where)s страницы. Затем закрепить блок на всех страницах.

     Здесь только разметка. Стили и скрипты — в сквозном коде сайта,
     см. rawhtml/site-html.html; без него блок будет без оформления.

     Фрагмент намеренно без <!doctype>, <html>, <head> и <body>:
     Craftum вставляет его внутрь своей страницы.

     Собрано скриптом tools/make_rawhtml.py, руками не править.
     ===================================================================== -->
<div class="dzb dzb-chrome dzb-chrome--%(kind)s">
%(body)s
</div>
"""


def page_title(html):
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def main():
    knit = open(os.path.join(REPO, "assets/css/knit.css"), encoding="utf-8").read()
    # @charset осмыслен только в начале отдельного файла стилей. Внутри
    # <style> он бесполезен, а конструктор его к тому же выталкивает
    # на страницу видимым текстом.
    knit = re.sub(r"^\s*@charset[^;]+;\s*", "", knit)
    app = open(os.path.join(REPO, "assets/js/app.js"), encoding="utf-8").read()
    # Лента материалов нужна только на news.html и research.html, но сквозной
    # код один на весь сайт. Это безопасно: без контейнера [data-articles]
    # модуль молча ничего не делает.
    articles = open(os.path.join(REPO, "assets/js/articles.js"),
                    encoding="utf-8").read()

    # ------------------------------------------------ сквозной код
    css = absolutize_css(scope_css(knit))
    site = (SITE_HEAD
            + GUARD_RESET
            + "\n/* --- assets/css/knit.css, заскоуплен под .dzb --- */\n"
            + css
            + GUARD_BTN
            + SITE_SCRIPT % {"app": app, "articles": articles})

    os.makedirs(OUT_DIR, exist_ok=True)
    site_path = os.path.join(OUT_DIR, "site-html.html")
    with open(site_path, "w", encoding="utf-8") as f:
        f.write(site)
    print("сквозной код: rawhtml/site-html.html — %.1f КБ"
          % (len(site.encode("utf-8")) / 1024))

    # ------------------------------------------- шапка и подвал
    # Блок «HTML-код» (категория «Другое») штатной кнопкой «показывать на
    # всех страницах» не закрепляется — она работает только для блоков
    # «Меню» и «Подвал». Поэтому шапку и подвал отдаём отдельными файлами:
    # вставить один раз и закрепить средствами конструктора.
    index = open(os.path.join(REPO, "index.html"), encoding="utf-8").read()
    for kind, tag, what, where in (
        ("header", "header", "шапка", "в самом верху"),
        ("footer", "footer", "подвал", "в самом низу"),
    ):
        m = re.search(r"<%s[^>]*>.*?</%s>" % (tag, tag), index, re.S)
        if not m:
            raise SystemExit("в index.html не найден <%s>" % tag)
        chrome = CHROME_TPL % {
            "kind": kind,
            "what": what,
            "where": where,
            # aria-current="page" в сборке стоит на «Главной»: шапка
            # вырезана из index.html. Блок один на все страницы, поэтому
            # отметку снимаем — её расставит скрипт сквозного кода.
            "body": re.sub(r'\s*aria-current="page"', "",
                           absolutize_html(m.group(0))).strip(),
        }
        with open(os.path.join(OUT_DIR, kind + ".html"), "w",
                  encoding="utf-8") as f:
            f.write(chrome)
    print("шапка и подвал: rawhtml/header.html, rawhtml/footer.html")

    # ------------------------------------------------ блоки страниц
    os.makedirs(PAGES_DIR, exist_ok=True)
    for old in os.listdir(PAGES_DIR):
        os.remove(os.path.join(PAGES_DIR, old))

    made = 0
    for name in sorted(os.listdir(REPO)):
        if not name.endswith(".html") or name in SKIP:
            continue
        src = open(os.path.join(REPO, name), encoding="utf-8").read()
        if re.search(r'http-equiv=["\']refresh', src, re.I):
            continue        # редирект-заглушка старого адреса Craftum
        m = re.search(r"<main[^>]*>(.*?)</main>", src, re.S)
        if not m:
            continue
        block = PAGE_TPL % {
            "title": page_title(src),
            "slug": name,
            "body": absolutize_html(m.group(1)).strip(),
        }
        with open(os.path.join(PAGES_DIR, name), "w", encoding="utf-8") as f:
            f.write(block)
        made += 1

    if not made:
        raise SystemExit("ни одной страницы не найдено — сначала запустите "
                         "python3 tools/build.py")
    print("блоки страниц: rawhtml/pages/ — %d файлов" % made)


if __name__ == "__main__":
    main()
