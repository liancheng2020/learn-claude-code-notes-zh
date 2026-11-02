/* 注释高亮 + 移动端目录抽屉 */
(function () {
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
