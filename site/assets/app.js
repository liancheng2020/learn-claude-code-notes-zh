/* 注释高亮 + 移动端目录抽屉 */
(function () {
  var links = [].slice.call(document.querySelectorAll('.side nav a, .toc-sheet nav a'));

  function rowsBetween(wrap, from, to) {
    return [].slice.call(wrap.querySelectorAll('.row')).filter(function (r) {
      var n = +r.dataset.line;
      return n >= from && n <= to;
    });
  }
  function paint(ann, on) {
    var wrap = ann.closest('.code-wrap');
    if (!wrap) return;
    rowsBetween(wrap, +ann.dataset.from, +ann.dataset.to).forEach(function (r) {
      r.classList.toggle('hl', on);
    });
  }
  [].slice.call(document.querySelectorAll('.ann')).forEach(function (ann) {
    ann.addEventListener('mouseenter', function () { paint(ann, true); });
    ann.addEventListener('mouseleave', function () {
      if (ann.getAttribute('aria-pressed') !== 'true') paint(ann, false);
    });
    function toggle() {
      var on = ann.getAttribute('aria-pressed') !== 'true';
      ann.setAttribute('aria-pressed', on ? 'true' : 'false');
      ann.classList.toggle('pinned', on);
      paint(ann, on);
    }
    ann.addEventListener('click', toggle);
    ann.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); }
    });
  });


  /* 单页完整教程：滚动高亮左侧目录 */
  var hashLinks = links.filter(function (l) {
    var h = l.getAttribute('href');
    return h && h.charAt(0) === '#' && document.querySelector(h);
  });
  function markHash(id) {
    hashLinks.forEach(function (l) {
      var on = l.getAttribute('href') === '#' + id;
      l.classList.toggle('active', on);
      if (on) l.setAttribute('aria-current', 'true');
      else l.removeAttribute('aria-current');
    });
  }
  if (hashLinks.length) {
    var ticking = false;
    function updateActive() {
      ticking = false;
      var y = window.scrollY + 140;
      var current = 'top';
      hashLinks.forEach(function (l) {
        var el = document.querySelector(l.getAttribute('href'));
        if (!el) return;
        var top = el.getBoundingClientRect().top + window.scrollY;
        if (top <= y) current = l.getAttribute('href').slice(1);
      });
      markHash(current);
    }
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
      l.addEventListener('click', function () {
        markHash(l.getAttribute('href').slice(1));
      });
    });
    updateActive();
  }
  var btn = document.getElementById('tocBtn');
  var panel = document.getElementById('tocPanel');
  var closeBtn = document.getElementById('tocClose');
  function setPanel(open) {
    if (!panel || !btn) return;
    panel.hidden = !open;
    panel.classList.toggle('open', open);
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) { var f = panel.querySelector('a'); if (f) f.focus(); }
    else { btn.focus(); }
  }
  if (btn && panel) {
    btn.addEventListener('click', function () { setPanel(panel.hidden); });
    if (closeBtn) closeBtn.addEventListener('click', function () { setPanel(false); });
    panel.addEventListener('click', function (e) {
      if (e.target === panel) setPanel(false);
      if (e.target.closest('a')) setPanel(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !panel.hidden) setPanel(false);
    });
  }
})();
