#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает rawhtml/index.html — главную страницу сайта одним
самодостаточным фрагментом для блока «HTML-код» в Craftum.

Страница не верстается заново: берётся готовая сборка. Разметка —
из `index.html` (секция <main>), стили — из `assets/css/knit.css`,
поведение — из `assets/js/app.js`. Так перенос остаётся один в один
с сайтом, а правки дизайна попадают сюда сами.

Три вещи, которые делает скрипт:

1. Скоупит весь CSS под `.dzb`. `:root`, `html` и `body` становятся
   самим блоком, остальные селекторы получают префикс. Специфичность
   при этом сдвигается одинаково у всех правил, поэтому расстановка
   приоритетов внутри knit.css не меняется.
2. Переписывает относительные пути на абсолютные: внутри блока нет
   ни `assets/`, ни соседних страниц.
3. Добавляет защитный слой — сброс чужих правил конструктора и
   фиксацию цвета кнопок. Больше ничего своего в стилях нет.

Запуск:

    python3 tools/make_rawhtml.py
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(REPO, "rawhtml", "index.html")

# Откуда блок берёт картинки и куда ведут ссылки.
# Craftum раздаёт только то, что загружено в его медиатеку, поэтому
# ассеты тянутся с нашей же сборки на GitHub Pages. Если сайт переедет
# (например на Cloudflare Pages) — поменять здесь и пересобрать.
BASE = "https://undemorbe.github.io/dirigible_community/"

SCOPE = ".dzb"


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
    # :root и body — это сам блок, а не что-то внутри него
    sel = re.sub(r"^:root\b", SCOPE, sel)
    sel = re.sub(r"^html\s+body\b", SCOPE, sel)
    sel = re.sub(r"^body\b", SCOPE, sel)
    sel = re.sub(r"^html\b", SCOPE, sel)
    if sel.startswith(SCOPE):
        return sel
    return SCOPE + " " + sel


def scope_selectors(prelude):
    """Список селекторов через запятую. Запятые внутри :is()/:not()
    не разделяют селекторы, поэтому режем с учётом вложенности."""
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
            # @charset/@import и прочие правила-без-тела
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
        return '%s=%s%s%s%s' % (name, quote, BASE, value.lstrip("/"), quote)

    # src/href/srcset-одиночки на assets/ и на страницы сайта
    html = re.sub(
        r'\b(src|href|poster)=(["\'])((?:assets/|[a-z0-9_\-]+\.html)[^"\']*)\2',
        attr, html)
    return html


# Сброс чужих правил конструктора. На странице Craftum висят свои
# стили на p/h2/img/button, и они бьют наследование от блока —
# сбрасывать приходится явно. :where() даёт нулевую специфичность,
# иначе этот слой победил бы сам knit.css.
GUARD_RESET = """
/* --- защита от стилей страницы-хозяина (добавлено make_rawhtml.py) --- */
%(s)s :where(h1,h2,h3,h4,h5,h6,p,li,dt,dd,span,a,b,strong,em,i,small,
             figcaption,button,label,time,blockquote,figure,ul,ol,dl,dd) {
  font-family: inherit; font-size: inherit; font-weight: inherit;
  font-style: inherit; line-height: inherit; letter-spacing: normal;
  text-transform: none; text-align: inherit; color: inherit; margin: 0;
}
%(s)s :where(ul,ol) { padding: 0; list-style: none; }
%(s)s :where(img,svg,video) { border: 0; border-radius: 0; box-shadow: none; }
%(s)s :where(button) { margin: 0; padding: 0; background: transparent;
  border: 0; border-radius: 0; box-shadow: none; text-transform: none; }
""" % {"s": SCOPE}

# Тема конструктора красит ссылки своим акцентом, и правило может
# оказаться с !important. Кнопки — единственное место, где это заметно
# ломает вид: белая надпись на оранжевой кнопке сливается с фоном.
GUARD_BTN = """
/* --- цвет кнопок поверх темы конструктора (добавлено make_rawhtml.py) --- */
%(s)s a.btn, %(s)s a.btn:hover, %(s)s a.btn:focus, %(s)s a.btn:visited {
  color: var(--btn-fg) !important;
  text-decoration: none !important;
}
""" % {"s": SCOPE}

HEAD = """<!-- =====================================================================
     АНО «Дирижабль» — главная страница одним блоком для Craftum.
     Вставлять в блок «HTML-код» («+» → вкладка «Другое» → «HTML-код»).

     Файл собран скриптом tools/make_rawhtml.py из самой сборки сайта:
     разметка — секция <main> из index.html, стили — assets/css/knit.css,
     поведение — assets/js/app.js. Руками не править, правки делать
     в исходниках и пересобирать.

     Весь CSS заскоуплен под .dzb, поэтому стили конструктора не
     затрагиваются и не затрагивают нас. Картинки и ссылки — абсолютные,
     на %(base)s

     Фрагмент намеренно без <!doctype>, <html>, <head> и <body>:
     Craftum вставляет его внутрь своей страницы.
     ===================================================================== -->
<section class="dzb" id="dzb">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Comfortaa:wght@500;700&amp;family=Nunito:wght@400;600;700;800&amp;display=swap">
<style>
""" % {"base": BASE}

BOOT = """
<script>
/* app.js рассчитан на обычную страницу и запускается сам.
   Внутри блока разметка может появиться уже после загрузки документа —
   тогда boot() отработает сразу, это предусмотрено в самом app.js.
   Защита от повторной вставки блока: второй раз не инициализируем. */
(function () {
  var root = document.getElementById("dzb");
  if (!root || root.getAttribute("data-dzb-ready") === "1") { return; }
  root.setAttribute("data-dzb-ready", "1");
%(app)s
})();
</script>
</section>
"""


def main():
    index = open(os.path.join(REPO, "index.html"), encoding="utf-8").read()
    knit = open(os.path.join(REPO, "assets/css/knit.css"), encoding="utf-8").read()
    app = open(os.path.join(REPO, "assets/js/app.js"), encoding="utf-8").read()

    m = re.search(r"<main[^>]*>(.*?)</main>", index, re.S)
    if not m:
        raise SystemExit("в index.html не найдена секция <main> — сначала "
                         "запустите python3 tools/build.py")
    body = absolutize_html(m.group(1))

    css = absolutize_css(scope_css(knit))

    html = (HEAD
            + GUARD_RESET
            + "\n/* --- assets/css/knit.css, заскоуплен под .dzb --- */\n"
            + css
            + GUARD_BTN
            + "</style>\n"
            + body
            + BOOT % {"app": app})

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)

    print("записан %s — %.1f КБ" % (OUT, len(html.encode("utf-8")) / 1024))


if __name__ == "__main__":
    main()
