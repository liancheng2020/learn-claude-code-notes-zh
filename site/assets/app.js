/* 主题、复制、注释高亮、目录抽屉 */
(function () {
  'use strict';

  /* ---------- 主题：跟随系统 → 浅色 → 深色 ---------- */
  var root = document.documentElement;
  var themeBtn = document.getElementById('themeBtn');
  function themeName(t) { return t === 'dark' ? '深色' : t === 'light' ? '浅色' : '跟随系统'; }
  function applyTheme(t, init) {
    if (t === 'light' || t === 'dark') root.dataset.theme = t;
    else if (!init) delete root.dataset.theme;
    if (themeBtn) {
      themeBtn.title = '主题：' + themeName(t) + '（点击切换）';
      themeBtn.setAttribute('aria-label', '当前主题：' + themeName(t) + '，点击切换');
    }
  }
  var stored = null;
  try { stored = localStorage.getItem('lcc-theme'); } catch (e) { /* 隐私模式 */ }
  applyTheme(stored, true);
  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      var cur = root.dataset.theme;
      var next = cur === 'dark' ? null : cur === 'light' ? 'dark' : 'light';
      try {
        if (next) localStorage.setItem('lcc-theme', next);
        else localStorage.removeItem('lcc-theme');
      } catch (e) { /* ignore */ }
      applyTheme(next);
    });
  }

  /* ---------- 复制代码（只复制源码） ---------- */
  [].slice.call(document.querySelectorAll('.copy')).forEach(function (btn) {
    btn.addEventListener('click', function () {
      var code = document.getElementById(btn.dataset.copy);
      if (!code) return;
      var text = [].slice.call(code.querySelectorAll('.row .tx')).map(function (tx) {
        return tx.textContent.replace(/\u00a0/g, '');
      }).join('\n');
      var done = function () {
        var old = btn.textContent;
        btn.textContent = '已复制';
        setTimeout(function () { btn.textContent = old; }, 1500);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { fallback(text, done); });
      } else {
        fallback(text, done);
      }
    });
  });
  function fallback(text, done) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.top = '-1000px';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); done(); } catch (e) { /* ignore */ }
    document.body.removeChild(ta);
  }

  /* ---------- 注释 ↔ 代码行 ---------- */
  function rowsOf(ann) {
    var wrap = ann.closest('.code-wrap');
    if (!wrap) return [];
    var from = +ann.dataset.from, to = +ann.dataset.to;
    return [].slice.call(wrap.querySelectorAll('.row')).filter(function (r) {
      var n = +r.dataset.line;
      return n >= from && n <= to;
    });
  }
  function paint(ann, on) {
    rowsOf(ann).forEach(function (r) { r.classList.toggle('hl', on); });
  }
  [].slice.call(document.querySelectorAll('.ann')).forEach(function (ann) {
    ann.addEventListener('mouseenter', function () { paint(ann, true); });
    ann.addEventListener('mouseleave', function () {
      if (ann.getAttribute('aria-pressed') !== 'true') paint(ann, false);
    });
    function toggle() {
      var on = ann.getAttribute('aria-pressed') !== 'true';
      ann.setAttribute('aria-pressed', on ? 'true' : 'false');
      paint(ann, on);
      if (on) {
        var first = rowsOf(ann)[0];
        if (first) first.scrollIntoView({ block: 'nearest', inline: 'nearest' });
      }
    }
    ann.addEventListener('click', toggle);
    ann.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); }
    });
  });

  /* ---------- 目录：滚动高亮 ---------- */
  var links = [].slice.call(document.querySelectorAll('.side nav a, .toc-sheet nav a'));
  function markHash(id) {
    links.forEach(function (l) {
      var on = l.getAttribute('href') === '#' + id;
      l.classList.toggle('active', on);
      if (on) l.setAttribute('aria-current', 'true');
      else l.removeAttribute('aria-current');
    });
  }
  var hashLinks = links.filter(function (l) {
    var h = l.getAttribute('href');
    return h && h.charAt(0) === '#' && document.querySelector(h);
  });
  if (hashLinks.length) {
    var updateActive = function () {
      var y = window.scrollY + 140;
      var current = 'top';
      hashLinks.forEach(function (l) {
        var el = document.querySelector(l.getAttribute('href'));
        if (!el) return;
        if (el.getBoundingClientRect().top + window.scrollY <= y) current = l.getAttribute('href').slice(1);
      });
      markHash(current);
    };
    var lastTick = 0;
    window.addEventListener('scroll', function () {
      var now = Date.now();
      if (now - lastTick < 80) return;
      lastTick = now;
      updateActive();
    }, { passive: true });
    window.addEventListener('resize', updateActive);
    window.addEventListener('hashchange', function () {
      if (location.hash) markHash(location.hash.slice(1));
    });
    hashLinks.forEach(function (l) {
      l.addEventListener('click', function () { markHash(l.getAttribute('href').slice(1)); });
    });
    updateActive();
  }

  /* ---------- 目录抽屉：焦点陷阱 / 关闭 / 恢复 ---------- */
  var btn = document.getElementById('tocBtn');
  var panel = document.getElementById('tocPanel');
  var closeBtn = document.getElementById('tocClose');
  var shell = document.querySelector('.shell');
  var lastFocus = null;

  function focusables() {
    if (!panel) return [];
    return [].slice.call(panel.querySelectorAll('a[href], button:not([disabled])'))
      .filter(function (el) { return el.offsetParent !== null; });
  }
  function setPanel(open) {
    if (!panel || !btn) return;
    if (open) {
      lastFocus = (document.activeElement && document.activeElement !== document.body)
        ? document.activeElement : btn;
      panel.hidden = false;
      panel.classList.add('open');
      document.body.classList.add('toc-open');
      if (shell) shell.inert = true;
      btn.setAttribute('aria-expanded', 'true');
      var first = focusables()[0];
      if (first) first.focus();
    } else {
      panel.classList.remove('open');
      panel.hidden = true;
      document.body.classList.remove('toc-open');
      if (shell) shell.inert = false;
      btn.setAttribute('aria-expanded', 'false');
      var back = (lastFocus && lastFocus !== document.body && lastFocus.focus) ? lastFocus : btn;
      back.focus();
    }
  }
  if (btn && panel) {
    btn.addEventListener('click', function () { setPanel(panel.hidden); });
    if (closeBtn) closeBtn.addEventListener('click', function () { setPanel(false); });
    panel.addEventListener('click', function (e) {
      if (e.target === panel) setPanel(false);
      if (e.target.closest('a')) setPanel(false);
    });
    panel.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { e.preventDefault(); setPanel(false); return; }
      if (e.key !== 'Tab') return;
      var list = focusables();
      if (!list.length) return;
      var first = list[0], last = list[list.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !panel.hidden) setPanel(false);
    });
  }
})();
