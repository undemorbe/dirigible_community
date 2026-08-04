/* АНО «Дирижабль» — общий поведенческий слой сайта.
   Без зависимостей. Всё опционально: если блока нет на странице, модуль молчит. */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ------------------------------------------------------- мобильное меню */
  function initNav() {
    var toggle = document.querySelector('[data-nav-toggle]');
    var nav = document.getElementById('site-nav');
    var backdrop = document.querySelector('[data-nav-backdrop]');
    if (!toggle || !nav) return;

    var lastFocused = null;

    function open() {
      lastFocused = document.activeElement;
      nav.classList.add('is-open');
      if (backdrop) backdrop.classList.add('is-open');
      toggle.setAttribute('aria-expanded', 'true');
      document.body.classList.add('is-locked');
      var first = nav.querySelector('a, button');
      if (first) first.focus({ preventScroll: true });
    }

    function close() {
      nav.classList.remove('is-open');
      if (backdrop) backdrop.classList.remove('is-open');
      toggle.setAttribute('aria-expanded', 'false');
      document.body.classList.remove('is-locked');
      if (lastFocused && document.contains(lastFocused)) lastFocused.focus({ preventScroll: true });
    }

    toggle.addEventListener('click', function () {
      if (toggle.getAttribute('aria-expanded') === 'true') close(); else open();
    });

    if (backdrop) backdrop.addEventListener('click', close);

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') close();
    });

    // удержание фокуса внутри панели, пока она открыта
    nav.addEventListener('keydown', function (e) {
      if (e.key !== 'Tab' || toggle.getAttribute('aria-expanded') !== 'true') return;
      var items = nav.querySelectorAll('a[href], button:not([disabled])');
      if (!items.length) return;
      var first = items[0], last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); toggle.focus(); }
    });

    // переход в десктопный режим — сбрасываем состояние
    var desktop = window.matchMedia('(min-width: 1024px)');
    var onChange = function (e) { if (e.matches) close(); };
    if (desktop.addEventListener) desktop.addEventListener('change', onChange);
    else if (desktop.addListener) desktop.addListener(onChange);
  }

  /* ------------------------------------------------------------- карусели */
  function initCarousels(root) {
    var list = (root || document).querySelectorAll('[data-carousel]');
    Array.prototype.forEach.call(list, function (carousel) {
      var track = carousel.querySelector('[data-carousel-track]');
      if (!track) return;
      var prev = carousel.querySelector('[data-carousel-prev]');
      var next = carousel.querySelector('[data-carousel-next]');
      var dotsBox = carousel.querySelector('[data-carousel-dots]');
      var slides = Array.prototype.slice.call(track.children);
      if (slides.length < 2) {
        var nav = carousel.querySelector('.carousel__nav');
        if (nav) nav.hidden = true;
        return;
      }

      var dots = [];
      if (dotsBox) {
        slides.forEach(function (slide, i) {
          var dot = document.createElement('button');
          dot.type = 'button';
          dot.className = 'carousel__dot';
          dot.setAttribute('aria-label', 'Слайд ' + (i + 1) + ' из ' + slides.length);
          dot.addEventListener('click', function () { scrollToIndex(i); });
          dotsBox.appendChild(dot);
          dots.push(dot);
        });
      }

      // Позиция слайда считается через getBoundingClientRect относительно трека:
      // offsetLeft отсчитывается от offsetParent, которым трек не является,
      // и даёт неверные координаты.
      function slideOffset(s) {
        return s.getBoundingClientRect().left - track.getBoundingClientRect().left + track.scrollLeft;
      }

      function currentIndex() {
        var center = track.scrollLeft + track.clientWidth / 2;
        var best = 0, bestDist = Infinity;
        slides.forEach(function (s, i) {
          var d = Math.abs(slideOffset(s) + s.offsetWidth / 2 - center);
          if (d < bestDist) { bestDist = d; best = i; }
        });
        return best;
      }

      function scrollToIndex(i) {
        var s = slides[Math.max(0, Math.min(slides.length - 1, i))];
        track.scrollTo({
          left: slideOffset(s) - (track.clientWidth - s.offsetWidth) / 2,
          behavior: reduceMotion ? 'auto' : 'smooth'
        });
      }

      function sync() {
        var i = currentIndex();
        dots.forEach(function (d, di) { d.setAttribute('aria-current', di === i ? 'true' : 'false'); });
        if (prev) prev.disabled = track.scrollLeft <= 2;
        if (next) next.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 2;
      }

      if (prev) prev.addEventListener('click', function () { scrollToIndex(currentIndex() - 1); });
      if (next) next.addEventListener('click', function () { scrollToIndex(currentIndex() + 1); });

      var ticking = false;
      track.addEventListener('scroll', function () {
        if (ticking) return;
        ticking = true;
        window.requestAnimationFrame(function () { sync(); ticking = false; });
      }, { passive: true });

      window.addEventListener('resize', sync, { passive: true });
      sync();
    });
  }

  /* ------------------------------------------------- появление при скролле */
  function initReveal(root) {
    var items = (root || document).querySelectorAll('.reveal');
    if (!items.length) return;
    if (reduceMotion || !('IntersectionObserver' in window)) {
      Array.prototype.forEach.call(items, function (el) { el.classList.add('is-visible'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        io.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    Array.prototype.forEach.call(items, function (el) { io.observe(el); });

    // Страховка: контент не должен остаться невидимым, если наблюдатель почему-то
    // не сработал (фоновая вкладка, приостановленный рендеринг, ошибка в браузере).
    window.setTimeout(function () {
      Array.prototype.forEach.call(items, function (el) {
        if (!el.classList.contains('is-visible')) {
          el.classList.add('is-visible');
          io.unobserve(el);
        }
      });
    }, 3000);
  }

  /* --------------------------- виджет пожертвований: запасной вариант */
  function initDonateFallback() {
    var box = document.querySelector('[data-donate-widget]');
    var fallback = document.querySelector('[data-donate-fallback]');
    if (!box || !fallback) return;

    var mount = box.querySelector('mixplat-form');
    var loading = box.querySelector('[data-donate-loading]');

    // Точки монтирования нет — идентификаторы не заданы при сборке.
    // Запасной блок уже показан разметкой, ждать нечего.
    if (!mount) return;

    function rendered() {
      // Виджет дорисовывает содержимое внутрь <mixplat-form>.
      return mount.children.length > 0 || mount.shadowRoot ||
             box.querySelector('iframe, form');
    }

    // Тема виджета: свои стили внутрь shadow DOM. Обычный CSS страницы
    // сквозь границу shadow DOM не проходит, а вот <link> внутри shadowRoot
    // работает. CSS-переменные сайта наследуются туда сами.
    function applyTheme() {
      var href = box.getAttribute('data-donate-style');
      var root = mount.shadowRoot;
      if (!href || !root || root.querySelector('link[data-donate-theme]')) return;
      var link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = href;
      link.setAttribute('data-donate-theme', '');
      root.appendChild(link);
    }

    function settle() {
      if (loading) loading.hidden = true;
      box.setAttribute('data-state', 'ready');
      applyTheme();
    }

    // Виджет donation.ru внешний: если он не отрисовался за 6 с
    // (нет сети, блокировщик, офлайн-просмотр) — показываем реквизиты.
    var waited = 0;
    var timer = window.setInterval(function () {
      waited += 400;
      if (rendered()) {
        window.clearInterval(timer);
        settle();
      } else if (waited >= 6000) {
        window.clearInterval(timer);
        if (loading) loading.hidden = true;
        fallback.hidden = false;
        box.setAttribute('data-state', 'fallback');
      }
    }, 400);
  }

  /* ----------------------------------------- активный пункт навигации */
  function markCurrentNav() {
    var here = location.pathname.split('/').pop() || 'index.html';
    var links = document.querySelectorAll('.nav__link, .footer__list a');
    Array.prototype.forEach.call(links, function (a) {
      var href = (a.getAttribute('href') || '').split('/').pop().split('#')[0];
      if (href && href === here) a.setAttribute('aria-current', 'page');
    });
  }

  /* ------------------------------------------------------------- запуск */
  function boot() {
    initNav();
    initCarousels();
    initReveal();
    initDonateFallback();
    markCurrentNav();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();

  // Публичное API — используется articles.js для доинициализации новых карточек.
  window.Dirigible = { initCarousels: initCarousels, initReveal: initReveal, reduceMotion: reduceMotion };
})();
