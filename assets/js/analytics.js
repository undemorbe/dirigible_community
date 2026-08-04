/* Аналитика: Яндекс.Метрика и Top.Mail.Ru.
 *
 * Идентификаторы приходят из window.ANALYTICS_CONFIG — его вставляет
 * tools/build.py из переменных окружения (на GitHub — из секретов).
 * В репозитории их нет намеренно: иначе форк или локальная сборка начнут
 * слать хиты в боевую статистику организации и писать сессии в вебвизор.
 *
 * Если конфига нет или хост локальный — работает заглушка: интерфейс тот же,
 * события пишутся в console.debug, наружу ничего не уходит.
 */
(function () {
  'use strict';

  var cfg = window.ANALYTICS_CONFIG || {};
  var host = location.hostname;

  var isLocal = !host ||
    host === 'localhost' ||
    host === '::1' ||
    /^127\./.test(host) ||
    /^192\.168\./.test(host) ||
    /^10\./.test(host) ||
    /\.local$/.test(host) ||
    location.protocol === 'file:';

  // ?analytics=force — принудительно включить счётчики на локальном хосте.
  // Нужно, чтобы проверить интеграцию, не выкладывая сайт. Проверять только
  // с тестовыми номерами счётчиков, иначе хит уйдёт в боевую статистику.
  var forced = /[?&]analytics=force\b/.test(location.search);

  var enabled = (!isLocal || forced) && !!(cfg.yandexMetrika || cfg.topMailRu);

  var queue = [];

  function track(event, params) {
    queue.push({ event: event, params: params || null });
    if (!enabled && window.console && console.debug) {
      console.debug('[analytics:stub]', event, params || '');
    }
  }

  /* --------------------------------------------------------- Яндекс.Метрика */
  function loadYandexMetrika(id) {
    /* eslint-disable */
    (function (m, e, t, r, i, k, a) {
      m[i] = m[i] || function () { (m[i].a = m[i].a || []).push(arguments); };
      m[i].l = 1 * new Date();
      for (var j = 0; j < e.scripts.length; j++) {
        if (e.scripts[j].src === r) return;
      }
      k = e.createElement(t); a = e.getElementsByTagName(t)[0];
      k.async = 1; k.src = r; a.parentNode.insertBefore(k, a);
    })(window, document, 'script', 'https://mc.yandex.ru/metrika/tag.js', 'ym');
    /* eslint-enable */

    window.ym(id, 'init', {
      clickmap: true,
      trackLinks: true,
      accurateTrackBounce: true,
      webvisor: true
    });
  }

  /* ---------------------------------------------------------- Top.Mail.Ru */
  function loadTopMailRu(id) {
    var _tmr = window._tmr || (window._tmr = []);
    _tmr.push({ id: String(id), type: 'pageView', start: (new Date()).getTime() });

    (function (d, w, scriptId) {
      if (d.getElementById(scriptId)) return;
      var ts = d.createElement('script');
      ts.type = 'text/javascript';
      ts.async = true;
      ts.id = scriptId;
      ts.src = 'https://top-fwz1.mail.ru/js/code.js';
      var f = function () {
        var s = d.getElementsByTagName('script')[0];
        s.parentNode.insertBefore(ts, s);
      };
      if (w.opera === '[object Opera]') d.addEventListener('DOMContentLoaded', f, false);
      else f();
    })(document, window, 'tmr-code');
  }

  function start() {
    if (!enabled) {
      if (window.console && console.info && (cfg.yandexMetrika || cfg.topMailRu)) {
        console.info('[analytics] локальный хост — боевые счётчики не подключены');
      }
      return;
    }
    // Отложенный запуск, как было в исходной вёрстке: счётчики не должны
    // конкурировать за сеть с контентом страницы.
    window.setTimeout(function () {
      try {
        if (cfg.yandexMetrika) loadYandexMetrika(cfg.yandexMetrika);
        if (cfg.topMailRu) loadTopMailRu(cfg.topMailRu);
      } catch (e) {
        if (window.console) console.error('[analytics]', e);
      }
    }, 1500);
  }

  window.analytics = { track: track, queue: queue, enabled: enabled };

  // Совместимость: ym() должен существовать до загрузки счётчика.
  if (typeof window.ym !== 'function') {
    window.ym = function () {
      (window.ym.a = window.ym.a || []).push(arguments);
      track('ym', Array.prototype.slice.call(arguments));
    };
  }

  if (document.readyState === 'complete') start();
  else window.addEventListener('load', start);

  track('pageview', { path: location.pathname, title: document.title });
})();
