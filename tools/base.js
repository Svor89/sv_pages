/* Общий скрипт всех страниц (правка здесь → python tools/build.py): копирование, вкладки, «Усі команди»,
   оглавление, поиск по вопросам, тема, значок вкладки браузера. */
(function () {
  var d = document, toastTimer;
  function all(sel, root) { return [].slice.call((root || d).querySelectorAll(sel)); }

  all('pre[data-collect]').forEach(function (p) {
    var lines = all('pre', d.getElementById(p.getAttribute('data-collect'))).map(function (x) { return x.textContent.trim(); });
    if (p.getAttribute('data-after')) lines.push(p.getAttribute('data-after'));
    p.textContent = lines.join('\n');
  });
  var logo = d.querySelector('.logo');
  if (logo) d.getElementById('favicon').href = logo.src;

  // оглавление: nav[data-toc] — из заголовков разделов (номер .num + h2); раздел без id получает s1, s2…
  all('[data-toc]').forEach(function (nav) {
    var ol = d.createElement('ol');
    all('main .sec').forEach(function (s, i) {
      var h = s.querySelector('h2'), n = s.querySelector('.num');
      if (!h) return;
      if (!s.id) s.id = 's' + (i + 1);
      var li = d.createElement('li'), a = d.createElement('a'), a1 = d.createElement('span'), a2 = d.createElement('span');
      a.href = '#' + s.id; a1.textContent = n ? n.textContent : i + 1; a2.textContent = h.textContent;
      a.appendChild(a1); a.appendChild(a2); li.appendChild(a); ol.appendChild(li);
    });
    nav.appendChild(ol);
  });

  // поиск: input[data-search] фильтрует вопросы details.q (раскрывает найденные), прячет пустые разделы, .empty — «нічого»
  function norm(s) { return s.toLowerCase().replace(/[’ʼ`]/g, "'"); }
  all('input[data-search]').forEach(function (inp) {
    var items = all('details.q'), empty = d.querySelector('.empty');
    function run() {
      var q = norm(inp.value.trim()), n = 0;
      items.forEach(function (it) {
        var hit = !q || norm(it.textContent).indexOf(q) >= 0;
        it.hidden = !hit; if (hit) n++;
        if (q) it.open = hit;
      });
      all('main .sec').forEach(function (s) {
        var qs = all('details.q', s);
        if (qs.length) s.hidden = qs.every(function (x) { return x.hidden; });
      });
      if (empty) empty.hidden = n > 0;
    }
    var m = /[?&]q=([^&]*)/.exec(location.search);
    if (m) inp.value = decodeURIComponent(m[1].replace(/\+/g, ' '));
    inp.addEventListener('input', run);
    run();
  });

  // #id в адресе открывает этот вопрос / блок
  function openHash() {
    var t = location.hash && d.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (t && t.tagName === 'DETAILS') { t.open = true; t.scrollIntoView(); }
  }
  openHash();
  window.addEventListener('hashchange', openHash);

  function toast(msg) {
    var t = d.getElementById('toast');
    t.lastChild.textContent = msg;
    t.className = 'show';
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.className = ''; }, 2500);
  }
  function fallback(text) {
    var ta = d.createElement('textarea');
    ta.value = text; ta.style.cssText = 'position:fixed;opacity:0';
    d.body.appendChild(ta); ta.select();
    var ok = false; try { ok = d.execCommand('copy'); } catch (e) {}
    d.body.removeChild(ta);
    return ok;
  }
  function copy(text, done) {
    if (navigator.clipboard && window.isSecureContext)
      navigator.clipboard.writeText(text).then(done, function () { if (fallback(text)) done(); });
    else if (fallback(text)) done();
  }

  d.addEventListener('click', function (e) {
    var b = e.target.closest('[data-copy]');
    if (b) {
      e.preventDefault(); e.stopPropagation();   // кнопка в <summary> не сворачивает блок
      var every = b.getAttribute('data-copy') === 'all';
      var pre = (every ? b.closest('details') : b.closest('.line')).querySelector('pre');
      copy(pre.textContent.trim() + (every ? '\n' : ''), function () {
        var use = b.querySelector('use'), span = b.querySelector('span'), text = span && span.textContent;
        use.setAttribute('href', '#i-check'); b.classList.add('ok');
        if (span) span.textContent = 'Скопійовано!';
        toast(every ? 'Усі команди скопійовано' : 'Команду скопійовано');
        setTimeout(function () {
          use.setAttribute('href', '#i-copy'); b.classList.remove('ok');
          if (span) span.textContent = text;
        }, 2000);
      });
      return;
    }
    if (e.target.closest('.theme')) {
      var light = d.documentElement.classList.toggle('light');
      try { localStorage.setItem('theme', light ? 'light' : 'dark'); } catch (er) {}
      return;
    }
    var v = e.target.closest('[data-v]');
    if (v) { copy(v.getAttribute('data-v'), function () { toast('Скопійовано: ' + v.getAttribute('data-v')); }); return; }
    var t = e.target.closest('[data-tab]');
    if (t) {
      [].forEach.call(t.parentNode.children, function (x) {
        x.classList.toggle('on', x === t);
        x.setAttribute('aria-selected', x === t);
        d.getElementById(x.getAttribute('data-tab')).hidden = x !== t;
      });
    }
  });
})();
