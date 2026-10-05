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
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT_DIR = os.path.join(REPO, "rawhtml")
PAGES_DIR = os.path.join(OUT_DIR, "pages")

# Откуда блоки берут картинки и куда ведут ссылки.
# Craftum раздаёт только то, что загружено в его медиатеку, поэтому ассеты
# тянутся с нашей же сборки. Сайт переехал — поменять здесь и пересобрать.
BASE = "https://undemorbe.github.io/dirigible_community/"

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
        return "url(%s%s%s%s)" % (quote, BASE, path, quote)

    return re.sub(r"url\((['\"]?)([^)'\"]+)\1\)", repl, css)


# -------------------------------------------------------------- HTML

def absolutize_html(html):
    """Пути к ассетам и ссылки на страницы сайта → абсолютные."""
    def attr(m):
        name, quote, value = m.group(1), m.group(2), m.group(3)
        if value.startswith(("http:", "https:", "//", "data:", "#",
                             "mailto:", "tel:")):
            return m.group(0)
        return "%s=%s%s%s%s" % (name, quote, BASE, value.lstrip("/"), quote)

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
    # поэтому отдаём ленте базу явно.
    html = re.sub(r"\bdata-articles(?=[\s>])",
                  'data-articles data-articles-base="%s"' % BASE, html, count=1)
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
/* --- цвет кнопок поверх темы конструктора --- */
%(s)s a.btn, %(s)s a.btn:hover, %(s)s a.btn:focus, %(s)s a.btn:visited {
  color: var(--btn-fg) !important;
  text-decoration: none !important;
}
""" % {"s": SCOPE}


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

  function sweep() {
    Array.prototype.forEach.call(document.querySelectorAll(".dzb"), claim);
    firstSweep = false;
    /* Ленту материалов зовём всегда: её boot() отрабатывает раньше, чем
       конструктор вставит блок. Повторов не будет — articles.js помечает
       контейнер флагом data-articles-ready. */
    if (window.DirigibleArticles) { window.DirigibleArticles.boot(); }
  }

  function watch() {
    sweep();
    if (!window.MutationObserver) { return; }
    new MutationObserver(sweep).observe(document.body,
      { childList: true, subtree: true });
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


def page_title(html):
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def main():
    knit = open(os.path.join(REPO, "assets/css/knit.css"), encoding="utf-8").read()
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
