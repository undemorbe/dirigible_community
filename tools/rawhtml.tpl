<!-- =====================================================================
     АНО «Дирижабль» — тестовая страница в дизайне «Вязаное полотно».
     Самодостаточный фрагмент для блока «HTML-код» в Craftum
     («+» под блоком → вкладка «Другое» → «HTML-код» → «Настроить»).

     Что внутри: разметка + <style> + <script>. Внешних файлов нет:
     SVG-тайлы вязки встроены как data: URI, фотографии берутся
     с CDN организации (тот же 274418.selcdn.ru, что и в Craftum).

     Фрагмент намеренно без <!doctype>, <html>, <head> и <body>:
     Craftum вставляет его внутрь своей страницы.

     Все классы и переменные начинаются с dzb- / --dzb-, вся стилистика
     ограничена селектором .dzb — стили Craftum не затрагиваются
     и не затрагивают нас.
     ===================================================================== -->
<section class="dzb" id="dzb" aria-labelledby="dzb-h1">
<style>
@import url("https://fonts.googleapis.com/css2?family=Comfortaa:wght@500;700&family=Nunito:wght@400;600;700;800&display=swap");

/* ------------------------------------------------------------- токены */
.dzb {
  /* шерсть — фоны */
  --dzb-wool-50:  #FBF6EC;
  --dzb-wool-100: #F4EADA;
  --dzb-wool-200: #EADCC6;
  --dzb-wool-300: #DCC8AA;
  --dzb-wool-400: #C7AE8C;
  /* чернила — текст */
  --dzb-ink:      #33291F;
  --dzb-ink-soft: #6B5A47;
  --dzb-ink-mute: #927E67;
  /* пряжа — акценты (фирменные цвета логотипа-дирижабля) */
  --dzb-blue:       #1E93CC;
  --dzb-blue-deep:  #146189;
  --dzb-orange:     #EE7B18;
  --dzb-orange-deep:#C25E06;
  --dzb-mustard:    #D9A441;
  --dzb-sage:       #6E8F63;
  /* нить-обводка */
  --dzb-thread: rgba(51, 41, 31, .22);
  /* геометрия */
  --dzb-r-sm: 10px;
  --dzb-r-md: 18px;
  --dzb-r-lg: 28px;
  --dzb-r-pill: 999px;
  /* тени — тёплый коричневый, без чёрного */
  --dzb-shadow-1: 0 2px 0 rgba(199, 174, 140, .55),
                  0 6px 18px -8px rgba(51, 41, 31, .30);
  --dzb-shadow-2: 0 3px 0 rgba(199, 174, 140, .65),
                  0 16px 34px -16px rgba(51, 41, 31, .38);
  /* ритм */
  --dzb-gap: clamp(1rem, 3vw, 1.75rem);
  --dzb-pad-x: clamp(1rem, 5vw, 2.5rem);
  --dzb-section-y: clamp(2.5rem, 7vw, 5rem);
  --dzb-maxw: 1140px;
  --dzb-ease: cubic-bezier(.34, .12, .2, 1);
  /* текстуры — встроены data: URI, внешних файлов нет */
  --dzb-tex-stockinette: url("__STOCKINETTE__");
  --dzb-tex-seed: url("__SEED__");
  --dzb-tex-cable: url("__CABLE__");

  /* сам блок */
  position: relative;
  isolation: isolate;
  margin: 0;
  padding: 0;
  background-color: var(--dzb-wool-50);
  background-image: var(--dzb-tex-stockinette);
  background-size: 44px 33px;
  color: var(--dzb-ink);
  font-family: "Nunito", "Segoe UI", "Helvetica Neue", system-ui, -apple-system, sans-serif;
  font-size: clamp(1rem, .96rem + .25vw, 1.0625rem);
  line-height: 1.65;
  font-weight: 400;
  text-align: left;
  overflow-x: hidden;
  -webkit-font-smoothing: antialiased;
}

/* --------------------------------------------- локальный сброс */
/* Сброс только внутри .dzb — блоки Craftum он не трогает.
   Селекторы завёрнуты в :where(), у которого нулевая специфичность:
   иначе `.dzb p` (0,1,1) побеждал бы `.dzb-lead` (0,1,0) и собственные
   стили компонентов не применялись бы.
   Сбрасывать приходится много: на странице конструктора висят свои
   правила на p/h2/img/button, и они бьют наследование от .dzb. */
.dzb *, .dzb *::before, .dzb *::after { box-sizing: border-box; }

.dzb :where(h1, h2, h3, h4, h5, h6, p, figure, blockquote, dl, dd, ul, ol, li,
            fieldset, form) { margin: 0; }
.dzb :where(ul, ol) { padding: 0; list-style: none; }

