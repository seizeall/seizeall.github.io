/* ==========================================================================
   Rongtao Chen — personal academic homepage
   Vanilla JS, progressive enhancement. The page works with this file disabled.
   ========================================================================== */
(function () {
  'use strict';

  var doc = document;
  var root = doc.documentElement;
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------------- Theme ---------------- */
  var themeToggle = doc.getElementById('themeToggle');

  function applyTheme(theme) {
    root.dataset.theme = theme;
    if (themeToggle) {
      var toDark = theme === 'light';
      themeToggle.setAttribute('aria-label', toDark ? 'Switch to dark theme' : 'Switch to light theme');
      themeToggle.setAttribute('title', toDark ? 'Switch to dark theme' : 'Switch to light theme');
    }
    var meta = doc.querySelector('meta[name="theme-color"]:not([media])');
    if (!meta) {
      meta = doc.createElement('meta');
      meta.name = 'theme-color';
      doc.head.appendChild(meta);
    }
    meta.content = theme === 'dark' ? '#080b12' : '#f5f6fa';
  }

  applyTheme(root.dataset.theme === 'dark' ? 'dark' : 'light');

  if (themeToggle) {
    themeToggle.addEventListener('click', function () {
      var next = root.dataset.theme === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      try { localStorage.setItem('theme', next); } catch (e) { /* ignore */ }
    });
  }

  // Follow the OS only while the visitor has not chosen explicitly.
  var mq = window.matchMedia('(prefers-color-scheme: dark)');
  var onSchemeChange = function (e) {
    var saved = null;
    try { saved = localStorage.getItem('theme'); } catch (err) { /* ignore */ }
    if (!saved) applyTheme(e.matches ? 'dark' : 'light');
  };
  if (mq.addEventListener) mq.addEventListener('change', onSchemeChange);
  else if (mq.addListener) mq.addListener(onSchemeChange);

  /* ---------------- Header state ---------------- */
  var header = doc.getElementById('siteHeader');
  var navLinks = Array.prototype.slice.call(doc.querySelectorAll('.nav a[href^="#"]'));
  var sections = navLinks
    .map(function (a) { return doc.querySelector(a.getAttribute('href')); })
    .filter(Boolean);

  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () {
      ticking = false;
      var y = window.scrollY || window.pageYOffset;

      if (header) header.classList.toggle('is-stuck', y > 8);

      // Scroll spy: the last section whose top has passed the header.
      var marker = y + (header ? header.offsetHeight : 70) + 90;
      var current = null;
      for (var i = 0; i < sections.length; i++) {
        if (sections[i].offsetTop <= marker) current = sections[i];
      }
      navLinks.forEach(function (a) {
        var active = current && a.getAttribute('href') === '#' + current.id;
        a.classList.toggle('is-active', !!active);
        if (active) a.setAttribute('aria-current', 'true');
        else a.removeAttribute('aria-current');
      });
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  onScroll();

  /* ---------------- Mobile menu ---------------- */
  var menuBtn = doc.getElementById('menuBtn');
  var nav = doc.getElementById('primaryNav');

  function closeMenu() {
    if (!menuBtn) return;
    doc.body.classList.remove('nav-open');
    menuBtn.setAttribute('aria-expanded', 'false');
    menuBtn.setAttribute('aria-label', 'Open menu');
  }

  if (menuBtn && nav) {
    menuBtn.addEventListener('click', function () {
      var open = doc.body.classList.toggle('nav-open');
      menuBtn.setAttribute('aria-expanded', String(open));
      menuBtn.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    });
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) closeMenu();
    });
    doc.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeMenu();
    });
    doc.addEventListener('click', function (e) {
      if (!doc.body.classList.contains('nav-open')) return;
      if (nav.contains(e.target) || menuBtn.contains(e.target)) return;
      closeMenu();
    });
    window.addEventListener('resize', function () {
      if (window.innerWidth > 760) closeMenu();
    });
  }

  /* ---------------- Publication filter ---------------- */
  var filter = doc.getElementById('pubFilter');
  var pubList = doc.getElementById('pubList');
  var pubEmpty = doc.getElementById('pubEmpty');

  if (filter && pubList) {
    var pubs = Array.prototype.slice.call(pubList.querySelectorAll('.pub'));
    filter.addEventListener('click', function (e) {
      var btn = e.target.closest('.chip');
      if (!btn) return;
      var kind = btn.dataset.filter;
      var shown = 0;

      filter.querySelectorAll('.chip').forEach(function (c) {
        var on = c === btn;
        c.classList.toggle('is-active', on);
        c.setAttribute('aria-pressed', String(on));
      });

      pubs.forEach(function (p) {
        var match = kind === 'all' || p.dataset.type === kind;
        p.classList.toggle('is-hidden', !match);
        if (match) shown++;
      });

      if (pubEmpty) pubEmpty.hidden = shown > 0;
    });
  }

  /* ---------------- Copy email ---------------- */
  var copyBtn = doc.getElementById('copyEmail');
  var toast = doc.getElementById('toast');
  var toastTimer = null;

  function showToast(msg) {
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add('is-visible');
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(function () {
      toast.classList.remove('is-visible');
    }, 2200);
  }

  function legacyCopy(text) {
    var ta = doc.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.top = '-1000px';
    doc.body.appendChild(ta);
    ta.select();
    var ok = false;
    try { ok = doc.execCommand('copy'); } catch (e) { ok = false; }
    doc.body.removeChild(ta);
    return ok;
  }

  if (copyBtn) {
    copyBtn.addEventListener('click', function () {
      var email = copyBtn.dataset.email;
      var label = copyBtn.querySelector('.copy-label');
      var done = function (ok) {
        if (ok) {
          showToast('Email copied — ' + email);
          if (label) {
            var original = label.textContent;
            label.textContent = 'Copied';
            window.setTimeout(function () { label.textContent = original; }, 1800);
          }
        } else {
          showToast('Copy failed — the address is ' + email);
        }
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(email).then(function () { done(true); }, function () { done(legacyCopy(email)); });
      } else {
        done(legacyCopy(email));
      }
    });
  }

  /* ---------------- Reveal on scroll ---------------- */
  var revealables = Array.prototype.slice.call(doc.querySelectorAll('[data-reveal]'));

  if (revealables.length) {
    if (reduceMotion || !('IntersectionObserver' in window)) {
      revealables.forEach(function (el) { el.classList.add('is-visible'); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var el = entry.target;
          var siblings = el.parentElement ? Array.prototype.slice.call(el.parentElement.children) : [];
          var idx = Math.max(0, siblings.indexOf(el));
          el.style.setProperty('--d', Math.min(idx * 70, 350) + 'ms');
          el.classList.add('is-visible');
          io.unobserve(el);
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
      revealables.forEach(function (el) { io.observe(el); });
    }
  }

  /* ---------------- Count-up stats ---------------- */
  var counters = Array.prototype.slice.call(doc.querySelectorAll('.count[data-count]'));

  function runCounter(el) {
    var target = parseInt(el.dataset.count, 10) || 0;
    if (reduceMotion) { el.textContent = String(target); return; }
    var start = performance.now();
    var dur = 1100;
    function frame(now) {
      var t = Math.min(1, Math.max(0, (now - start) / dur));
      var eased = 1 - Math.pow(1 - t, 3);
      el.textContent = String(Math.round(target * eased));
      if (t < 1) window.requestAnimationFrame(frame);
    }
    window.requestAnimationFrame(frame);
  }

  if (counters.length && 'IntersectionObserver' in window) {
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        runCounter(entry.target);
        cio.unobserve(entry.target);
      });
    }, { threshold: 0.5 });
    counters.forEach(function (c) { cio.observe(c); });
  }

  /* ---------------- Footer year ---------------- */
  var yearEl = doc.getElementById('year');
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());
})();
