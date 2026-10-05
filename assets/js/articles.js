/* Лента материалов АНО «Дирижабль».
 *
 * Заменяет исходный articles.js из Craftum, который ходил в закрытый
 * бэкенд `/user-website-api/blog/rubrics/<id>/articles/` и в статической
 * выгрузке всегда падал с 404, оставляя пустой список.
 *
 * Источник данных теперь локальный: assets/data/articles.json.
 * Если fetch недоступен (открытие по file://), берём копию данных из
 * инлайнового <script type="application/json" id="articles-data">.
 */
(function () {
  'use strict';

  var MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];

  function formatDate(iso) {
    var d = new Date(iso);
    if (isNaN(d.getTime())) return '';
    return d.getDate() + ' ' + MONTHS[d.getMonth()] + ' ' + d.getFullYear();
  }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function readInline() {
    var node = document.getElementById('articles-data');
    if (!node) return null;
    try { return JSON.parse(node.textContent); }
    catch (e) { return null; }
  }

  function load(endpoint) {
    var inline = readInline();
    if (!window.fetch || location.protocol === 'file:') {
      return inline ? Promise.resolve(inline)
                    : Promise.reject(new Error('нет fetch и нет инлайновых данных'));
    }
    return fetch(endpoint, { headers: { Accept: 'application/json' } })
      .then(function (res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      })
      .catch(function (err) {
        if (inline) return inline;
        throw err;
      });
  }

  function Feed(root) {
    this.root = root;
    this.endpoint = root.dataset.articlesEndpoint || 'assets/data/articles.json';
    // Пути к картинкам и страницам внутри articles.json относительные.
    // На сайте они разрешаются сами, а в сборке для Craftum лента живёт
    // на чужом домене — там база задаётся через data-articles-base.
    this.base = root.dataset.articlesBase || '';
    // Картинки и страницы там лежат по разным адресам: файлы — в нашем
    // хранилище, страницы — на самом домене и под своими адресами.
    // data-articles-links отдаёт карту «имя файла → адрес страницы».
    try {
      this.links = JSON.parse(root.dataset.articlesLinks || '{}');
    } catch (e) {
      this.links = {};
    }
    this.perPage = parseInt(root.dataset.articlesPerPage, 10) || 6;
    this.rubric = root.dataset.articlesRubric || '';
    this.listEl = root.querySelector('[data-articles-list]');
    this.tagsEl = root.querySelector('[data-articles-tags]');
    this.moreEl = root.querySelector('[data-articles-more]');
    this.statusEl = root.querySelector('[data-articles-status]');
    this.all = [];
    this.tags = [];
    this.activeTag = '';
    this.shown = 0;
  }

  Feed.prototype.status = function (message, isError) {
    if (!this.statusEl) return;
    if (!message) { this.statusEl.hidden = true; this.statusEl.textContent = ''; return; }
    this.statusEl.hidden = false;
    this.statusEl.textContent = message;
    this.statusEl.setAttribute('role', isError ? 'alert' : 'status');
  };

  Feed.prototype.filtered = function () {
    var tag = this.activeTag;
    if (!tag) return this.all;
    return this.all.filter(function (a) { return (a.tags || []).indexOf(tag) !== -1; });
  };

  Feed.prototype.renderTags = function () {
    if (!this.tagsEl) return;
    this.tagsEl.innerHTML = '';
    var self = this;
    var options = [{ id: '', name: 'Все' }].concat(this.tags);

    options.forEach(function (tag) {
      var btn = el('button', 'tag', tag.name);
      btn.type = 'button';
      btn.setAttribute('aria-pressed', String(tag.id === self.activeTag));
      btn.addEventListener('click', function () {
        if (self.activeTag === tag.id) return;
        self.activeTag = tag.id;
        self.shown = 0;
        self.listEl.innerHTML = '';
        self.renderTags();
        self.renderPage();
      });
      self.tagsEl.appendChild(btn);
    });
  };

  // Относительный путь из articles.json + база ленты. Абсолютные адреса,
  // якоря, mailto: и tel: остаются как есть.
  Feed.prototype.resolve = function (path) {
    if (!path) return path;
    if (/^(https?:|\/\/|data:|#|mailto:|tel:)/i.test(path)) return path;
    var cut = path.indexOf('#');
    var file = cut < 0 ? path : path.slice(0, cut);
    var hash = cut < 0 ? '' : path.slice(cut);
    if (this.links[file]) return this.links[file] + hash;
    if (!this.base) return path;
    return this.base + path.replace(/^\//, '');
  };

  Feed.prototype.card = function (article) {
    var isExternal = /^https?:/i.test(article.url || '');
    var node = el(article.url ? 'a' : 'article', 'card article-card' + (article.url ? ' card--link' : '') + ' reveal');

    if (article.url) {
      node.href = this.resolve(article.url);
      if (isExternal) { node.target = '_blank'; node.rel = 'noopener noreferrer'; }
    }

    if (article.image) {
      var img = el('img', 'article-card__media');
      img.src = this.resolve(article.image);
      img.alt = article.imageAlt || '';
      img.loading = 'lazy';
      img.decoding = 'async';
      if (article.imageWidth) img.width = article.imageWidth;
      if (article.imageHeight) img.height = article.imageHeight;
      node.appendChild(img);
    }

    var body = el('div', 'article-card__body');
    // dateText — человекочитаемая подпись, когда точная дата в источнике не указана
    var when = article.dateText || (article.date ? formatDate(article.date) : '');
    if (when) body.appendChild(el('span', 'article-card__date', when));
    body.appendChild(el('h3', 'article-card__title', article.title || 'Без названия'));
    if (article.excerpt) body.appendChild(el('p', 'article-card__text', article.excerpt));

    if ((article.tags || []).length) {
      var wrap = el('div', 'article-card__tags');
      var names = this.tagNames;
      article.tags.forEach(function (id) {
        wrap.appendChild(el('span', 'chip', names[id] || id));
      });
      body.appendChild(wrap);
    }

    if (isExternal) {
      var hint = el('span', 'visually-hidden', '(откроется в новой вкладке)');
      body.appendChild(hint);
    }

    node.appendChild(body);
    return node;
  };

  Feed.prototype.renderPage = function () {
    var items = this.filtered();

    if (!items.length) {
      this.status('По этому фильтру материалов пока нет. Выберите другой раздел.');
      if (this.moreEl) this.moreEl.hidden = true;
      return;
    }
    this.status('');

    var slice = items.slice(this.shown, this.shown + this.perPage);
    var frag = document.createDocumentFragment();
    for (var i = 0; i < slice.length; i++) frag.appendChild(this.card(slice[i]));
    this.listEl.appendChild(frag);
    this.shown += slice.length;

    if (this.moreEl) {
      var left = items.length - this.shown;
      this.moreEl.hidden = left <= 0;
      this.moreEl.textContent = left > 0 ? 'Показать ещё (' + left + ')' : 'Показать ещё';
    }

    if (window.Dirigible) window.Dirigible.initReveal(this.listEl);
  };

  Feed.prototype.init = function () {
    var self = this;
    if (!this.listEl) return;

    this.status('Загружаем материалы…');

    load(this.endpoint).then(function (data) {
      var articles = (data && data.articles) || [];
      var tags = (data && data.tags) || [];

      self.tagNames = {};
      tags.forEach(function (t) { self.tagNames[t.id] = t.name; });

      if (self.rubric) {
        var allowed = self.rubric.split(/\s*,\s*/).filter(Boolean);
        articles = articles.filter(function (a) {
          return (a.tags || []).some(function (t) { return allowed.indexOf(t) !== -1; });
        });
      }

      // сортировка по дате; материалы без даты уходят в конец, сохраняя исходный порядок
      articles.sort(function (a, b) {
        var ta = a.date ? new Date(a.date).getTime() : -Infinity;
        var tb = b.date ? new Date(b.date).getTime() : -Infinity;
        return tb - ta;
      });
      self.all = articles;

      // показываем только те теги, которые реально встречаются
      var used = {};
      articles.forEach(function (a) { (a.tags || []).forEach(function (t) { used[t] = true; }); });
      self.tags = tags.filter(function (t) { return used[t.id]; });

      self.renderTags();
      self.renderPage();
    }).catch(function (err) {
      self.status('Не удалось загрузить ленту материалов: ' + err.message +
                  '. Обновите страницу или откройте сайт через локальный сервер.', true);
      if (self.moreEl) self.moreEl.hidden = true;
      if (window.console) console.error('[articles]', err);
    });

    if (this.moreEl) {
      this.moreEl.addEventListener('click', function () { self.renderPage(); });
    }
  };

  function boot() {
    var roots = document.querySelectorAll('[data-articles]');
    Array.prototype.forEach.call(roots, function (root) {
      // Повторный запуск возможен: в сборке для Craftum сквозной код
      // выполняется раньше, чем на странице появляется блок с лентой,
      // поэтому boot() зовут ещё раз. Второй Feed на том же контейнере
      // продублировал бы карточки.
      if (root.getAttribute('data-articles-ready') === '1') return;
      root.setAttribute('data-articles-ready', '1');
      new Feed(root).init();
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();

  // Публичное API — как window.Dirigible у app.js: позволяет запустить
  // ленту для разметки, появившейся после загрузки страницы.
  window.DirigibleArticles = { boot: boot };
})();
