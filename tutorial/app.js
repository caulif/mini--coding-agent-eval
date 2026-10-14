(() => {
  'use strict';
  const english = document.documentElement.lang === 'en';
  const labels = english
    ? {copied: 'Copied', copy: 'Copy', manual: 'Please copy manually', last: 'Last read: ', overview: 'Overview'}
    : {copied: '已复制', copy: '复制', manual: '请手动复制', last: '上次读到：', overview: '阅读路线'};
  const languageLink = document.querySelector('.language-switch');
  // Keep the current section when switching between the two static pages.
  languageLink.addEventListener('click', () => {
    languageLink.hash = current ? '#' + current.id : location.hash;
  });
  document.querySelectorAll('.copy').forEach(button => button.addEventListener('click', async () => {
    const code = button.closest('.code').querySelector('code').textContent;
    try {
      if (navigator.clipboard && window.isSecureContext) await navigator.clipboard.writeText(code);
      else {
        const area = document.createElement('textarea'); area.value = code;
        area.style.cssText = 'position:fixed;left:-9999px'; document.body.append(area); area.select();
        const ok = document.execCommand('copy'); area.remove(); if (!ok) throw new Error('copy');
      }
      button.textContent = labels.copied; setTimeout(() => { button.textContent = labels.copy; }, 1500);
    } catch { button.textContent = labels.manual; }
  }));
  const chapters = [...document.querySelectorAll('.chapter')];
  const headings = [...document.querySelectorAll('.chapter h2, .chapter h3')];
  const links = [...document.querySelectorAll('nav a')];
  const contents = document.querySelector('.contents');
  const compact = matchMedia('(max-width: 800px)');
  contents.open = !compact.matches;
  const storageKey = 'mini-eval-reading-v2-' + document.documentElement.lang;
  const banner = document.querySelector('#resume-reading');
  let saved = null, current = null, timer, scheduled = false;
  try { saved = JSON.parse(localStorage.getItem(storageKey)); } catch { /* Reading works without storage. */ }
  if (!location.hash && saved && typeof saved.id === 'string') {
    const target = headings.find(h => h.id === saved.id);
    if (target) {
      document.querySelector('#resume-label').textContent = labels.last + target.textContent;
      document.querySelector('#resume-link').setAttribute('href', '#' + target.id);
      banner.hidden = false;
    }
  }
  document.querySelector('#dismiss-resume').addEventListener('click', () => { banner.hidden = true; });
  document.querySelector('#resume-link').addEventListener('click', () => { banner.hidden = true; });
  function save() {
    if (!current) return;
    try { localStorage.setItem(storageKey, JSON.stringify({id: current.id})); } catch { /* Optional persistence. */ }
  }
  function update() {
    scheduled = false;
    const height = document.documentElement.scrollHeight - innerHeight;
    document.querySelector('#progress').style.width = (height > 0 ? Math.max(0, Math.min(100, 100 * scrollY / height)) : 0) + '%';
    let chapter = null, heading = null;
    chapters.forEach(c => { if (c.getBoundingClientRect().top < 160) chapter = c; });
    if (chapter) chapter.querySelectorAll('h2, h3').forEach(h => { if (!heading || h.getBoundingClientRect().top < 160) heading = h; });
    document.querySelector('#reading-location').textContent = chapter ? chapter.dataset.stage + ' · ' + heading.textContent : labels.overview;
    document.querySelectorAll('.nav-group').forEach(group => {
      group.classList.toggle('active', !!chapter && group.querySelector('.chapter-link').hash === '#' + chapter.id);
    });
    links.forEach(link => {
      const active = !!chapter && (link.hash === '#' + chapter.id || link.hash === '#' + heading.id);
      link.classList.toggle('active', active);
      if (active) link.setAttribute('aria-current', 'location'); else link.removeAttribute('aria-current');
    });
    if (heading && current !== heading) { current = heading; clearTimeout(timer); timer = setTimeout(save, 800); }
  }
  function schedule() { if (!scheduled) { scheduled = true; requestAnimationFrame(update); } }
  links.forEach(link => link.addEventListener('click', () => { if (compact.matches) contents.open = false; }));
  // Native anchors keep links usable without JS; move keyboard focus after navigation.
  addEventListener('hashchange', () => {
    const target = document.getElementById(location.hash.slice(1));
    const heading = target && (target.matches('h2, h3') ? target : target.querySelector('h2'));
    if (heading) heading.focus({preventScroll: true});
    schedule();
  });
  addEventListener('scroll', schedule, {passive: true});
  addEventListener('resize', schedule);
  addEventListener('pagehide', save);
  update();
})();