.dzb :where(h1, h2, h3, h4, h5, h6, p, li, dt, dd, span, a, b, strong, em, i,
            small, figcaption, button, label, time) {
  font-family: inherit;
  font-size: inherit;
  font-weight: inherit;
  font-style: inherit;
  line-height: inherit;
  letter-spacing: normal;
  text-transform: none;
  text-align: inherit;
  color: inherit;
}
.dzb :where(code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: .9em;
  color: inherit;
}

.dzb :where(img, svg, video) {
  display: block;
  max-width: 100%;
  height: auto;
  border: 0;
  border-radius: 0;
  box-shadow: none;
}
.dzb img { background-color: var(--dzb-wool-100); }

.dzb :where(button) {
  margin: 0;
  padding: 0;
  background: transparent;
  border: 0;
  border-radius: 0;
  box-shadow: none;
  text-transform: none;
  cursor: pointer;
}

.dzb a { color: var(--dzb-blue-deep); text-decoration-thickness: 1.5px;
         text-underline-offset: .22em; transition: color .2s var(--dzb-ease); }
.dzb a:hover { color: var(--dzb-orange-deep); }
.dzb :focus-visible {
  outline: 3px dashed var(--dzb-orange);
  outline-offset: 3px;
  border-radius: var(--dzb-r-sm);
}
.dzb ::selection { background: rgba(217, 164, 65, .45); }

/* ---------------------------------------------------------- раскладка */
.dzb-container {
  width: 100%;
  max-width: var(--dzb-maxw);
  margin-inline: auto;
  padding-inline: var(--dzb-pad-x);
}
.dzb-section { padding-block: var(--dzb-section-y); position: relative; }
.dzb-section--tight { padding-block: clamp(1.5rem, 4vw, 2.5rem); }

/* «изнаночная» секция — жемчужная вязка */
.dzb-section--purl {
  background-color: var(--dzb-wool-100);
  background-image: var(--dzb-tex-seed);
  background-size: 26px 26px;
  border-block: 2px solid var(--dzb-thread);
}
.dzb-section--wool {
  background-color: var(--dzb-wool-200);
  background-image: var(--dzb-tex-seed);
  background-size: 26px 26px;
}

/* --------------------------------------------------------- типографика */
.dzb h1, .dzb h2, .dzb h3 {
  font-family: "Comfortaa", "Trebuchet MS", system-ui, sans-serif;
  font-weight: 700;
  line-height: 1.18;
  letter-spacing: -.01em;
  color: var(--dzb-ink);
}
.dzb h1 { font-size: clamp(2rem, 1.3rem + 3.4vw, 3.5rem); }
.dzb h2 { font-size: clamp(1.5rem, 1.1rem + 1.9vw, 2.25rem); }
.dzb h3 { font-size: clamp(1.125rem, 1rem + .6vw, 1.375rem); }

.dzb-eyebrow {
  font-family: "Comfortaa", "Trebuchet MS", sans-serif;
  font-size: .8125rem;
  font-weight: 700;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--dzb-blue-deep);
  margin-bottom: .6rem;
}
.dzb-lead {
  font-size: clamp(1.0625rem, 1rem + .4vw, 1.25rem);
  color: var(--dzb-ink-soft);
  line-height: 1.6;
}
.dzb-section-head { margin-bottom: clamp(1.5rem, 4vw, 2.5rem); }
.dzb-section-head--center { text-align: center; }
.dzb-text-center { text-align: center; }
.dzb-center-x { margin-inline: auto; }

/* подчёркивание-стежок.
   Сделано фоном, а не ::after: псевдоэлемент растягивался на всю
   ширину строчного бокса, когда заголовок переносился. */
.dzb-stitch {
  background-image: linear-gradient(transparent 62%, rgba(217, 164, 65, .55) 62%);
  background-repeat: no-repeat;
  -webkit-box-decoration-break: clone;
  box-decoration-break: clone;
  padding-inline: .08em;
}

/* --------------------------------------------------------------- кнопки */
.dzb-btn {
  display: inline-flex;
  align-items: center;
  gap: .55rem;
  padding: .8rem 1.5rem;
  border: 2px solid var(--dzb-ink);
  border-radius: var(--dzb-r-pill);
  background: var(--dzb-wool-50);
  color: var(--dzb-ink);
  font-family: "Comfortaa", "Trebuchet MS", sans-serif;
  font-weight: 700;
  font-size: 1rem;
  line-height: 1.2;
  text-decoration: none;
  box-shadow: var(--dzb-shadow-1);
  transition: transform .18s var(--dzb-ease), box-shadow .18s var(--dzb-ease),
              background-color .18s var(--dzb-ease);
}
.dzb-btn:hover { transform: translateY(-2px); box-shadow: var(--dzb-shadow-2); }
.dzb-btn:active { transform: translateY(1px); box-shadow: var(--dzb-shadow-1); }
.dzb-btn--lg { padding: .95rem 1.85rem; font-size: 1.0625rem; }
.dzb-btn--orange {
  background: var(--dzb-orange);
  border-color: var(--dzb-orange-deep);
  color: #fff;
}
.dzb-btn--orange:hover { background: var(--dzb-orange-deep); color: #fff; }
.dzb-btn--blue {
  background: var(--dzb-blue);
  border-color: var(--dzb-blue-deep);
  color: #fff;
}
.dzb-btn--blue:hover { background: var(--dzb-blue-deep); color: #fff; }
.dzb-btn--ghost { background: transparent; }
.dzb-btn--ghost:hover { background: var(--dzb-wool-100); color: var(--dzb-ink); }
.dzb-btn__icon { width: 20px; height: 20px; flex: none; }

.dzb-cluster {
  display: flex;
  flex-wrap: wrap;
  gap: .85rem;
  align-items: center;
}
.dzb-cluster--center { justify-content: center; }

/* ------------------------------------------------------------------ hero */
.dzb-hero { padding-block: clamp(2.5rem, 7vw, 5rem) var(--dzb-section-y); }
.dzb-hero__grid {
  display: grid;
  gap: clamp(1.75rem, 5vw, 3.5rem);
  align-items: center;
}
.dzb-hero__actions { margin-top: 1.75rem; display: flex; flex-wrap: wrap; gap: .85rem; }

/* рамка-полотно под фотографию */
.dzb-frame {
  position: relative;
  padding: .7rem;
  background: var(--dzb-wool-100);
  background-image: var(--dzb-tex-seed);
  background-size: 26px 26px;
  border: 2px solid var(--dzb-thread);
  border-radius: var(--dzb-r-lg);
  box-shadow: var(--dzb-shadow-2);
  transform: rotate(-1.2deg);
}
.dzb-frame > img {
  border-radius: calc(var(--dzb-r-lg) - .5rem);
  width: 100%;
  aspect-ratio: 4 / 3;
  object-fit: cover;
  object-position: center 30%;
}

/* декоративный клубок.
   Вставлен инлайновым SVG, а не через url(): в подключённом файлом SVG
   currentColor не наследуется и покрасить его из CSS нельзя. */
.dzb-pompom {
  position: absolute;
  width: clamp(54px, 9vw, 86px);
  color: var(--dzb-mustard);
  opacity: .9;
  pointer-events: none;
  z-index: 2;
}
.dzb-pompom--tr { top: -22px; right: -14px; transform: rotate(14deg); }
.dzb-pompom--bl { bottom: -24px; left: -16px; transform: rotate(-18deg); }

/* ------------------------------------------------- косичка-разделитель */
.dzb-cable {
  height: 44px;
  background-image: var(--dzb-tex-cable);
  background-size: auto 44px;
  background-repeat: repeat-x;
  background-position: center;
  opacity: .85;
  margin-block: clamp(.5rem, 2vw, 1.25rem);
}

/* ---------------------------------------------------------------- сетки */
.dzb-grid { display: grid; gap: var(--dzb-gap); }
@media (min-width: 680px) {
  .dzb-grid--3 { grid-template-columns: repeat(2, 1fr); }
}
@media (min-width: 980px) {
  .dzb-grid--3 { grid-template-columns: repeat(3, 1fr); }
  .dzb-hero__grid { grid-template-columns: 1.05fr .95fr; }
}

/* ------------------------------------------------------- карточка-заплатка */
.dzb-card {
  position: relative;
  padding: clamp(1.4rem, 3.5vw, 2rem);
  background: var(--dzb-wool-50);
  border: 2px dashed var(--dzb-thread);
  border-radius: var(--dzb-r-lg);
  box-shadow: var(--dzb-shadow-1);
  transition: transform .22s var(--dzb-ease), box-shadow .22s var(--dzb-ease);
}
.dzb-card:hover { transform: translateY(-4px); box-shadow: var(--dzb-shadow-2); }
.dzb-card:nth-child(2) { transform: rotate(.6deg); }
.dzb-card:nth-child(2):hover { transform: rotate(.6deg) translateY(-4px); }
.dzb-card:nth-child(3) { transform: rotate(-.5deg); }
.dzb-card:nth-child(3):hover { transform: rotate(-.5deg) translateY(-4px); }
.dzb-card__num {
  display: inline-grid;
  place-items: center;
  width: 2.6rem;
  height: 2.6rem;
  margin-bottom: .9rem;
  border-radius: var(--dzb-r-pill);
  background: var(--dzb-blue);
  color: #fff;
  font-family: "Comfortaa", "Trebuchet MS", sans-serif;
  font-weight: 700;
  font-size: 1.15rem;
  box-shadow: inset 0 -2px 0 rgba(20, 97, 137, .6);
}
.dzb-card__title { margin-bottom: .55rem; }
.dzb-card__text { color: var(--dzb-ink-soft); }

/* -------------------------------------------------------- команда: карусель */
.dzb-carousel { position: relative; }
.dzb-track {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: min(78%, 240px);
  gap: var(--dzb-gap);
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  scroll-behavior: smooth;
  padding-block: .5rem 1.25rem;
  padding-inline: 2px;
  /* полоса прокрутки в тон полотну */
  scrollbar-color: var(--dzb-wool-400) transparent;
  scrollbar-width: thin;
}
.dzb-track::-webkit-scrollbar { height: 8px; }
.dzb-track::-webkit-scrollbar-thumb {
  background: var(--dzb-wool-400);
  border-radius: var(--dzb-r-pill);
}
@media (min-width: 680px)  { .dzb-track { grid-auto-columns: min(42%, 260px); } }
@media (min-width: 980px)  { .dzb-track { grid-auto-columns: 1fr; grid-auto-flow: row;
                                          grid-template-columns: repeat(4, 1fr);
                                          overflow: visible; } }
.dzb-person { scroll-snap-align: start; }
.dzb-person__photo {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  border-radius: var(--dzb-r-md);
  border: 2px solid var(--dzb-thread);
  box-shadow: var(--dzb-shadow-1);
  margin-bottom: .75rem;
}
.dzb-person figcaption { display: grid; gap: .2rem; }
.dzb-person__name {
  font-family: "Comfortaa", "Trebuchet MS", sans-serif;
  font-weight: 700;
  font-size: 1.0625rem;
}
.dzb-person__role { font-size: .9375rem; color: var(--dzb-ink-soft); line-height: 1.45; }

.dzb-nav-btns { display: flex; gap: .6rem; justify-content: center; margin-top: .5rem; }
@media (min-width: 980px) { .dzb-nav-btns { display: none; } }
.dzb-arrow {
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  border: 2px solid var(--dzb-ink);
  border-radius: var(--dzb-r-pill);
  background: var(--dzb-wool-50);
  box-shadow: var(--dzb-shadow-1);
  transition: transform .18s var(--dzb-ease), background-color .18s var(--dzb-ease);
}
.dzb-arrow:hover { background: var(--dzb-wool-200); transform: translateY(-2px); }
.dzb-arrow[disabled] { opacity: .35; cursor: default; transform: none; }
.dzb-arrow svg { width: 22px; height: 22px; }

/* ------------------------------------------------------------- аккордеон */
.dzb-acc { display: grid; gap: .75rem; max-width: 760px; margin-inline: auto; }
.dzb-acc__item {
  background: var(--dzb-wool-50);
  border: 2px solid var(--dzb-thread);
  border-radius: var(--dzb-r-md);
  box-shadow: var(--dzb-shadow-1);
  overflow: hidden;
}
.dzb-acc__btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  width: 100%;
  padding: 1rem 1.25rem;
  border: 0;
  background: transparent;
  font-family: "Comfortaa", "Trebuchet MS", sans-serif;
  font-weight: 700;
  font-size: 1.0625rem;
  text-align: left;
}
.dzb-acc__btn::after {
  content: "";
  flex: none;
  width: 12px;
  height: 12px;
  border-right: 2.5px solid var(--dzb-blue-deep);
  border-bottom: 2.5px solid var(--dzb-blue-deep);
  transform: rotate(45deg) translateY(-2px);
  transition: transform .22s var(--dzb-ease);
}
.dzb-acc__btn[aria-expanded="true"]::after { transform: rotate(-135deg) translateY(-2px); }
.dzb-acc__panel { padding: 0 1.25rem 1.15rem; color: var(--dzb-ink-soft); }
.dzb-acc__panel[hidden] { display: none; }

/* -------------------------------------------------------- панель проверки */
.dzb-check {
  max-width: 560px;
  margin-inline: auto;
  padding: clamp(1.25rem, 3vw, 1.75rem);
  background: var(--dzb-wool-50);
  border: 2px dashed var(--dzb-thread);
  border-radius: var(--dzb-r-lg);
  box-shadow: var(--dzb-shadow-1);
}
.dzb-check h3 { margin-bottom: .85rem; }
.dzb-check ul { display: grid; gap: .45rem; }
.dzb-check li {
  display: flex;
  align-items: baseline;
  gap: .6rem;
  font-size: .9375rem;
}
.dzb-check b {
  flex: none;
  width: 1.4em;
  font-family: "Comfortaa", "Trebuchet MS", sans-serif;
  font-weight: 700;
  color: var(--dzb-ink-mute);
}
.dzb-check li[data-ok="1"] b { color: var(--dzb-sage); }
.dzb-check li[data-ok="0"] b { color: #C0392B; }

/* ----------------------------------------------------------- реквизиты */
.dzb-facts {
  display: grid;
  gap: .6rem 1.5rem;
  max-width: 760px;
  margin-inline: auto;
  text-align: left;
}
@media (min-width: 680px) { .dzb-facts { grid-template-columns: auto 1fr; } }
.dzb-facts dt {
  font-family: "Comfortaa", "Trebuchet MS", sans-serif;
  font-weight: 700;
  font-size: .9375rem;
  color: var(--dzb-ink-mute);
}
.dzb-facts dd { font-size: .9375rem; }

/* --------------------------------------------------------------- фестоны */
.dzb-scallop { position: relative; }
.dzb-scallop::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: -11px;
  height: 22px;
  background-image: radial-gradient(circle at 11px 0, var(--dzb-wool-100) 11px,
                                    transparent 11.5px);
  background-size: 22px 22px;
  background-repeat: repeat-x;
}

/* ---------------------------------------------------------------- motion */
.dzb-reveal {
  opacity: 0;
  transform: translateY(18px);
  transition: opacity .5s var(--dzb-ease), transform .5s var(--dzb-ease);
}
.dzb-reveal.dzb-in { opacity: 1; transform: none; }
/* без JS и без IntersectionObserver блок всё равно виден */
.dzb-no-js .dzb-reveal { opacity: 1; transform: none; }

@media (prefers-reduced-motion: reduce) {
  .dzb *, .dzb *::before, .dzb *::after {
    animation-duration: .001ms !important;
    transition-duration: .001ms !important;
  }
  .dzb-reveal { opacity: 1; transform: none; }
  .dzb-track { scroll-behavior: auto; }
}
</style>

<!-- ======================================================== hero -->
<div class="dzb-hero">
  <div class="dzb-container">
    <div class="dzb-hero__grid">
      <div>
        <p class="dzb-eyebrow">Центр развития социальных практик</p>
        <h1 id="dzb-h1">Мы вяжем <span class="dzb-stitch">страховочную сеть</span> для семей в кризисе</h1>
        <p class="dzb-lead" style="margin-top:1rem">Наша миссия — помогать людям строить, укреплять
        и налаживать свою «сеть поддержки» из родных, друзей и помогающих специалистов.</p>
        <div class="dzb-hero__actions">
          <a class="dzb-btn dzb-btn--orange dzb-btn--lg" href="#dzb-cta">
            <svg class="dzb-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8z"/>
            </svg>
            Поддержать нас
          </a>
          <a class="dzb-btn dzb-btn--ghost dzb-btn--lg" href="#dzb-work">Как это работает</a>
        </div>
      </div>
      <div class="dzb-frame">
        <!-- клубки: инлайновый SVG, чтобы красились из CSS -->
        <svg class="dzb-pompom dzb-pompom--tr" viewBox="0 0 100 100" aria-hidden="true">
          <circle cx="50" cy="50" r="34" fill="currentColor" opacity=".95"/>
          <g fill="none" stroke="#FBF6EC" stroke-width="2.4" opacity=".75" stroke-linecap="round">
            <path d="M22 42c10 6 24 8 40 4"/>
            <path d="M18 56c14 6 32 6 48-2"/>
            <path d="M28 68c12 4 26 3 38-4"/>
          </g>
          <path d="M80 62c12 6 10 20 0 26s-22 2-24-8" fill="none" stroke="currentColor"
                stroke-width="5" stroke-linecap="round"/>
        </svg>
        <svg class="dzb-pompom dzb-pompom--bl" viewBox="0 0 100 100" aria-hidden="true"
             style="color:var(--dzb-blue)">
          <circle cx="50" cy="50" r="30" fill="currentColor" opacity=".9"/>
          <g fill="none" stroke="#FBF6EC" stroke-width="2.2" opacity=".7" stroke-linecap="round">
            <path d="M24 46c10 5 22 7 36 3"/>
            <path d="M22 58c13 5 29 5 44-2"/>
          </g>
          <path d="M22 66C8 72 8 86 20 90" fill="none" stroke="currentColor"
                stroke-width="5" stroke-linecap="round"/>
        </svg>
        <img src="__CDN__aa763a1d-d787-43d3-89ae-0395a8158f0e.jpg"
             alt="Вязаные фигурки людей стоят кругом на столе во время сетевой встречи"
             fetchpriority="high" decoding="async">
      </div>
    </div>
  </div>
</div>

<div class="dzb-container"><div class="dzb-cable" role="presentation"></div></div>

<!-- ======================================================== миссия -->
<div class="dzb-section dzb-section--tight">
  <div class="dzb-container">
    <p class="dzb-lead dzb-center-x dzb-text-center dzb-reveal" style="max-width:72ch">
      Мы помогаем людям представить себе хорошее будущее и идти туда, опираясь на свои сильные
      стороны. Собираем их родственников и друзей, учителей, врачей или соцработников, чтобы
      вместе решить реальные проблемы: от прогулов школы до угрозы попадания ребёнка под опеку
      государства.
    </p>
  </div>
</div>

<!-- ======================================================== что делаем -->
<div class="dzb-section dzb-section--purl" id="dzb-work" aria-labelledby="dzb-work-title">
  <div class="dzb-container">
    <div class="dzb-section-head dzb-section-head--center">
      <p class="dzb-eyebrow">Три петли нашей работы</p>
      <h2 id="dzb-work-title">Что мы делаем</h2>
    </div>
    <div class="dzb-grid dzb-grid--3">
      <article class="dzb-card dzb-reveal">
        <span class="dzb-card__num">1</span>
        <h3 class="dzb-card__title">Проводим сетевые встречи</h3>
        <p class="dzb-card__text">Ведём сетевые встречи и похожие форматы по запросу коллег
        в Москве и Подмосковье. Разгружаем специалистов и помогаем взглянуть на сложный
        случай «изнутри круга».</p>
      </article>
      <article class="dzb-card dzb-reveal">
        <span class="dzb-card__num">2</span>
        <h3 class="dzb-card__title">Обучаем специалистов</h3>
        <p class="dzb-card__text">Учим команды в регионах, ведём сообщество в Telegram,
        проводим супервизии, интервизии и мероприятия по обмену опытом.</p>
      </article>
      <article class="dzb-card dzb-reveal">
        <span class="dzb-card__num">3</span>
        <h3 class="dzb-card__title">Внедряем и исследуем</h3>
        <p class="dzb-card__text">Помогаем закрепить технологию в организации и на территории.
        Исследуем результативность, собираем и описываем новые идеи из практики.</p>
      </article>
    </div>
  </div>
</div>

<!-- ======================================================== команда -->
<div class="dzb-section dzb-section--wool" aria-labelledby="dzb-team-title">
  <div class="dzb-container">
    <div class="dzb-section-head dzb-section-head--center">
      <p class="dzb-eyebrow">Кто вяжет эту сеть</p>
      <h2 id="dzb-team-title"><span class="dzb-stitch">Наша команда</span></h2>
    </div>
    <div class="dzb-carousel">
      <div class="dzb-track" id="dzb-track" tabindex="0" role="group"
           aria-label="Команда — прокрутите в сторону">
__PEOPLE__
      </div>
      <div class="dzb-nav-btns">
        <button class="dzb-arrow" type="button" data-dzb-prev aria-label="Предыдущие">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"
               stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M15 18 9 12l6-6"/>
          </svg>
        </button>
        <button class="dzb-arrow" type="button" data-dzb-next aria-label="Следующие">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"
               stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="m9 18 6-6-6-6"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</div>

<!-- ======================================================== аккордеон -->
<div class="dzb-section" aria-labelledby="dzb-faq-title">
  <div class="dzb-container">
    <div class="dzb-section-head dzb-section-head--center">
      <p class="dzb-eyebrow">Коротко о технологии</p>
      <h2 id="dzb-faq-title">Частые вопросы</h2>
    </div>
    <div class="dzb-acc" id="dzb-acc">
      <div class="dzb-acc__item">
        <h3><button class="dzb-acc__btn" type="button" aria-expanded="false"
                    aria-controls="dzb-p1" id="dzb-b1">Что такое сетевая встреча?</button></h3>
        <div class="dzb-acc__panel" id="dzb-p1" role="region" aria-labelledby="dzb-b1" hidden>
          <p>Встреча человека или семьи вместе с их «сетью» — родственниками, друзьями,
          соседями, учителями, врачами, соцработниками. Ведёт её сетевой терапевт: он
          не решает за участников, а помогает им договориться и распределить, кто что
          может сделать.</p>
        </div>
      </div>
      <div class="dzb-acc__item">
        <h3><button class="dzb-acc__btn" type="button" aria-expanded="false"
                    aria-controls="dzb-p2" id="dzb-b2">Кому мы помогаем?</button></h3>
        <div class="dzb-acc__panel" id="dzb-p2" role="region" aria-labelledby="dzb-b2" hidden>
          <p>Семьям в кризисе и специалистам, которые с ними работают. Запрос чаще приходит
          от коллег — школ, опеки, больниц, фондов, — когда обычные меры уже не помогают.</p>
        </div>
      </div>
      <div class="dzb-acc__item">
        <h3><button class="dzb-acc__btn" type="button" aria-expanded="false"
                    aria-controls="dzb-p3" id="dzb-b3">Как попасть на обучение?</button></h3>
        <div class="dzb-acc__panel" id="dzb-p3" role="region" aria-labelledby="dzb-b3" hidden>
          <p>Мы проводим программы повышения квалификации для помогающих специалистов,
          супервизии и интервизии. Расписание и условия — в разделе «Обучение»;
          по вопросам записи пишите на
          <a href="mailto:dirigible.community@mail.ru">dirigible.community@mail.ru</a>.</p>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ======================================================== панель проверки -->
<div class="dzb-section dzb-section--tight">
  <div class="dzb-container">
    <div class="dzb-check" id="dzb-check">
      <h3>Проверка блока</h3>
      <p style="color:var(--dzb-ink-soft);font-size:.9375rem;margin-bottom:.85rem">
        Этот список заполняет скрипт самого блока. Если напротив пунктов стоят галочки —
        Craftum не вырезал ни стили, ни скрипт.
      </p>
      <ul>
        <li data-dzb-test="js"><b>…</b><span>JavaScript внутри блока выполняется</span></li>
        <li data-dzb-test="vars"><b>…</b><span>CSS-переменные <code>--dzb-*</code> дошли до блока</span></li>
        <li data-dzb-test="tex"><b>…</b><span>Текстура вязки встроена как <code>data:</code> URI</span></li>
        <li data-dzb-test="font"><b>…</b><span>Шрифт Comfortaa загрузился с Google Fonts</span></li>
        <li data-dzb-test="io"><b>…</b><span>IntersectionObserver доступен (анимации появления)</span></li>
        <li data-dzb-test="img"><b>…</b><span>Фотографии с CDN организации отдаются</span></li>
        <li data-dzb-test="scope"><b>…</b><span>Стили не вышли за пределы блока</span></li>
      </ul>
    </div>
  </div>
</div>

<!-- ======================================================== CTA -->
<div class="dzb-section dzb-section--purl dzb-scallop" id="dzb-cta" aria-labelledby="dzb-cta-title">
  <div class="dzb-container dzb-text-center">
    <h2 id="dzb-cta-title"><span class="dzb-stitch">Поддержите «сеть поддержки»</span></h2>
    <p class="dzb-lead dzb-center-x" style="max-width:56ch;margin-top:.9rem">Любое пожертвование
    помогает семьям удержаться на плаву и найти опору среди близких.</p>
    <p class="dzb-cluster dzb-cluster--center" style="margin-top:1.6rem">
      <a class="dzb-btn dzb-btn--orange dzb-btn--lg" href="https://dirigible.community/donate">
        <svg class="dzb-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8z"/>
        </svg>
        Сделать пожертвование
      </a>
      <a class="dzb-btn dzb-btn--ghost dzb-btn--lg" href="#dzb-facts">Реквизиты организации</a>
    </p>
  </div>
</div>

<!-- ======================================================== реквизиты -->
<div class="dzb-section" id="dzb-facts" aria-labelledby="dzb-facts-title">
  <div class="dzb-container">
    <div class="dzb-section-head dzb-section-head--center">
      <h2 id="dzb-facts-title">Реквизиты</h2>
    </div>
    <dl class="dzb-facts">
      <dt>Полное название</dt>
      <dd>Автономная некоммерческая организация Центр развития социальных практик «Дирижабль»</dd>
      <dt>ИНН / КПП</dt>
      <dd>7716981773 / 771601001</dd>
      <dt>ОГРН</dt>
      <dd>1237700318877</dd>
      <dt>Адрес</dt>
      <dd>129128, г. Москва, проспект Мира, д. 202А, кв. 40</dd>
      <dt>Телефон</dt>
      <dd><a href="tel:+79169259174">+7 (916) 925-91-74</a></dd>
      <dt>Почта</dt>
      <dd><a href="mailto:dirigible.community@mail.ru">dirigible.community@mail.ru</a></dd>
      <dt>Директор</dt>
      <dd>Татьяна Арчакова</dd>
    </dl>
  </div>
</div>

<script>
/* Вся логика блока. Обёрнута в IIFE: Craftum может вставить блок
   несколько раз, глобальных имён не оставляем.
   Все выборки — внутри #dzb, чужую разметку не трогаем. */
(function () {
  "use strict";

  var root = document.getElementById("dzb");
  if (!root || root.getAttribute("data-dzb-ready") === "1") { return; }
  root.setAttribute("data-dzb-ready", "1");

  /* ------------------------------------------------ появление при скролле */
  var reveal = root.querySelectorAll(".dzb-reveal");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add("dzb-in");
          io.unobserve(e.target);
        }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    Array.prototype.forEach.call(reveal, function (el) { io.observe(el); });
  } else {
    /* нет observer — показываем сразу, иначе контент останется невидимым */
    root.classList.add("dzb-no-js");
  }

  /* ------------------------------------------------------ карусель команды */
  var track = root.querySelector("#dzb-track");
  var prev = root.querySelector("[data-dzb-prev]");
  var next = root.querySelector("[data-dzb-next]");

  if (track && prev && next) {
    /* шаг — ширина первой карточки с зазором. offsetLeft тут не годится:
       он считается от offsetParent, а не от самой дорожки. */
    function step() {
      var first = track.firstElementChild;
      if (!first) { return track.clientWidth; }
      var styles = window.getComputedStyle(track);
      var gap = parseFloat(styles.columnGap || styles.gap || "0") || 0;
      return first.getBoundingClientRect().width + gap;
    }
    function sync() {
      var max = track.scrollWidth - track.clientWidth - 2;
      prev.disabled = track.scrollLeft <= 2;
      next.disabled = track.scrollLeft >= max;
    }
    prev.addEventListener("click", function () { track.scrollBy({ left: -step(), behavior: "smooth" }); });
    next.addEventListener("click", function () { track.scrollBy({ left: step(), behavior: "smooth" }); });
    track.addEventListener("scroll", sync, { passive: true });
    window.addEventListener("resize", sync);
    sync();
  }

  /* --------------------------------------------------------------- аккордеон */
  var accBtns = root.querySelectorAll(".dzb-acc__btn");
  Array.prototype.forEach.call(accBtns, function (btn) {
    btn.addEventListener("click", function () {
      var panel = root.querySelector("#" + btn.getAttribute("aria-controls"));
      var open = btn.getAttribute("aria-expanded") === "true";
      /* один открытый за раз */
      Array.prototype.forEach.call(accBtns, function (other) {
        other.setAttribute("aria-expanded", "false");
        var p = root.querySelector("#" + other.getAttribute("aria-controls"));
        if (p) { p.hidden = true; }
      });
      if (!open) {
        btn.setAttribute("aria-expanded", "true");
        if (panel) { panel.hidden = false; }
      }
    });
  });

  /* ---------------------------------------------------------- панель проверки */
  function mark(name, ok, note) {
    var li = root.querySelector('[data-dzb-test="' + name + '"]');
    if (!li) { return; }
    li.setAttribute("data-ok", ok ? "1" : "0");
    li.querySelector("b").textContent = ok ? "✓" : "✗";
    if (note) {
      var span = li.querySelector("span");
      span.textContent = span.textContent + " — " + note;
    }
  }

  var cs = window.getComputedStyle(root);

  mark("js", true);
  mark("vars", (cs.getPropertyValue("--dzb-orange") || "").trim() === "#EE7B18");
  mark("tex", cs.backgroundImage.indexOf("data:image/svg+xml") !== -1);
  mark("io", "IntersectionObserver" in window);

  /* стили не должны протекать наружу: у <body> не должно быть нашего фона */
  var bodyBg = window.getComputedStyle(document.body).backgroundImage || "";
  mark("scope", bodyBg.indexOf("data:image/svg+xml") === -1);

  /* шрифт — ждём загрузки, иначе проверка сработает раньше времени */
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(function () {
      mark("font", document.fonts.check('700 1rem "Comfortaa"'));
    });
  } else {
    mark("font", false, "браузер не поддерживает Font Loading API");
  }

  /* Картинки с CDN. Ждать load от всех нельзя: портреты команды стоят
     loading="lazy" и за экраном не грузятся вовсе — счётчик никогда бы
     не закрылся. Поэтому считаем состояние после загрузки страницы:
     отложенные — не ошибка, ошибкой считается complete без naturalWidth. */
  var imgs = root.querySelectorAll("img");
  var total = imgs.length;

  function reportImgs() {
    var bad = 0, loaded = 0, pending = 0;
    Array.prototype.forEach.call(imgs, function (im) {
      if (!im.complete) { pending += 1; }
      else if (!im.naturalWidth) { bad += 1; }
      else { loaded += 1; }
    });
    var note = bad
      ? "не отдались: " + bad + " из " + total
      : loaded + " из " + total + (pending ? ", остальные отложены (lazy)" : "");
    mark("img", bad === 0, note);
  }

  if (total === 0) {
    mark("img", false, "картинок в блоке нет");
  } else {
    Array.prototype.forEach.call(imgs, function (im) {
      im.addEventListener("error", reportImgs);
    });
    if (document.readyState === "complete") {
      setTimeout(reportImgs, 400);
    } else {
      window.addEventListener("load", function () { setTimeout(reportImgs, 400); });
    }
  }
})();
</script>
</section>
